import { redirect, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { 
  getAllCourses, 
  getSettings, 
  queryOne, 
  getUserCoursePurchases,
  getCommunityTopics,
  createCommunityTopic,
  toggleCommunityLike,
  getAllPremiumPlans
} from '$lib/server/database';

export const load: PageServerLoad = async ({ locals, url }) => {
  const settings = await getSettings();
  if (settings.enable_member_login !== '1') throw redirect(303, '/');

  const selectedCategory = url.searchParams.get('category') || undefined;

  const userId = locals.user?.id || 0;
  const userRole = locals.user?.role || 'guest';

  const courses = await getAllCourses(true);
  const coursePurchases = userId ? await getUserCoursePurchases(userId) : [];
  const premiumPlans = await getAllPremiumPlans();
  const cheapestPlan = premiumPlans && premiumPlans.length > 0 ? premiumPlans[0] : null;

  // Check premium subscription
  const subscription = userId ? await queryOne(
    `SELECT id FROM premium_subscriptions WHERE user_id = ? AND status = 'active' AND (expires_at IS NULL OR expires_at > datetime('now'))`,
    [userId]
  ) : null;
  const hasPremium = !!subscription || userRole === 'admin';

  // Carrega tópicos da comunidade VIP
  const communityTopics = (hasPremium && userId) ? await getCommunityTopics('default', selectedCategory, userId) : [];

  // Enrich courses with access info
  const purchasedCourseIds = new Set(coursePurchases.map((p: any) => p.course_id));
  const enrichedCourses = courses.map((c: any) => ({
    ...c,
    hasAccess: c.access_type === 'free' || hasPremium || (c.access_type === 'paid' && purchasedCourseIds.has(c.id))
  }));

  return {
    user: locals.user,
    courses: enrichedCourses,
    communityTopics,
    hasPremium,
    cheapestPlan,
    selectedCategory,
    settings
  };
};

export const actions: Actions = {
  createTopic: async ({ request, locals }) => {
    if (!locals.user) return fail(401, { error: 'Não autorizado' });

    // Check premium subscription
    const subscription = await queryOne(
      `SELECT id FROM premium_subscriptions WHERE user_id = ? AND status = 'active' AND (expires_at IS NULL OR expires_at > datetime('now'))`,
      [locals.user.id]
    );
    const hasPremium = !!subscription || locals.user.role === 'admin';
    if (!hasPremium) return fail(403, { error: 'Exclusivo para assinantes VIP' });

    const data = await request.formData();
    const title = (data.get('title') as string || '').trim();
    const content = (data.get('content') as string || '').trim();
    const category = (data.get('category') as string || 'Geral').trim();
    const isPinned = data.get('is_pinned') === 'on' && locals.user.role === 'admin';

    if (!title || title.length < 5) {
      return fail(400, { error: 'O título deve ter pelo menos 5 caracteres' });
    }

    if (!content || content.length < 10) {
      return fail(400, { error: 'O conteúdo deve ter pelo menos 10 caracteres' });
    }

    try {
      const topicId = await createCommunityTopic({
        userId: locals.user.id,
        title,
        content,
        category,
        isPinned
      });
      return { success: true, topicId };
    } catch (e) {
      console.error('Error creating community topic:', e);
      return fail(500, { error: 'Erro ao publicar tópico' });
    }
  },

  toggleLike: async ({ request, locals }) => {
    if (!locals.user) return fail(401, { error: 'Não autorizado' });

    const data = await request.formData();
    const topicId = parseInt(data.get('topic_id') as string);
    if (!topicId || isNaN(topicId)) return fail(400, { error: 'Tópico inválido' });

    try {
      const liked = await toggleCommunityLike(topicId, locals.user.id);
      return { success: true, liked, topicId };
    } catch (e) {
      console.error('Error toggling topic like:', e);
      return fail(500, { error: 'Erro ao curtir tópico' });
    }
  }
};
