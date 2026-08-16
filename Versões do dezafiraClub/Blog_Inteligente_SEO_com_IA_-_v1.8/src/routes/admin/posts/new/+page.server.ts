import { redirect, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { createPost, generateUniqueSlug, getAllCategories, assignCategoriesToPost, getAllProducts, assignProductsToPost } from '$lib/server/database';
import { uploadImage } from '$lib/server/cloudinary';

export const load: PageServerLoad = async () => {
    const categories = await getAllCategories();
    const products = await getAllProducts();
    return { categories, products };
};

function sanitizeInput(input: string | null): string {
    if (!input) return '';
    return input.trim().slice(0, 10000);
}

function sanitizeContent(content: string | null): string {
    if (!content) return '';
    return content.slice(0, 100000);
}

function failWithFields(
    status: number,
    error: string,
    fields: Record<string, unknown>
) {
    return fail(status, { error, ...fields });
}

export const actions: Actions = {
    default: async ({ request }) => {
        const data = await request.formData();
        const title = sanitizeInput(data.get('title') as string);
        const content = sanitizeContent(data.get('content') as string);
        
        // LOG DE DEBUG PARA DIAGNÓSTICO
        console.log(`[DEBUG] Recebendo post - Título: "${title.slice(0, 50)}...", Tamanho Conteúdo: ${content.length} bytes`);
        
        const excerpt = sanitizeInput(data.get('excerpt') as string);
        const published = data.get('published') === 'on' ? 1 : 0;
        const customSlug = sanitizeInput(data.get('slug') as string);
        let cover_image = sanitizeInput(data.get('cover_image') as string);
        const cover_image_file = data.get('cover_image_file');
        const pinterest_enabled = data.get('pinterest_enabled') === 'on' ? 1 : 0;
        const pinterest_image = sanitizeInput(data.get('pinterest_image') as string);
        const is_18_plus = data.get('is_18_plus') === 'on' ? 1 : 0;
        const youtube_video_url = sanitizeInput(data.get('youtube_video_url') as string);
        const tags = sanitizeInput(data.get('tags') as string);
        const categoryIds = data.getAll('categories').map(id => parseInt(id as string)).filter(id => !isNaN(id));
        const productIds = data.getAll('products').map(id => parseInt(id as string)).filter(id => !isNaN(id));

        const fieldSnapshot = {
            title,
            content,
            excerpt,
            cover_image,
            published: published === 1,
            pinterest_enabled: pinterest_enabled === 1,
            pinterest_image,
            youtube_video_url,
            tags,
            is_18_plus: is_18_plus === 1,
            slug: customSlug
        };

        if (cover_image_file && cover_image_file instanceof File && cover_image_file.size > 0) {
            if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(cover_image_file.type)) {
                return failWithFields(400, 'INVALID_FILE', fieldSnapshot);
            }
            if (cover_image_file.size > 5 * 1024 * 1024) {
                return failWithFields(400, 'FILE_TOO_LARGE', fieldSnapshot);
            }
            try {
                cover_image = await uploadImage(cover_image_file, 'blog/posts');
                fieldSnapshot.cover_image = cover_image;
            } catch {
                return failWithFields(500, 'UPLOAD_FAILED', fieldSnapshot);
            }
        }

        if (!title || !content) {
            return failWithFields(400, 'TITLE_CONTENT_REQUIRED', fieldSnapshot);
        }

        if (title.length < 3) {
            return failWithFields(400, 'TITLE_TOO_SHORT', fieldSnapshot);
        }

        if (title.length > 200) {
            return failWithFields(400, 'TITLE_TOO_LONG', fieldSnapshot);
        }

        const slug = customSlug
            ? await generateUniqueSlug(customSlug)
            : await generateUniqueSlug(title);

        try {
            const result = await createPost({
                title,
                slug,
                content,
                excerpt,
                cover_image,
                published,
                pinterest_enabled,
                pinterest_image,
                is_18_plus,
                youtube_video_url,
                tags
            });


            if (result.lastInsertRowid) {
                const postId = Number(result.lastInsertRowid);
                if (categoryIds.length > 0) {
                    await assignCategoriesToPost(postId, categoryIds);
                }
                if (productIds.length > 0) {
                    await assignProductsToPost(postId, productIds);
                }
            }

            throw redirect(303, '/admin/posts');
        } catch (e: any) {
            if (e?.status === 303) throw e;
            return failWithFields(500, 'CREATE_FAILED', fieldSnapshot);
        }
    }
};
