import { fail, redirect } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { getProductCategories, createProductCategory, updateProductCategory, deleteProductCategory } from '$lib/server/database';
import { validateSession } from '$lib/server/auth';

export const load: PageServerLoad = async ({ cookies }) => {
    const token = cookies.get('admin_session');
    const username = await validateSession(token || '');
    if (!username) {
        throw redirect(303, '/admin/login');
    }

    const categories = await getProductCategories();
    return { categories };
};

export const actions: Actions = {
    create: async ({ request, cookies }) => {
        const token = cookies.get('admin_session');
        const username = await validateSession(token || '');
        if (!username) {
            return fail(403, { error: 'Acesso negado' });
        }

        const data = await request.formData();
        const name = data.get('name') as string;
        const description = data.get('description') as string;

        if (!name || name.trim().length < 2) {
            return fail(400, { error: 'O nome da categoria é obrigatório e deve ter pelo menos 2 caracteres.' });
        }

        try {
            await createProductCategory(name, description);
            return { success: true, message: 'Categoria de produto criada com sucesso!' };
        } catch (e: any) {
            console.error('Error creating product category:', e);
            if (e.message?.includes('UNIQUE')) {
                return fail(400, { error: 'Já existe uma categoria com este nome.' });
            }
            return fail(500, { error: 'Erro ao criar a categoria no banco de dados.' });
        }
    },

    update: async ({ request, cookies }) => {
        const token = cookies.get('admin_session');
        const username = await validateSession(token || '');
        if (!username) {
            return fail(403, { error: 'Acesso negado' });
        }

        const data = await request.formData();
        const id = parseInt(data.get('id') as string);
        const name = data.get('name') as string;
        const description = data.get('description') as string;

        if (isNaN(id) || !name || name.trim().length < 2) {
            return fail(400, { error: 'Dados inválidos para atualização da categoria.' });
        }

        try {
            await updateProductCategory(id, name, description);
            return { success: true, message: 'Categoria de produto atualizada com sucesso!' };
        } catch (e: any) {
            console.error('Error updating product category:', e);
            if (e.message?.includes('UNIQUE')) {
                return fail(400, { error: 'Já existe outra categoria com este nome.' });
            }
            return fail(500, { error: 'Erro ao atualizar a categoria.' });
        }
    },

    delete: async ({ request, cookies }) => {
        const token = cookies.get('admin_session');
        const username = await validateSession(token || '');
        if (!username) {
            return fail(403, { error: 'Acesso negado' });
        }

        const data = await request.formData();
        const id = parseInt(data.get('id') as string);

        if (isNaN(id)) {
            return fail(400, { error: 'ID da categoria inválido.' });
        }

        try {
            await deleteProductCategory(id);
            return { success: true, message: 'Categoria de produto excluída com sucesso!' };
        } catch (e) {
            console.error('Error deleting product category:', e);
            return fail(500, { error: 'Erro ao excluir a categoria.' });
        }
    }
};
