import { getAllPostsAdmin, getAnalyticsSummary } from '$lib/server/database';
import { getTenantId } from '$lib/server/tenant';

export async function load() {
	const tenantId = getTenantId();
	const [posts, analytics] = await Promise.all([
		getAllPostsAdmin(tenantId),
		getAnalyticsSummary(tenantId)
	]);

	return {
		posts,
		analytics
	};
}
