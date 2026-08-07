import { JSDOM } from 'jsdom';

const ALLOWED_TAGS = new Set([
  'p','br','b','i','u','em','strong','h1','h2','h3','h4','h5','h6',
  'ul','ol','li','a','img','blockquote','pre','code','span','div',
  'figure','figcaption','table','thead','tbody','tr','th','td',
  'section','article','header','footer','nav','aside','main',
  'div','span','small','sup','sub','mark','del','ins'
]);

const ALLOWED_PROTOCOLS = ['http:', 'https:', 'mailto:'];

const FORBIDDEN_TAGS = new Set(['script','style','iframe','form','input','button','select','textarea','object','embed','applet']);

const FORBIDDEN_ATTRS = [
  'onerror','onclick','onload','onmouseover','onfocus','onblur','onchange','onsubmit',
  'onkeydown','onkeyup','onkeypress','onabort','onbeforeunload','oncanplay','oncanplaythrough',
  'oncontextmenu','oncopy','oncuechange','oncut','ondblclick','ondeactivate','ondrag',
  'ondragend','ondragenter','ondragleave','ondragover','ondragstart','ondrop',
  'ondurationchange','onemptied','onended','onfocus','onhashchange','oninput','oninvalid',
  'onkeydown','onkeypress','onkeyup','onload','onloadeddata','onloadedmetadata','onloadstart',
  'onmessage','onmousedown','onmouseenter','onmouseleave','onmousemove','onmouseout',
  'onmouseover','onmouseup','onmousewheel','onoffline','ononline','onpagehide','onpageshow',
  'onpause','onplay','onplaying','onpopstate','onprogress','onratechange','onredo','onreset',
  'onresize','onrowdelete','onrowinserted','onstorage','onsubmit','ontimeupdate','onundo',
  'onunload','onvolumechange','onwaiting','onwheel','onauxclick','ondblclick','ondragend',
  'ondragenter','ondragleave','ondragover','ondragstart','ondrop','onfocusin','onfocusout',
  'onmouseenter','onmouseleave','onmozfullscreenchange','onmozfullscreenerror','onpointerdown',
  'onpointerlockchange','onpointerlockerror','onpointermove','onpointerout','onpointerover',
  'onpointerup','onratechange','onresize','onscroll','onscrollend','ontoggle','ontransitionend',
  'onwheel'
];

export function sanitizeHtml(html: string): string {
  if (typeof html !== 'string') return '';

  try {
    const dom = new JSDOM(html, { pretendToBeVisual: true });
    const doc = dom.window.document;

    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_ELEMENT, null);
    const nodesToRemove: Node[] = [];

    let node: Element | null;
    while ((node = walker.nextNode() as Element | null)) {
      if (FORBIDDEN_TAGS.has(node.tagName.toLowerCase())) {
        nodesToRemove.push(node);
        continue;
      }

      const attrs = node.attributes;
      for (let i = attrs.length - 1; i >= 0; i--) {
        const attr = attrs[i];
        if (FORBIDDEN_ATTRS.includes(attr.name.toLowerCase()) || attr.name.startsWith('on')) {
          node.removeAttribute(attr.name);
        }
      }

      if (node.tagName.toLowerCase() === 'a') {
        const href = node.getAttribute('href') || '';
        if (href && !ALLOWED_PROTOCOLS.some(p => href.startsWith(p))) {
          node.removeAttribute('href');
        }
        node.setAttribute('target', '_blank');
        node.setAttribute('rel', 'noopener noreferrer');
      }

      if (node.tagName.toLowerCase() === 'img') {
        const src = node.getAttribute('src') || '';
        if (src && !ALLOWED_PROTOCOLS.some(p => src.startsWith(p))) {
          node.removeAttribute('src');
        }
      }
    }

    for (const n of nodesToRemove) {
      n.parentNode?.removeChild(n);
    }

    return doc.body.innerHTML;
  } catch {
    return html;
  }
}

export function sanitizeText(text: string): string {
  if (typeof text !== 'string') return '';
  return text
    .replace(/[<>]/g, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+=/gi, '')
    .trim()
    .slice(0, 10000);
}

export function sanitizeFilename(filename: string): string {
  if (typeof filename !== 'string') return 'file';
  return filename.replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 255);
}

export function escapeHtml(text: string): string {
  if (typeof text !== 'string') return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function unescapeHtml(text: string): string {
  if (typeof text !== 'string') return '';
  return text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'");
}

export function stripAllTags(html: string): string {
  if (typeof html !== 'string') return '';
  try {
    const dom = new JSDOM(`<div>${html}</div>`);
    return dom.window.document.body.textContent || '';
  } catch {
    return html.replace(/<[^>]*>/g, '');
  }
}

export function truncate(text: string, maxLen: number): string {
  if (typeof text !== 'string') return '';
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen).replace(/\s+\S*$/, '') + '…';
}

export function slugify(text: string): string {
  if (typeof text !== 'string') return '';
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
}

export function extractPlainText(html: string, maxLength?: number): string {
  let text = stripAllTags(html);
  text = text.replace(/\s+/g, ' ').trim();
  if (maxLength) text = truncate(text, maxLength);
  return text;
}

export function sanitizeAds(ads: any[]): any[] {
  if (!Array.isArray(ads)) return [];
  return ads.map(ad => ({
    id: ad.id,
    name: sanitizeText(ad.name || ''),
    placement: ad.placement,
    type: ad.type,
    content: ad.type === 'text' ? sanitizeHtml(ad.content || '') : ad.content,
    image_url: ad.image_url,
    link_url: ad.link_url,
    is_active: ad.is_active,
    weight: ad.weight || 1,
    youtube_video_url: ad.youtube_video_url || null,
  }));
}