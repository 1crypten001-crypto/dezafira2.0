import type { RequestHandler } from './$types';
import { getAllPosts, getSettings } from '$lib/server/database';
import { env } from '$env/dynamic/private';
import { htmlLang } from '$lib/i18n';

export const GET: RequestHandler = async ({ url }) => {
  try {
    const posts = await getAllPosts({ limit: 100 });
    const settings = await getSettings();
    const siteUrl = env.SITE_URL || settings.site_url || url.origin;
    const siteName = settings.site_title || 'Blog';
    const siteDesc = settings.site_description || 'Feed RSS do blog';
    const feedLang = htmlLang(settings.site_language || 'pt');

    const rssItems = posts.map(post => `
    <item>
      <title><![CDATA[${post.title}]]></title>
      <link>${siteUrl}/post/${post.slug}</link>
      <guid isPermaLink="true">${siteUrl}/post/${post.slug}</guid>
      <description><![CDATA[${post.excerpt || ''}]]></description>
      <pubDate>${new Date(post.created_at).toUTCString()}</pubDate>
      <author>${post.author_email || 'admin@blog.com'}</author>
      ${post.category_name ? `<category><![CDATA[${post.category_name}]]></category>` : ''}
    </item>`).join('');

    const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title><![CDATA[${siteName}]]></title>
    <link>${siteUrl}</link>
    <description><![CDATA[${siteDesc}]]></description>
    <language>${feedLang}</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${siteUrl}/rss.xml" rel="self" type="application/rss+xml"/>
    ${rssItems}
  </channel>
</rss>`;

    return new Response(rss, {
      headers: {
        'Content-Type': 'application/xml; charset=utf-8',
        'Cache-Control': 'max-age=3600'
      }
    });
  } catch (error) {
    console.error('RSS feed error:', error);
    return new Response('<?xml version="1.0"?><rss version="2.0"></rss>', {
      headers: { 'Content-Type': 'application/xml' }
    });
  }
};