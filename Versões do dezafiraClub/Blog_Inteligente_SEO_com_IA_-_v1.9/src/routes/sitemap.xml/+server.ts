import type { RequestHandler } from './$types';
import { getAllPosts, getAllCategories, getIndexedShortlinks, getPublishedWebStories } from '$lib/server/database';

export const GET: RequestHandler = async ({ url }) => {
  try {
    const [posts, categories, shortlinks, webStories] = await Promise.all([
      getAllPosts({ limit: 500 }),
      getAllCategories(),
      getIndexedShortlinks(),
      getPublishedWebStories(100)
    ]);

    // Whitelabel: dynamically get the requested origin (e.g. https://dailyitgirl.com)
    // rather than relying on hardcoded settings
    const siteUrl = url.origin;

    const staticPages = [
      { url: '/', priority: '1.0', changefreq: 'daily' },
      { url: '/categories', priority: '0.7', changefreq: 'weekly' },
      { url: '/products', priority: '0.8', changefreq: 'weekly' },
      { url: '/premium', priority: '0.7', changefreq: 'weekly' },
      { url: '/contact', priority: '0.5', changefreq: 'monthly' }
    ];
    
    const today = new Date().toISOString();
    
    function formatSitemapDate(dateStr: string | null | undefined): string {
      if (!dateStr) return today;
      try {
        // SQLite dates usually come as "YYYY-MM-DD HH:MM:SS"
        const isoString = dateStr.replace(' ', 'T');
        // Let Date parse it. If it doesn't have Z, the browser assumes local, but for sitemap standard ISO is enough
        const d = new Date(isoString);
        if (!isNaN(d.getTime())) return d.toISOString();
        return today;
      } catch {
        return today;
      }
    }

    const urls = [
      ...staticPages.map(page => `
  <url>
    <loc>${siteUrl}${page.url}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
  </url>`),
      ...categories.map(cat => `
  <url>
    <loc>${siteUrl}/category/${cat.slug}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>`),
      ...posts.map(post => `
  <url>
    <loc>${siteUrl}/post/${post.slug}</loc>
    <lastmod>${formatSitemapDate(post.updated_at || post.created_at)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>${post.is_featured ? '0.9' : '0.7'}</priority>
  </url>`),
      ...shortlinks.map(link => `
  <url>
    <loc>${siteUrl}/l/${link.slug}</loc>
    <lastmod>${formatSitemapDate(link.updated_at || link.created_at)}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>`),
      ...webStories.map(story => `
  <url>
    <loc>${siteUrl}/stories/${story.slug}</loc>
    <lastmod>${formatSitemapDate(story.updated_at || story.created_at)}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>`)
    ].join('');

    const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
${urls}
</urlset>`;
    return new Response(sitemap, {
      headers: {
        'Content-Type': 'application/xml; charset=utf-8',
        'Cache-Control': 'max-age=3600'
      }
    });
  } catch (error) {
    console.error('Sitemap error:', error);
    return new Response('<?xml version="1.0"?><urlset></urlset>', {
      headers: { 'Content-Type': 'application/xml' }
    });
  }
};