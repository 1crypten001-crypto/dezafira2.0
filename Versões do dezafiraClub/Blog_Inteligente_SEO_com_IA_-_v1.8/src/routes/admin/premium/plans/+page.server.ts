import type { PageServerLoad } from './$types';
import { getAllPremiumPlans } from '$lib/server/database';

export const load: PageServerLoad = async () => {
    const plans = await getAllPremiumPlans();
    return { plans };
};