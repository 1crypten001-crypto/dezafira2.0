import { getPinterestEnabledCategories } from '$lib/server/database';
import type { Category } from '$lib/server/database';
import { getSettings } from '$lib/server/database';
import { getTenantId } from '$lib/server/tenant';
import { json } from '@sveltejs/kit';

/**
 * Lista todas as categorias habilitadas para Pinterest
 * Útil para configurar os feeds no Pinterest
 */
export const GET = async ({ url }) => {
  const tenantId = getTenantId();
  const categories = await getPinterestEnabledCategories(tenantId);
  const settings = await getSettings(tenantId);
  const siteURL = (settings.site_url || url.origin).replace(/\/$/, '');

  const feeds = categories.map((category: Category) => ({
    name: category.name,
    slug: category.slug,
    description: category.description || `Feed da categoria ${category.name}`,
    feedUrl: `${siteURL}/pinterest_${category.slug}.xml`,
    legacyFeedUrl: `${siteURL}/pinterest.xml/${category.slug}`,
    categoryUrl: `${siteURL}/category/${category.slug}`
  }));

  return json({
    feeds,
    mainFeedUrl: `${siteURL}/pinterest.xml`,
    totalCategories: feeds.length
  });
};
