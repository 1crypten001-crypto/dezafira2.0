import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getSettings } from '$lib/server/database';
import { trackRecommendationEvent } from '$lib/server/interest-engine';

export const POST: RequestHandler = async ({ request, locals, cookies, url }) => {
    try {
        const settings = await getSettings();
        if (settings.enable_recommendations === '0') {
            return json({ success: true, message: 'Recommendations system is disabled' });
        }

        const { event, postId } = await request.json();
        if (!postId || !event) {
            return json({ success: false, error: 'Missing parameters' }, { status: 400 });
        }

        await trackRecommendationEvent(event, Number(postId), locals, cookies, url);

        return json({ success: true });
    } catch (e: any) {
        console.error('Error tracking recommendation event:', e);
        return json({ success: false, error: e.message || 'Internal server error' }, { status: 500 });
    }
};
