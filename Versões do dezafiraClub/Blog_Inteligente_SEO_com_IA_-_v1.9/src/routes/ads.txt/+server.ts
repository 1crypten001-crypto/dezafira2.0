import type { RequestHandler } from './$types';
import { getSettings } from '$lib/server/database';

export const GET: RequestHandler = async () => {
  const settings = await getSettings();
  const adsTxt = settings.ads_txt || '';

  return new Response(adsTxt, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, must-revalidate'
    }
  });
};
