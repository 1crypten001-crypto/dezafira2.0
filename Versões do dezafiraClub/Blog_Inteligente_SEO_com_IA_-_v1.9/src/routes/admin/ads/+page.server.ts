import { getAllAds } from '$lib/server/database';
import { getTenantId } from '$lib/server/tenant';

export async function load() {
	const tenantId = getTenantId();
	const ads = await getAllAds(tenantId);
	return { ads };
}
