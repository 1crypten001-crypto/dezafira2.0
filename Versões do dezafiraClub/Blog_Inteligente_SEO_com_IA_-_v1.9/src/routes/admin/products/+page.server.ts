import { fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { getAllProducts, deleteProduct, getProductById } from '$lib/server/database';
import fs from 'fs';
import path from 'path';

export const load: PageServerLoad = async () => {
    const products = await getAllProducts();
    return { products };
};

export const actions: Actions = {
    delete: async ({ request }) => {
        const data = await request.formData();
        const id = parseInt(data.get('id') as string);

        if (isNaN(id)) {
            return fail(400, { message: 'ID do produto inválido' });
        }

        try {
            const product = await getProductById(id);
            if (product && product.file_url) {
                try {
                    const filename = path.basename(product.file_url);
                    const pathsToDelete = [];
                    if (process.env.PRODUCT_UPLOADS_DIR) {
                        pathsToDelete.push(path.join(process.env.PRODUCT_UPLOADS_DIR, filename));
                    }
                    pathsToDelete.push(path.join(process.cwd(), 'static', 'uploads', 'products', filename));
                    
                    for (const p of pathsToDelete) {
                        if (fs.existsSync(p)) {
                            fs.unlinkSync(p);
                        }
                    }
                } catch (err) {
                    console.error('Error deleting product file from disk:', err);
                }
            }

            await deleteProduct(id);
            return { success: true };
        } catch (e) {
            console.error('Error deleting product:', e);
            return fail(500, { message: 'Erro ao deletar produto' });
        }
    }
};
