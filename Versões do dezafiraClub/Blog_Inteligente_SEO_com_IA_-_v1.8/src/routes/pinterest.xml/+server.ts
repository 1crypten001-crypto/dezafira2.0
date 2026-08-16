import { getPostsForPinterest, getSettings } from '$lib/server/database';
import { sanitizeHtml } from '$lib/server/sanitize';
import { getTenantId } from '$lib/server/tenant';

export const GET = async ({ url }) => {
  const tenantId = getTenantId();
  const posts = await getPostsForPinterest(tenantId);
  const settings = await getSettings(tenantId);
  const siteTitle = settings.site_title || 'Blog';
  const siteDescription = settings.site_description || '';
  const siteURL = (settings.site_url || url.origin).replace(/\/$/, '');

  const rss = `<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
  xmlns:media="http://search.yahoo.com/mrss/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>${escapeXml(siteTitle)}</title>
  <description>${escapeXml(siteDescription)}</description>
  <link>${siteURL}</link>
  <atom:link href="${siteURL}/pinterest.xml" rel="self" type="application/rss+xml" />
  <language>pt-br</language>
  <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
  <generator>Tube Writer - SvelteKit Blog</generator>
  ${posts
    .map((post) => {
      // Usar pinterest_image se disponível, senão usar cover_image como fallback
      const imageUrl = toAbsoluteUrl(post.pinterest_image || post.cover_image || '', siteURL);
      
      // Sanitizar conteúdo para prevenir XSS
      const sanitizedContent = sanitizeHtml(post.content || post.excerpt || post.title);
      const mimeType = imageUrl ? getMimeType(imageUrl) : 'image/jpeg';
      const imageTag = imageUrl ? `<img src="${escapeXml(imageUrl)}" />` : '';
      
      return `
    <item>
      <title>${escapeXml(post.title)}</title>
      <description>${escapeXml(post.excerpt || post.title)}</description>
      <link>${siteURL}/post/${post.slug}</link>
      <guid isPermaLink="true">${siteURL}/post/${post.slug}</guid>
      <pubDate>${new Date(post.created_at).toUTCString()}</pubDate>
      <content:encoded><![CDATA[${imageTag} ${sanitizedContent}]]></content:encoded>
      ${imageUrl ? `
      <media:content url="${escapeXml(imageUrl)}" medium="image" width="1000" height="1500">
        <media:title type="plain">${escapeXml(post.title)}</media:title>
      </media:content>
      <enclosure url="${escapeXml(imageUrl)}" type="${mimeType}" length="1024" />
      ` : ''}
    </item>`;
    })
    .join('')}
</channel>
</rss>`;

  return new Response(rss, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'public, max-age=3600'
    }
  });
};

function escapeXml(unsafe: string) {
  return unsafe.replace(/[<>&'"]/g, (c) => {
    switch (c) {
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '&': return '&amp;';
      case '\'': return '&apos;';
      case '"': return '&quot;';
      default: return c;
    }
  });
}

function toAbsoluteUrl(value: string, siteURL: string) {
  if (!value) return '';
  if (value.startsWith('http://') || value.startsWith('https://')) return value;
  if (value.startsWith('/')) return `${siteURL}${value}`;
  return `${siteURL}/${value}`;
}

function getMimeType(url: string) {
  const ext = url.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'png': return 'image/png';
    case 'gif': return 'image/gif';
    case 'webp': return 'image/webp';
    case 'svg': return 'image/svg+xml';
    default: return 'image/jpeg';
  }
}
