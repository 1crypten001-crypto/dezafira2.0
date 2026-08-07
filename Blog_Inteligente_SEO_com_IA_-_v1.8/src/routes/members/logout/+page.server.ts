import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
  // We only support POST for actions or simple redirect for load
  throw redirect(303, '/');
};

export const actions = {
  default: async ({ cookies }) => {
    cookies.delete('member_session', { path: '/' });
    throw redirect(303, '/');
  }
};
