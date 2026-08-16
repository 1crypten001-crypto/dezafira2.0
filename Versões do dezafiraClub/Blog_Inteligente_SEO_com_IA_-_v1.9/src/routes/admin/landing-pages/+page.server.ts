import { fail, redirect } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { 
  getLandingPagesPage,
  createLandingPage, 
  deleteLandingPage, 
  updateLandingPage,
  getLandingPageBySlug,
  getLandingPageById,
  duplicateLandingPage,
  getCLITokenStatus,
  regenerateCLIToken
} from '$lib/server/database';

export const load: PageServerLoad = async ({ cookies, url }) => {
  const adminSession = cookies.get('admin_session');
  if (!adminSession) {
    throw redirect(302, '/admin/login');
  }

  const requestedPage = Math.max(1, Number.parseInt(url.searchParams.get('page') || '1', 10) || 1);
  const search = (url.searchParams.get('q') || '').trim().slice(0, 100);
  const [landingResult, cliTokenStatus] = await Promise.all([
    getLandingPagesPage({ page: requestedPage, limit: 20, search }),
    getCLITokenStatus()
  ]);

  if (landingResult.total > 0 && requestedPage > landingResult.totalPages) {
    const params = new URLSearchParams();
    if (search) params.set('q', search);
    params.set('page', String(landingResult.totalPages));
    throw redirect(302, `/admin/landing-pages?${params}`);
  }

  return {
    landingPages: landingResult.pages,
    search,
    pagination: {
      page: landingResult.page,
      limit: landingResult.limit,
      total: landingResult.total,
      totalPages: landingResult.totalPages
    },
    cliTokenConfigured: cliTokenStatus.configured,
    cliTokenExpiresAt: cliTokenStatus.expiresAt
  };
};

export const actions: Actions = {
  regenerateCliToken: async ({ cookies }) => {
    const adminSession = cookies.get('admin_session');
    if (!adminSession) throw redirect(302, '/admin/login');
    try {
      const token = await regenerateCLIToken();
      const status = await getCLITokenStatus();
      return { cliTokenSuccess: true, cliToken: token, cliTokenExpiresAt: status.expiresAt };
    } catch (e) {
      console.error('Erro ao regenerar token da CLI de landings:', e);
      return fail(500, { error: 'Erro ao regenerar o token da CLI.' });
    }
  },

  create: async ({ request, cookies }) => {
    const adminSession = cookies.get('admin_session');
    if (!adminSession) {
      throw redirect(302, '/admin/login');
    }

    const data = await request.formData();
    const title = data.get('title') as string;
    let slug = data.get('slug') as string;

    if (!title || title.trim() === '') {
      return fail(400, { error: 'O título é obrigatório.' });
    }

    // Normalizar slug se não for enviado
    if (!slug || slug.trim() === '') {
      slug = title
        .toLowerCase()
        .trim()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/[\s_]+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-+|-+$/g, '')
        .substring(0, 60);
    } else {
      slug = slug
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/[\s_]+/g, '-')
        .replace(/-+/g, '-');
    }

    if (!slug) {
      return fail(400, { error: 'O slug gerado é inválido.' });
    }

    // Verificar se o slug já existe
    const existing = await getLandingPageBySlug(slug);
    if (existing) {
      return fail(400, { error: 'Este slug de página já está em uso.' });
    }

    try {
      const pageId = await createLandingPage(title, slug);
      // Redireciona diretamente para o editor
      throw redirect(303, `/admin/landing-pages/${pageId}`);
    } catch (e: any) {
      if (e.status === 303) throw e;
      console.error('Erro ao criar landing page:', e);
      return fail(500, { error: 'Erro interno ao salvar no banco de dados.' });
    }
  },

  update: async ({ request, cookies }) => {
    const adminSession = cookies.get('admin_session');
    if (!adminSession) {
      throw redirect(302, '/admin/login');
    }

    const data = await request.formData();
    const id = parseInt(data.get('id') as string);
    const title = data.get('title') as string;
    let slug = data.get('slug') as string;
    const status = data.get('status') as string;

    if (isNaN(id)) {
      return fail(400, { error: 'ID inválido.' });
    }

    if (!title || title.trim() === '') {
      return fail(400, { error: 'O título é obrigatório.' });
    }

    if (!slug || slug.trim() === '') {
      return fail(400, { error: 'O slug é obrigatório.' });
    }

    slug = slug
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/[\s_]+/g, '-')
      .replace(/-+/g, '-');

    // Verificar se o slug já existe em outra página
    const existing = await getLandingPageBySlug(slug);
    if (existing && existing.id !== id) {
      return fail(400, { error: 'Este slug de página já está em uso.' });
    }

    try {
      const pageToUpdate = await getLandingPageById(id);
      if (!pageToUpdate) {
        return fail(404, { error: 'Landing page não encontrada.' });
      }
      await updateLandingPage(id, title, slug, status);
      return { success: true };
    } catch (e) {
      console.error('Erro ao atualizar landing page:', e);
      return fail(500, { error: 'Erro interno ao atualizar no banco de dados.' });
    }
  },

  delete: async ({ request, cookies }) => {
    const adminSession = cookies.get('admin_session');
    if (!adminSession) {
      throw redirect(302, '/admin/login');
    }

    const data = await request.formData();
    const id = parseInt(data.get('id') as string);

    if (isNaN(id)) {
      return fail(400, { error: 'ID inválido.' });
    }

    try {
      await deleteLandingPage(id);
      return { success: true };
    } catch (e) {
      console.error('Erro ao excluir landing page:', e);
      return fail(500, { error: 'Erro interno ao excluir no banco de dados.' });
    }
  },

  duplicate: async ({ request, cookies }) => {
    const adminSession = cookies.get('admin_session');
    if (!adminSession) {
      throw redirect(302, '/admin/login');
    }

    const data = await request.formData();
    const id = parseInt(data.get('id') as string);

    if (isNaN(id)) {
      return fail(400, { error: 'ID inválido.' });
    }

    try {
      const newId = await duplicateLandingPage(id);
      throw redirect(303, `/admin/landing-pages/${newId}`);
    } catch (e: any) {
      if (e?.status === 303) throw e;
      console.error('Erro ao duplicar landing page:', e);
      return fail(500, { error: 'Erro ao duplicar a página.' });
    }
  }
};
