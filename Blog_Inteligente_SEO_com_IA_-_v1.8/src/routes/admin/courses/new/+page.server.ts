import { fail, redirect } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { createCourse, generateUniqueCourseSlug } from '$lib/server/database';

export const load: PageServerLoad = async () => {
  return {};
};

export const actions: Actions = {
  default: async ({ request }) => {
    const data = await request.formData();
    const title = (data.get('title') as string)?.trim();
    const description = (data.get('description') as string)?.trim() || null;
    const cover_image = (data.get('cover_image') as string)?.trim() || null;
    const access_type = (data.get('access_type') as string) || 'premium';
    const price_str = (data.get('price') as string)?.replace(',', '.') || '0';
    const price_cents = Math.round(parseFloat(price_str || '0') * 100) || 0;
    const published = data.get('published') === '1' ? 1 : 0;

    if (!title) return fail(400, { error: 'Título obrigatório', values: Object.fromEntries(data) });

    const slug = await generateUniqueCourseSlug(title);

    try {
      await createCourse({ title, slug, description, cover_image, access_type, price_cents, published });
      throw redirect(303, '/admin/courses');
    } catch (e: any) {
      if (e?.status === 303) throw e;
      console.error(e);
      return fail(500, { error: 'Erro ao criar curso' });
    }
  }
};
