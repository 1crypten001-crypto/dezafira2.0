import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import crypto from 'crypto';
import {
  createCourse, createLesson, generateUniqueCourseSlug
} from '$lib/server/database';
import { env } from '$env/dynamic/private';

function safeEqual(a: string, b: string): boolean {
  const ba = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ba.length !== bb.length) return false;
  return crypto.timingSafeEqual(ba, bb);
}

/**
 * POST /api/import/member-course
 *
 * Ponte DezafiraAdm → DezafiraClube (Blueprint): cria um curso na área de
 * membros do Clube (member_courses + member_lessons) com texto e vídeo.
 *
 * Body:
 *   {
 *     title: string,
 *     slug?: string,
 *     description?: string,
 *     cover_image?: string,
 *     price_cents?: number,
 *     published?: number,
 *     lessons?: [
 *       { title: string, content?: string, video_url?: string, video_type?: string,
 *         topic?: string, is_preview?: number, sort_order?: number }
 *     ]
 *   }
 *
 * Autenticação: header `x-import-key` == IMPORT_API_KEY (mesma chave da ponte).
 */
export const POST: RequestHandler = async ({ request }) => {
  const importKey = env.IMPORT_API_KEY || '';
  const providedKey = request.headers.get('x-import-key') || '';

  if (!importKey) {
    return json({ success: false, error: 'IMPORT_API_KEY não configurado neste serviço.' }, { status: 503 });
  }
  if (!safeEqual(providedKey, importKey)) {
    return json({ success: false, error: 'Chave de importação inválida.' }, { status: 401 });
  }

  let body: any;
  try {
    body = await request.json();
  } catch {
    return json({ success: false, error: 'JSON inválido.' }, { status: 400 });
  }

  const title = String(body.title || '').trim();
  if (!title) {
    return json({ success: false, error: 'O campo title é obrigatório.' }, { status: 400 });
  }

  try {
    const slug = body.slug
      ? String(body.slug).trim()
      : await generateUniqueCourseSlug(title);

    const insertRes = await createCourse({
      title,
      slug,
      description: body.description ? String(body.description) : null,
      cover_image: body.cover_image ? String(body.cover_image) : null,
      access_type: 'purchase',
      price_cents: Math.max(0, parseInt(body.price_cents) || 0),
      published: body.published !== undefined ? Number(body.published) : 0,
      sort_order: 0
    });

    const courseId = (insertRes as any).lastInsertRowid || (insertRes as any).insertId
      ? Number((insertRes as any).lastInsertRowid ?? (insertRes as any).insertId)
      : null;

    let lessonsCreated = 0;
    if (courseId && Array.isArray(body.lessons)) {
      let order = 0;
      for (const lesson of body.lessons) {
        const lessonTitle = String(lesson.title || '').trim();
        if (!lessonTitle) continue;
        await createLesson({
          course_id: courseId,
          title: lessonTitle,
          content: lesson.content ? String(lesson.content) : null,
          video_url: lesson.video_url ? String(lesson.video_url) : null,
          video_type: lesson.video_type ? String(lesson.video_type) : 'youtube',
          topic: lesson.topic ? String(lesson.topic) : null,
          sort_order: lesson.sort_order !== undefined ? Number(lesson.sort_order) : order,
          published: lesson.published !== undefined ? Number(lesson.published) : 1,
          is_preview: lesson.is_preview ? 1 : 0
        });
        order++;
        lessonsCreated++;
      }
    }

    return json({
      success: true,
      course_id: courseId,
      slug,
      lessons_created: lessonsCreated,
      message: 'Curso criado na área de membros com sucesso.'
    }, { status: 201 });
  } catch (e: any) {
    console.error('[IMPORT MEMBER-COURSE] Erro:', e);
    return json({ success: false, error: e.message || 'Erro ao criar curso na área de membros.' }, { status: 500 });
  }
};
