import { error, redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import {
  getShortlinkBySlug,
  incrementShortlinkClicks,
  query,
  getSettings
} from '$lib/server/database';
import { sanitizeAds } from '$lib/server/sanitize';

export const load: PageServerLoad = async ({ params, setHeaders }) => {
  const { slug } = params;

  if (!slug) {
    throw error(404, 'Link não especificado');
  }

  const link = await getShortlinkBySlug(slug);

  if (!link) {
    throw error(404, 'Link não encontrado');
  }

  // Whitelabel privacy: private shortlinks stay out of search indexes
  if (link.is_indexed === 0) {
    setHeaders({
      'X-Robots-Tag': 'noindex, nofollow'
    });
  }

  // Fire-and-forget click counter
  incrementShortlinkClicks(slug).catch((err) => {
    console.error('Error incrementing shortlink clicks:', err);
  });

  // Instant redirect (no interstitial)
  if (link.use_ad_interstitial === 0) {
    throw redirect(302, link.destination_url);
  }

  // Interstitial: fixed ad first, then random active ad
  let selectedAd: any = null;

  if (link.fixed_ad_id) {
    const fixedAds = await query('SELECT * FROM ads WHERE id = ? AND is_active = 1', [
      link.fixed_ad_id
    ]);
    if (fixedAds && fixedAds.length > 0) {
      selectedAd = fixedAds[0];
    } else {
      console.log(
        `Fixed ad ${link.fixed_ad_id} not available for /l/${slug}, falling back to random.`
      );
      const activeAds = await query('SELECT * FROM ads WHERE is_active = 1');
      if (activeAds && activeAds.length > 0) {
        selectedAd = activeAds[Math.floor(Math.random() * activeAds.length)];
      }
    }
  } else {
    const activeAds = await query('SELECT * FROM ads WHERE is_active = 1');
    if (activeAds && activeAds.length > 0) {
      selectedAd = activeAds[Math.floor(Math.random() * activeAds.length)];
    }
  }

  // No ads configured → never strand the visitor on an empty page
  if (!selectedAd) {
    console.log(`Fallback redirect for shortlink /l/${slug}: no ads available.`);
    throw redirect(302, link.destination_url);
  }

  const settings = await getSettings();
  const siteTitle = settings.site_title || 'Blog';
  const siteLogo = settings.site_logo || '/favicon.svg';
  const [safeAd] = sanitizeAds([selectedAd]);

  return {
    link: {
      slug: link.slug,
      destination_url: link.destination_url,
      ad_duration_seconds: link.ad_duration_seconds,
      is_indexed: link.is_indexed,
      meta_title: link.meta_title,
      meta_description: link.meta_description
    },
    ad: safeAd || selectedAd,
    siteTitle,
    siteLogo
  };
};
