import { fail, error, redirect } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import {
  getCourseById, updateCourse, deleteCourse, generateUniqueCourseSlug,
  getLessonsByCourseId, createLesson, updateLesson, deleteLesson,
  getMaterialsByCourseId, createMaterial, deleteMaterial
} from '$lib/server/database';

export const load: PageServerLoad = async ({ params }) => {
  const id = parseInt(params.id);
  if (isNaN(id)) throw error(404, 'Curso não encontrado');

  const course = await getCourseById(id);
  if (!course) throw error(404, 'Curso não encontrado');

  const lessons = await getLessonsByCourseId(id);
  const materials = await getMaterialsByCourseId(id);

  return { course, lessons, materials };
};

export const actions: Actions = {
  updateCourse: async ({ request, params }) => {
    const id = parseInt(params.id);
    const data = await request.formData();
    const title = (data.get('title') as string)?.trim();
    const description = (data.get('description') as string)?.trim() || null;
    const cover_image = (data.get('cover_image') as string)?.trim() || null;
    const access_type = (data.get('access_type') as string) || 'premium';
    const price_cents = Math.round(parseFloat(((data.get('price') as string) || '0').replace(',', '.')) * 100) || 0;
    const published = data.get('published') === '1' ? 1 : 0;

    if (!title) return fail(400, { courseError: 'Título obrigatório' });

    const slug = await generateUniqueCourseSlug(title, id);
    await updateCourse(id, { title, slug, description, cover_image, access_type, price_cents, published });
    return { courseSuccess: 'Curso atualizado!' };
  },

  addLesson: async ({ request, params }) => {
    const courseId = parseInt(params.id);
    const data = await request.formData();
    const title = (data.get('title') as string)?.trim();
    const content = (data.get('content') as string) || null;
    const video_url = (data.get('video_url') as string)?.trim() || null;
    const video_type = (data.get('video_type') as string) || 'youtube';
    const topic = (data.get('topic') as string)?.trim() || null;
    const is_preview = data.get('is_preview') === '1' ? 1 : 0;
    const published = data.get('published') === '1' ? 1 : 0;

    if (!title) return fail(400, { lessonError: 'Título da aula obrigatório' });

    // Get next sort order
    const lessons = await getLessonsByCourseId(courseId);
    const sort_order = lessons.length;

    await createLesson({ course_id: courseId, title, content, video_url, video_type, topic, sort_order, published, is_preview });
    return { lessonSuccess: 'Aula adicionada!' };
  },

  updateLesson: async ({ request }) => {
    const data = await request.formData();
    const id = parseInt(data.get('lesson_id') as string);
    const title = (data.get('title') as string)?.trim();
    const content = (data.get('content') as string) || null;
    const video_url = (data.get('video_url') as string)?.trim() || null;
    const video_type = (data.get('video_type') as string) || 'youtube';
    const topic = (data.get('topic') as string)?.trim() || null;
    const is_preview = data.get('is_preview') === '1' ? 1 : 0;
    const published = data.get('published') === '1' ? 1 : 0;
    const sort_order = parseInt(data.get('sort_order') as string) || 0;

    if (!title || isNaN(id)) return fail(400, { lessonError: 'Dados inválidos' });
    await updateLesson(id, { title, content, video_url, video_type, topic, sort_order, published, is_preview });
    return { lessonSuccess: 'Aula atualizada!' };
  },

  deleteLesson: async ({ request }) => {
    const data = await request.formData();
    const id = parseInt(data.get('lesson_id') as string);
    if (isNaN(id)) return fail(400, { lessonError: 'ID inválido' });
    await deleteLesson(id);
    return { lessonSuccess: 'Aula removida!' };
  },

  addMaterial: async ({ request, params }) => {
    const courseId = parseInt(params.id);
    const data = await request.formData();
    const title = (data.get('title') as string)?.trim();
    const description = (data.get('description') as string)?.trim() || null;
    const file_url = (data.get('file_url') as string)?.trim();
    const file_type = (data.get('file_type') as string)?.trim() || null;

    if (!title || !file_url) return fail(400, { materialError: 'Título e URL do arquivo são obrigatórios' });
    await createMaterial({ course_id: courseId, title, description, file_url, file_type });
    return { materialSuccess: 'Material adicionado!' };
  },

  deleteMaterial: async ({ request }) => {
    const data = await request.formData();
    const id = parseInt(data.get('material_id') as string);
    if (isNaN(id)) return fail(400, { materialError: 'ID inválido' });
    await deleteMaterial(id);
    return { materialSuccess: 'Material removido!' };
  },

  deleteCourse: async ({ params }) => {
    const id = parseInt(params.id);
    await deleteCourse(id);
    throw redirect(303, '/admin/courses');
  }
};
