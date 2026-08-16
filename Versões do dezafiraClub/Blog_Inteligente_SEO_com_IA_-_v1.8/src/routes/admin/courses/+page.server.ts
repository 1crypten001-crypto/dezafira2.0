import { fail, redirect } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { getAllCourses, deleteCourse } from '$lib/server/database';

export const load: PageServerLoad = async () => {
  const courses = await getAllCourses();
  return { courses };
};

export const actions: Actions = {
  delete: async ({ request }) => {
    const data = await request.formData();
    const id = parseInt(data.get('id') as string);
    if (isNaN(id)) return fail(400, { message: 'ID inválido' });
    try {
      await deleteCourse(id);
      return { success: true };
    } catch (e) {
      console.error(e);
      return fail(500, { message: 'Erro ao deletar curso' });
    }
  }
};
