import type { PageServerLoad } from './$types';
import { getAllProducts, getProductCategories, getSettings } from '$lib/server/database';

export const load: PageServerLoad = async ({ locals }) => {
    const [products, categories, settings] = await Promise.all([
        getAllProducts(),
        getProductCategories(),
        getSettings(),
    ]);

    // Safety: remove file_url and external_link from public product listing
    const safeProducts = products.map((product) => ({
        ...product,
        file_url: undefined,
        external_link: undefined,
    }));

    return {
        products: safeProducts,
        // Full catalog from product_categories (not only categories already used by products)
        categories,
        settings,
        user: locals.user ?? null,
    };
};
