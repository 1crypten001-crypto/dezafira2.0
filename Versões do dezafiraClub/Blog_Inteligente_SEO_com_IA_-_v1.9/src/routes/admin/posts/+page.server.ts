import type { PageServerLoad } from './$types';
import { getAllPostsAdmin } from '$lib/server/database';
import { getTenantId } from '$lib/server/tenant';

export const load: PageServerLoad = async () => {
	const tenantId = getTenantId();
	const posts = await getAllPostsAdmin(tenantId);
	return { posts };
};
