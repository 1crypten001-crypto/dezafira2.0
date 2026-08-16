import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { validateSession } from '$lib/server/auth';
import { 
  getShortlinkBySlug, 
  createShortlink, 
  updateShortlink, 
  deleteShortlink,
  getPaginatedShortlinks,
  getShortlinksCount,
  getAllAds,
  getSettings
} from '$lib/server/database';

import { env } from '$env/dynamic/private';

export const load: PageServerLoad = async ({ cookies, url }) => {
  const token = cookies.get('admin_session');
  const username = await validateSession(token || '');
  if (!username) {
    throw redirect(302, '/admin/login');
  }

  const q = url.searchParams.get('q') || '';
  const page = parseInt(url.searchParams.get('page') || '1', 10);
  const limit = 10;
  const offset = (page - 1) * limit;

  const shortlinks = await getPaginatedShortlinks(q, limit, offset);
  const totalCount = await getShortlinksCount(q);
  const totalPages = Math.max(1, Math.ceil(totalCount / limit));

  const ads = await getAllAds();
  const activeAdsCount = ads.filter(a => a.is_active === 1).length;

  const settings = await getSettings();
  const rawSiteUrl = env.SITE_URL || settings.site_url || 'https://seusite.com';
  const siteUrl = rawSiteUrl.endsWith('/') ? rawSiteUrl.slice(0, -1) : rawSiteUrl;

  return {
    shortlinks,
    activeAdsCount,
    ads,
    siteUrl,
    q,
    currentPage: page,
    totalPages,
    totalCount
  };
};

export const actions: Actions = {
  create: async ({ request, cookies }) => {
    const token = cookies.get('admin_session');
    const username = await validateSession(token || '');
    if (!username) {
      return fail(401, { message: 'UNAUTHORIZED' });
    }

    const data = await request.formData();
    const slug = (data.get('slug') as string || '').trim().toLowerCase();
    const destinationUrl = (data.get('destination_url') as string || '').trim();
    const useAdInterstitial = data.get('use_ad_interstitial') === 'on' || data.get('use_ad_interstitial') === 'true';
    const adDurationSeconds = parseInt(data.get('ad_duration_seconds') as string || '5');
    const isIndexed = data.get('is_indexed') === 'on' || data.get('is_indexed') === 'true';
    const metaTitle = (data.get('meta_title') as string || '').trim();
    const metaDescription = (data.get('meta_description') as string || '').trim();
    const fixedAdIdRaw = data.get('fixed_ad_id') as string;
    const fixedAdId = fixedAdIdRaw && fixedAdIdRaw !== '' ? parseInt(fixedAdIdRaw, 10) : null;

    if (!slug || !destinationUrl) {
      return fail(400, { message: 'SL_REQUIRED' });
    }

    if (!/^[a-z0-9-_]+$/i.test(slug)) {
      return fail(400, { message: 'SL_INVALID_SLUG' });
    }

    const reservedSlugs = ['admin', 'api', 'members', 'login', 'logout', 'post', 'category', 'categories', 'premium', 'robots', 'sitemap', 'rss'];
    if (reservedSlugs.includes(slug)) {
      return fail(400, { message: 'SL_RESERVED' });
    }

    try {
      const existing = await getShortlinkBySlug(slug);
      if (existing) {
        return fail(400, { message: 'SL_SLUG_IN_USE', slug });
      }

      await createShortlink({
        slug,
        destinationUrl,
        useAdInterstitial,
        adDurationSeconds,
        isIndexed,
        metaTitle,
        metaDescription,
        fixedAdId
      });

      return { success: true, action: 'create' };
    } catch (e) {
      console.error('Error creating shortlink:', e);
      return fail(500, { message: 'SL_CREATE_FAIL' });
    }
  },

  update: async ({ request, cookies }) => {
    const token = cookies.get('admin_session');
    const username = await validateSession(token || '');
    if (!username) {
      return fail(401, { message: 'UNAUTHORIZED' });
    }

    const data = await request.formData();
    const id = data.get('id') as string;
    const slug = (data.get('slug') as string || '').trim().toLowerCase();
    const destinationUrl = (data.get('destination_url') as string || '').trim();
    const useAdInterstitial = data.get('use_ad_interstitial') === 'on' || data.get('use_ad_interstitial') === 'true';
    const adDurationSeconds = parseInt(data.get('ad_duration_seconds') as string || '5');
    const isIndexed = data.get('is_indexed') === 'on' || data.get('is_indexed') === 'true';
    const metaTitle = (data.get('meta_title') as string || '').trim();
    const metaDescription = (data.get('meta_description') as string || '').trim();
    const fixedAdIdRaw = data.get('fixed_ad_id') as string;
    const fixedAdId = fixedAdIdRaw && fixedAdIdRaw !== '' ? parseInt(fixedAdIdRaw, 10) : null;

    if (!id || !slug || !destinationUrl) {
      return fail(400, { message: 'SL_INCOMPLETE' });
    }

    if (!/^[a-z0-9-_]+$/i.test(slug)) {
      return fail(400, { message: 'SL_INVALID_SLUG' });
    }

    try {
      const existing = await getShortlinkBySlug(slug);
      if (existing && existing.id.toString() !== id) {
        return fail(400, { message: 'SL_SLUG_IN_USE', slug });
      }

      await updateShortlink(id, {
        slug,
        destinationUrl,
        useAdInterstitial,
        adDurationSeconds,
        isIndexed,
        metaTitle,
        metaDescription,
        fixedAdId
      });

      return { success: true, action: 'update' };
    } catch (e) {
      console.error('Error updating shortlink:', e);
      return fail(500, { message: 'SL_UPDATE_FAIL' });
    }
  },

  delete: async ({ request, cookies }) => {
    const token = cookies.get('admin_session');
    const username = await validateSession(token || '');
    if (!username) {
      return fail(401, { message: 'UNAUTHORIZED' });
    }

    const data = await request.formData();
    const id = data.get('id') as string;

    if (!id) {
      return fail(400, { message: 'SL_ID_REQUIRED' });
    }

    try {
      await deleteShortlink(id);
      return { success: true, action: 'delete' };
    } catch (e) {
      console.error('Error deleting shortlink:', e);
      return fail(500, { message: 'SL_DELETE_FAIL' });
    }
  }
};
