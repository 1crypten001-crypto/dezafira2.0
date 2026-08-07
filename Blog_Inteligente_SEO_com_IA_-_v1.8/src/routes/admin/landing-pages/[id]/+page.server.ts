import { error, redirect, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { getLandingPageById, updateLandingPage, getLandingPageBySlug, getAllProducts } from '$lib/server/database';
import { uploadImage } from '$lib/server/cloudinary';
import { env } from '$env/dynamic/private';
import fs from 'fs';
import path from 'path';

export const load: PageServerLoad = async ({ params, cookies }) => {
  const adminSession = cookies.get('admin_session');
  if (!adminSession) {
    throw redirect(302, '/admin/login');
  }

  const id = parseInt(params.id);
  if (isNaN(id)) {
    throw error(400, 'ID da página inválido.');
  }

  const landingPage = await getLandingPageById(id);
  if (!landingPage) {
    throw error(404, 'Landing page não encontrada.');
  }

  // Products for "link product" picker on buttons / CTAs / pricing
  let products: any[] = [];
  try {
    products = await getAllProducts();
  } catch {
    products = [];
  }

  return {
    landingPage,
    products: products.map((p) => ({
      id: p.id,
      name: p.name,
      slug: p.slug,
      price_cents: p.price_cents
    }))
  };
};

export const actions: Actions = {
  save: async ({ request, params, cookies }) => {
    const adminSession = cookies.get('admin_session');
    if (!adminSession) {
      throw redirect(302, '/admin/login');
    }

    const id = parseInt(params.id);
    if (isNaN(id)) {
      return fail(400, { error: 'ID inválido.' });
    }

    const data = await request.formData();
    const title = data.get('title') as string;
    let slug = data.get('slug') as string;
    const status = data.get('status') as string;
    const content = data.get('content') as string;
    const settings = data.get('settings') as string;

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

    // Verificar unicidade do slug
    const existing = await getLandingPageBySlug(slug);
    if (existing && existing.id !== id) {
      return fail(400, { error: 'Este slug já está em uso por outra página.' });
    }

    try {
      await updateLandingPage(id, title, slug, status, content, settings);
      return { success: true };
    } catch (e) {
      console.error('Erro ao salvar landing page:', e);
      return fail(500, { error: 'Erro interno ao salvar no banco de dados.' });
    }
  },

  uploadImage: async ({ request, cookies }) => {
    const adminSession = cookies.get('admin_session');
    if (!adminSession) {
      return fail(401, { error: 'Não autorizado.' });
    }

    const data = await request.formData();
    const file = data.get('file');

    if (!file || !(file instanceof File) || file.size === 0) {
      return fail(400, { error: 'Nenhum arquivo enviado.' });
    }

    try {
      const isCloudinaryConfigured = !!(
        env.CLOUDINARY_CLOUD_NAME &&
        env.CLOUDINARY_API_KEY &&
        env.CLOUDINARY_API_SECRET
      );

      if (isCloudinaryConfigured) {
        // Upload para Cloudinary na pasta landings
        const imageUrl = await uploadImage(file, 'blog/landings');
        return { success: true, url: imageUrl };
      } else {
        // Fallback local
        const buffer = Buffer.from(await file.arrayBuffer());
        const extension = file.name.split('.').pop() || 'jpg';
        const filename = `landing-img-${Date.now()}.${extension}`;

        const uploadDir = path.join(process.cwd(), 'static', 'uploads', 'landings');
        if (!fs.existsSync(uploadDir)) {
          fs.mkdirSync(uploadDir, { recursive: true });
        }

        fs.writeFileSync(path.join(uploadDir, filename), buffer);
        const imageUrl = `/uploads/landings/${filename}`;
        return { success: true, url: imageUrl };
      }
    } catch (e) {
      console.error('Erro ao fazer upload da imagem no builder:', e);
      return fail(500, { error: 'Erro interno ao fazer upload.' });
    }
  }
};
