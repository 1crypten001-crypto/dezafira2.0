import { error, redirect, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { 
  getCommunityTopicById, 
  getCommunityComments, 
  createCommunityComment, 
  deleteCommunityComment,
  deleteCommunityTopic,
  toggleCommunityLike,
  queryOne
} from '$lib/server/database';

export const load: PageServerLoad = async ({ params, locals }) => {
  if (!locals.user) throw redirect(303, '/members/login?redirectTo=/members/area');

  // Check premium subscription
  const subscription = await queryOne(
    `SELECT id FROM premium_subscriptions WHERE user_id = ? AND status = 'active' AND (expires_at IS NULL OR expires_at > datetime('now'))`,
    [locals.user.id]
  );
  const hasPremium = !!subscription || locals.user.role === 'admin';
  if (!hasPremium) throw redirect(303, '/members/area');

  const topicId = parseInt(params.id);
  if (isNaN(topicId)) throw error(404, 'Tópico inválido');

  const topic = await getCommunityTopicById(topicId, locals.user.id);
  if (!topic) throw error(404, 'Tópico não encontrado');

  const comments = await getCommunityComments(topicId);

  return {
    user: locals.user,
    topic,
    comments,
    hasPremium
  };
};

export const actions: Actions = {
  addComment: async ({ request, params, locals }) => {
    if (!locals.user) return fail(401, { error: 'Não autorizado' });

    const topicId = parseInt(params.id);
    const data = await request.formData();
    const content = (data.get('content') as string || '').trim();

    if (!content || content.length < 2) {
      return fail(400, { error: 'O comentário deve ter pelo menos 2 caracteres' });
    }

    try {
      await createCommunityComment({
        topicId,
        userId: locals.user.id,
        content
      });
      return { success: true };
    } catch (e) {
      console.error('Error adding comment:', e);
      return fail(500, { error: 'Erro ao enviar comentário' });
    }
  },

  deleteComment: async ({ request, locals }) => {
    if (!locals.user) return fail(401, { error: 'Não autorizado' });

    const data = await request.formData();
    const commentId = parseInt(data.get('comment_id') as string);
    const topicId = parseInt(data.get('topic_id') as string);

    if (!commentId || !topicId) return fail(400, { error: 'Dados inválidos' });

    // Check ownership or admin
    const comment = await queryOne(`SELECT user_id FROM community_comments WHERE id = ?`, [commentId]);
    if (!comment) return fail(404, { error: 'Comentário não encontrado' });
    if (comment.user_id !== locals.user.id && locals.user.role !== 'admin') {
      return fail(403, { error: 'Sem permissão' });
    }

    try {
      await deleteCommunityComment(commentId, topicId);
      return { success: true };
    } catch (e) {
      console.error('Error deleting comment:', e);
      return fail(500, { error: 'Erro ao excluir comentário' });
    }
  },

  deleteTopic: async ({ request, locals }) => {
    if (!locals.user) return fail(401, { error: 'Não autorizado' });

    const data = await request.formData();
    const topicId = parseInt(data.get('topic_id') as string);
    if (!topicId) return fail(400, { error: 'Tópico inválido' });

    const topic = await queryOne(`SELECT user_id FROM community_topics WHERE id = ?`, [topicId]);
    if (!topic) return fail(404, { error: 'Tópico não encontrado' });
    if (topic.user_id !== locals.user.id && locals.user.role !== 'admin') {
      return fail(403, { error: 'Sem permissão' });
    }

    try {
      await deleteCommunityTopic(topicId);
      throw redirect(303, '/members/area');
    } catch (e: any) {
      if (e?.status === 303) throw e;
      console.error('Error deleting topic:', e);
      return fail(500, { error: 'Erro ao excluir tópico' });
    }
  },

  toggleLike: async ({ params, locals }) => {
    if (!locals.user) return fail(401, { error: 'Não autorizado' });
    const topicId = parseInt(params.id);

    try {
      const liked = await toggleCommunityLike(topicId, locals.user.id);
      return { success: true, liked };
    } catch (e) {
      console.error('Error toggling like:', e);
      return fail(500, { error: 'Erro ao curtir' });
    }
  }
};
