import { redirect } from '@sveltejs/kit';
import { deleteAd } from '$lib/server/database';

export const actions = {
    default: async ({ params }) => {
        deleteAd(params.id);
        throw redirect(303, '/admin/ads');
    }
};
