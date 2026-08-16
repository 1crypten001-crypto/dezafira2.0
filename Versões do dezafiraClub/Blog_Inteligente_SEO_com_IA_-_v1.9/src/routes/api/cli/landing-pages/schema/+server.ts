import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { LANDING_CLI_MANIFEST } from '$lib/landing-cli-manifest';
import { requireCLIToken } from '../../auth';

export const GET: RequestHandler = async ({ request, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
  if (authError) return authError;
  return json(LANDING_CLI_MANIFEST, {
    headers: { 'cache-control': 'private, max-age=300' }
  });
};
