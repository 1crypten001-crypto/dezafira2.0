import { fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { 
  getCommunityTopics, 
  getCommunityStats, 
  deleteCommunityTopic, 
  togglePinCommunityTopic 
} from '$lib/server/database';

export const load: PageServerLoad = async () => {
  const topics = await getCommunityTopics('default');
  const stats = await getCommunityStats();

  return {
    topics,
    stats
  };
};

export const actions: Actions = {
  togglePin: async ({ request }) => {
    const data = await request.formData();
    const topicId = parseInt(data.get('topic_id') as string);
    const isPinned = data.get('is_pinned') === 'true';

    if (!topicId) return fail(400, { error: 'ID do tópico inválido' });

    try {
      await togglePinCommunityTopic(topicId, !isPinned);
      return { success: true };
    } catch (e) {
      console.error('Error toggling pin:', e);
      return fail(500, { error: 'Erro ao fixar tópico' });
    }
  },

  deleteTopic: async ({ request }) => {
    const data = await request.formData();
    const topicId = parseInt(data.get('topic_id') as string);

    if (!topicId) return fail(400, { error: 'ID do tópico inválido' });

    try {
      await deleteCommunityTopic(topicId);
      return { success: true };
    } catch (e) {
      console.error('Error deleting topic:', e);
      return fail(500, { error: 'Erro ao excluir tópico' });
    }
  }
};
