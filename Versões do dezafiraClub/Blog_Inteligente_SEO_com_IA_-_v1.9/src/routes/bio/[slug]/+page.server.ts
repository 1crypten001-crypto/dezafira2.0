import type { PageServerLoad } from './$types';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params, url }) => {
	const slug = params.slug;
	const preview = url.searchParams.get('preview') === 'true';

	// Resolvendo URL do backend FastAPI (com fallback seguro de desenvolvimento)
	const backendUrl = process.env.BACKEND_API_URL || 'https://dezafiraadm-production.up.railway.app';
	const reqUrl = `${backendUrl.replace(/\/$/, '')}/bio/${slug}${preview ? '?preview=true' : ''}`;

	try {
		const res = await fetch(reqUrl);
		if (!res.ok) {
			throw error(res.status, 'Bio Site não encontrado');
		}
		const html = await res.text();
		return { html };
	} catch (e: any) {
		console.error('Erro ao buscar bio site no backend:', e);
		throw error(e.status || 500, e.message || 'Erro ao carregar o Bio Site');
	}
};
