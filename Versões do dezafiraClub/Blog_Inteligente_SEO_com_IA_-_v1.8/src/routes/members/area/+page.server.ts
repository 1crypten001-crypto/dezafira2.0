import { redirect, error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getAllCourses, getSettings, queryOne, getUserCoursePurchases } from '$lib/server/database';

export const load: PageServerLoad = async ({ locals }) => {
  const settings = await getSettings();
  if (settings.enable_member_login !== '1') throw redirect(303, '/');
  if (!locals.user) throw redirect(303, '/members/login?redirectTo=/members/area');

  const courses = await getAllCourses(true);
  const coursePurchases = await getUserCoursePurchases(locals.user.id);

  // Check premium subscription
  const subscription = await queryOne(
    `SELECT id FROM premium_subscriptions WHERE user_id = ? AND status = 'active' AND (expires_at IS NULL OR expires_at > datetime('now'))`,
    [locals.user.id]
  );
  const hasPremium = !!subscription || locals.user.role === 'admin';

  // Enrich courses with access info
  const purchasedCourseIds = new Set(coursePurchases.map((p: any) => p.course_id));
  const enrichedCourses = courses.map((c: any) => ({
    ...c,
    hasAccess: c.access_type === 'free' || hasPremium || (c.access_type === 'paid' && purchasedCourseIds.has(c.id))
  }));

  return {
    user: locals.user,
    courses: enrichedCourses,
    hasPremium,
    settings
  };
};
