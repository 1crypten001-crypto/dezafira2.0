import type { PageServerLoad, Actions } from './$types';
import { fail } from '@sveltejs/kit';
import {
	getAllCategories,
	createCategory,
	updateCategory,
	deleteCategory
} from '$lib/server/database';
import { getTenantId } from '$lib/server/tenant';

export const load: PageServerLoad = async () => {
	const tenantId = getTenantId();
	const categories = await getAllCategories(tenantId);
	return { categories };
};

function generateSlug(name: string): string {
	return name
		.toLowerCase()
		.trim()
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
		.replace(/[^a-z0-9\s-]/g, '')
		.replace(/[\s_]+/g, '-')
		.replace(/-+/g, '-')
		.replace(/^-+|-+$/g, '');
}

export const actions: Actions = {
	create: async ({ request }) => {
		const tenantId = getTenantId();
		const data = await request.formData();
		const name = (data.get('name') as string)?.trim();

		if (!name || name.length < 2) {
			return fail(400, { error: 'O nome deve ter pelo menos 2 caracteres', action: 'create' });
		}

		const slug = generateSlug(name);

		try {
			await createCategory(name, slug, tenantId);
			return { success: true, message: 'Categoria criada com sucesso!' };
		} catch (err: any) {
			console.error('Erro ao criar categoria:', err);
			return fail(400, { 
				error: err.message?.includes('UNIQUE') ? 'Categoria já existe com este nome' : 'Erro ao criar categoria: ' + err.message, 
				action: 'create' 
			});
		}
	},

	update: async ({ request }) => {
		const tenantId = getTenantId();
		const data = await request.formData();
		const id = parseInt(data.get('id') as string);
		const name = (data.get('name') as string)?.trim();
		const pinterestEnabled = data.get('pinterest_enabled') === 'on';

		if (!name || name.length < 2) {
			return fail(400, { error: 'O nome deve ter pelo menos 2 caracteres', action: 'update' });
		}

		const slug = generateSlug(name);

		try {
			// Ajustado para passar os argumentos individualmente conforme definido no database.ts revisado
			await updateCategory(id, tenantId, name, slug, pinterestEnabled);
			return { success: true, message: 'Categoria atualizada!' };
		} catch (err: any) {
			console.error('Erro ao atualizar categoria:', err);
			return fail(400, { error: 'Erro ao atualizar categoria: ' + err.message, action: 'update' });
		}
	},

	delete: async ({ request }) => {
		const tenantId = getTenantId();
		const data = await request.formData();
		const id = parseInt(data.get('id') as string);

		try {
			await deleteCategory(id, tenantId);
			return { success: true, message: 'Categoria excluída!' };
		} catch (err: any) {
			console.error('Erro ao excluir categoria:', err);
			return fail(400, { error: 'Erro ao excluir categoria: ' + err.message, action: 'delete' });
		}
	}
};
