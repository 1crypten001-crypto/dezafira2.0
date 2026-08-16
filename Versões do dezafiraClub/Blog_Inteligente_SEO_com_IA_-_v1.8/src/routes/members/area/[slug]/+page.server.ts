import { redirect, error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import {
  getCourseBySlug, getLessonsByCourseId, getMaterialsByCourseId,
  getSettings, queryOne, hasUserPurchasedCourse
} from '$lib/server/database';

export const load: PageServerLoad = async ({ params, locals, url }) => {
  const settings = await getSettings();
  if (settings.enable_member_login !== '1') throw redirect(303, '/');
  if (!locals.user) throw redirect(303, `/members/login?redirectTo=${encodeURIComponent(url.pathname)}`);

  const course = await getCourseBySlug(params.slug);
  if (!course || !course.published) throw error(404, 'Curso não encontrado');

  const isAdmin = locals.user.role === 'admin';

  // Check access
  const subscription = await queryOne(
    `SELECT id FROM premium_subscriptions WHERE user_id = ? AND status = 'active' AND (expires_at IS NULL OR expires_at > datetime('now'))`,
    [locals.user.id]
  );
  const hasPremium = !!subscription || isAdmin;

  let hasAccess = false;
  if (course.access_type === 'free') hasAccess = true;
  else if (course.access_type === 'premium') hasAccess = hasPremium;
  else if (course.access_type === 'paid') {
    hasAccess = hasPremium || await hasUserPurchasedCourse(locals.user.id, course.id);
  }

  // Get lessons (published only for non-admins)
  const allLessons = await getLessonsByCourseId(course.id, !isAdmin);
  const materials = await getMaterialsByCourseId(course.id);

  // Selected lesson from query param
  const lessonId = url.searchParams.get('aula');
  const selectedLesson = lessonId
    ? allLessons.find((l: any) => l.id === parseInt(lessonId)) ?? allLessons[0]
    : allLessons[0];

  // Strip video_url from lessons before sending to client (protection)
  const safeLessons = allLessons.map((l: any) => ({
    id: l.id, title: l.title, sort_order: l.sort_order,
    published: l.published, is_preview: l.is_preview,
    has_video: !!l.video_url, has_content: !!l.content
  }));

  // For the selected lesson, include content but not video_url
  const safeSelectedLesson = selectedLesson ? {
    id: selectedLesson.id,
    title: selectedLesson.title,
    content: selectedLesson.content,
    has_video: !!selectedLesson.video_url,
    video_type: selectedLesson.video_type,
    is_preview: selectedLesson.is_preview,
    published: selectedLesson.published
  } : null;

  return {
    course,
    lessons: safeLessons,
    selectedLesson: safeSelectedLesson,
    materials,
    hasAccess,
    hasPremium,
    user: locals.user,
    settings
  };
};
