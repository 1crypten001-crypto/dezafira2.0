/**
 * SvelteKit Server Hooks
 * 
 * Aplica segurança global: headers, CSRF, rate limiting
 */

import type { Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import { recordPageView, getUserByUsername, getSettings } from '$lib/server/database';
import { validateSession } from '$lib/server/auth';
import { htmlLang } from '$lib/i18n';

// Simple performance logging + html lang for SSR
const performanceHandle: Handle = async ({ event, resolve }) => {
  const start = Date.now();
  let lang = 'pt';
  try {
    const settings = await getSettings();
    lang = settings.site_language || 'pt';
  } catch {
    // ignore settings failures during early boot
  }

  const langAttr = htmlLang(lang);
  const result = await resolve(event, {
    transformPageChunk: ({ html }) => {
      if (/<html[^>]*\slang=/.test(html)) {
        return html.replace(/<html([^>]*)\slang="[^"]*"/, `<html$1 lang="${langAttr}"`);
      }
      return html.replace('<html', `<html lang="${langAttr}"`);
    }
  });
  const duration = Date.now() - start;

  if (process.env.NODE_ENV !== 'production' && duration > 200) {
    console.log(`[PERF] ${event.request.method} ${event.url.pathname}: ${duration}ms`);
  }

  return result;
};

// Authentication handler
const authHandle: Handle = async ({ event, resolve }) => {
  const token = event.cookies.get('member_session');
  if (token) {
    try {
      const username = await validateSession(token);
      if (username) {
        const dbUser = await getUserByUsername(username);
        if (dbUser) {
          event.locals.user = {
            id: dbUser.id,
            username: dbUser.username,
            role: dbUser.role || 'member',
            name: dbUser.name || '',
            cpf: dbUser.cpf || '',
            phone: dbUser.phone || ''
          };
        }
      }
    } catch (e) {
      console.error('[AUTH HOOK] Error validating session:', e);
    }
  }
  return resolve(event);
};

// Analytics page view tracker
const analyticsHandle: Handle = async ({ event, resolve }) => {
  const pathname = event.url.pathname;
  const isGet = event.request.method === 'GET';
  const isAsset = pathname.includes('.') || pathname.startsWith('/_app/') || pathname.startsWith('/images/') || pathname.startsWith('/favicon.png');
  const isAdminOrApi = pathname.startsWith('/admin') || pathname.startsWith('/api') || pathname.startsWith('/auth');

  // Detect prefetch, prerender or preview requests to avoid counting fake page views.
  // Chrome, Firefox, Safari and SvelteKit send specific headers when speculative preloading is active.
  const headers = event.request.headers;
  const purpose = headers.get('purpose') || '';
  const secPurpose = headers.get('sec-purpose') || '';
  const xPurpose = headers.get('x-purpose') || '';
  const xMoz = headers.get('x-moz') || '';

  const isPrefetch =
    purpose === 'prefetch' ||
    secPurpose === 'prefetch' ||
    secPurpose === 'prerender' ||
    xPurpose === 'prefetch' ||
    xPurpose === 'preview' ||
    xMoz === 'prefetch' ||
    headers.has('x-sveltekit-preload');

  if (isGet && !isAsset && !isAdminOrApi && !isPrefetch) {
    let ip = '127.0.0.1';
    try {
      ip = event.getClientAddress() || '127.0.0.1';
    } catch (e) {
      // ignore client address failures in local dev
    }
    const userAgent = event.request.headers.get('user-agent') || '';
    recordPageView(pathname, ip, userAgent).catch((err) => {
      console.error('[ANALYTICS] Error tracking page view:', err);
    });
  }

  return resolve(event);
};

const cacheControlHandle: Handle = async ({ event, resolve }) => {
  const response = await resolve(event);
  const contentType = response.headers.get('content-type') || '';
  
  if (contentType.includes('text/html')) {
    response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate');
    response.headers.set('Pragma', 'no-cache');
    response.headers.set('Expires', '0');
  }
  
  return response;
};

export const handle: Handle = sequence(
  performanceHandle,
  authHandle,
  analyticsHandle,
  cacheControlHandle
);