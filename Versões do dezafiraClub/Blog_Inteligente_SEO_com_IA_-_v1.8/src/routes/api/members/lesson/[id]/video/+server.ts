import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getLessonById, getCourseById, hasUserPurchasedCourse, queryOne, getSettings } from '$lib/server/database';

function extractVideoId(url: string, type: string): string {
  if (!url) return '';
  if (type === 'youtube' || !type) {
    const m = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/))([a-zA-Z0-9_-]{11})/);
    return m ? m[1] : url;
  }
  if (type === 'vimeo') {
    const m = url.match(/vimeo\.com\/(\d+)/);
    return m ? m[1] : url;
  }
  return url;
}

export const GET: RequestHandler = async ({ params, locals }) => {
  const settings = await getSettings();
  if (settings.enable_member_login !== '1') throw error(403, 'Área de membros desativada');
  if (!locals.user) throw error(401, 'Login necessário');

  const lessonId = parseInt(params.id);
  if (isNaN(lessonId)) throw error(400, 'ID inválido');

  const lesson = await getLessonById(lessonId);
  if (!lesson || !lesson.published) throw error(404, 'Aula não encontrada');

  const course = await getCourseById(lesson.course_id);
  if (!course || !course.published) throw error(404, 'Curso não encontrado');

  // Preview aulas abertas para qualquer membro logado
  if (lesson.is_preview) {
    return json({
      videoId: extractVideoId(lesson.video_url, lesson.video_type),
      videoType: lesson.video_type
    });
  }

  // Verificar acesso por tipo de curso
  const isAdmin = locals.user.role === 'admin';
  if (isAdmin) {
    return json({ videoId: extractVideoId(lesson.video_url, lesson.video_type), videoType: lesson.video_type });
  }

  if (course.access_type === 'free') {
    return json({ videoId: extractVideoId(lesson.video_url, lesson.video_type), videoType: lesson.video_type });
  }

  // Verificar assinatura premium ativa
  const subscription = await queryOne(
    `SELECT id FROM premium_subscriptions WHERE user_id = ? AND status = 'active' AND (expires_at IS NULL OR expires_at > datetime('now'))`,
    [locals.user.id]
  );
  const hasPremium = !!subscription;

  if (course.access_type === 'premium' && hasPremium) {
    return json({ videoId: extractVideoId(lesson.video_url, lesson.video_type), videoType: lesson.video_type });
  }

  if (course.access_type === 'paid') {
    if (hasPremium) {
      return json({ videoId: extractVideoId(lesson.video_url, lesson.video_type), videoType: lesson.video_type });
    }
    const purchased = await hasUserPurchasedCourse(locals.user.id, course.id);
    if (purchased) {
      return json({ videoId: extractVideoId(lesson.video_url, lesson.video_type), videoType: lesson.video_type });
    }
  }

  throw error(403, 'Sem acesso a esta aula');
};
