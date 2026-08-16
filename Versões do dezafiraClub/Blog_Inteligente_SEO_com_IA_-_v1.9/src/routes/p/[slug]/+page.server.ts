import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getLandingPageBySlug } from '$lib/server/database';
import { parseAndSanitizeLandingContent } from '$lib/server/landing-pages';

export const load: PageServerLoad = async ({ params, cookies }) => {
  const { slug } = params;

  if (!slug) {
    throw error(400, 'Slug inválido.');
  }

  const landingPage = await getLandingPageBySlug(slug);

  if (!landingPage) {
    throw error(404, 'Página não encontrada.');
  }

  // Se for rascunho, só permite visualização se for administrador logado
  if (landingPage.status === 'draft') {
    const adminSession = cookies.get('admin_session');
    if (!adminSession) {
      throw error(404, 'Página não encontrada.');
    }
  }

  return {
    landingPage: {
      ...landingPage,
      content: parseAndSanitizeLandingContent(landingPage.content || '[]')
    }
  };
};
