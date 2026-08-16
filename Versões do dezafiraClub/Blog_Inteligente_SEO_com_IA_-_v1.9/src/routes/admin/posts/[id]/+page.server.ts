import { error, redirect, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { getPostById, updatePost, generateUniqueSlug, slugExists, getAllCategories, getCategoriesByPostId, assignCategoriesToPost, getAllProducts, getProductsByPostId, assignProductsToPost } from '$lib/server/database';
import type { Post } from '$lib/server/database';
import { generateSafeFilename, validateFileUpload } from '$lib/server/security';
import { uploadImage } from '$lib/server/cloudinary';
import { env } from '$env/dynamic/private';
import fs from 'fs';
import path from 'path';


export const load: PageServerLoad = async ({ params }) => {
  const post = await getPostById(parseInt(params.id)) as Post | undefined;

  if (!post) {
    throw error(404, 'Post não encontrado');
  }

  const categories = await getAllCategories();
  const postCategories = await getCategoriesByPostId(post.id);
  const products = await getAllProducts();
  const postProducts = await getProductsByPostId(post.id);

  return { 
    post, 
    categories, 
    postCategoryIds: postCategories.map(c => c.id),
    products,
    postProductIds: postProducts.map(p => p.id)
  };
};

function sanitizeInput(input: string | null): string {
  if (!input) return '';
  return input.trim().slice(0, 10000);
}

function sanitizeContent(content: string | null): string {
  if (!content) return '';
  return content.slice(0, 100000);
}

export const actions: Actions = {
  default: async ({ request, params }) => {
    const postId = parseInt(params.id);
    const data = await request.formData();
    const title = sanitizeInput(data.get('title') as string);
    const content = sanitizeContent(data.get('content') as string);
    
    // LOG DE DEBUG PARA DIAGNÓSTICO
    console.log(`[DEBUG] Atualizando post ${postId} - Título: "${title.slice(0, 50)}...", Tamanho Conteúdo: ${content.length} bytes`);
    
    const excerpt = sanitizeInput(data.get('excerpt') as string);
    const published = data.get('published') === 'on' ? 1 : 0;
    const customSlug = sanitizeInput(data.get('slug') as string);
    let cover_image = sanitizeInput(data.get('cover_image') as string);
    const cover_image_file = data.get('cover_image_file');
    const pinterest_enabled = data.get('pinterest_enabled') === 'on' ? 1 : 0;
    const is_18_plus = data.get('is_18_plus') === 'on' ? 1 : 0;
    const youtube_video_url = sanitizeInput(data.get('youtube_video_url') as string);
    const tags = sanitizeInput(data.get('tags') as string);
    let pinterest_image = sanitizeInput(data.get('pinterest_image') as string);
    const pinterest_image_file = data.get('pinterest_image_file');
    const categoryIds = data.getAll('categories').map(id => parseInt(id as string)).filter(id => !isNaN(id));
    const productIds = data.getAll('products').map(id => parseInt(id as string)).filter(id => !isNaN(id));

    if (cover_image_file && cover_image_file instanceof File && cover_image_file.size > 0) {
      const validation = validateFileUpload(cover_image_file, {
        maxSize: 8 * 1024 * 1024,
        allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
      });

      if (!validation.valid) {
        return fail(400, {
          error: validation.error || 'Arquivo de imagem de capa inválido',
          post: {
            id: postId,
            title,
            slug: customSlug,
            content,
            excerpt,
            cover_image,
            published,
            pinterest_enabled,
            pinterest_image,
            youtube_video_url
          }
        });
      }

      try {
        const isCloudinaryConfigured = !!(env.CLOUDINARY_CLOUD_NAME && env.CLOUDINARY_API_KEY && env.CLOUDINARY_API_SECRET);
        if (isCloudinaryConfigured) {
          cover_image = await uploadImage(cover_image_file, 'blog/posts');
        } else {
          // Fallback: armazenamento local
          const buffer = Buffer.from(await cover_image_file.arrayBuffer());
          const filename = generateSafeFilename(cover_image_file.name);
          const uploadDir = path.join(process.cwd(), 'static', 'uploads', 'posts');
          if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
          }
          fs.writeFileSync(path.join(uploadDir, filename), buffer);
          cover_image = `/uploads/posts/${filename}`;
        }
      } catch (err) {
        console.error('Error uploading cover image:', err);
        return fail(500, {
          error: 'Erro ao fazer upload da imagem de capa',
          post: { id: postId, title, slug: customSlug, content, excerpt, cover_image, published, pinterest_enabled, pinterest_image, youtube_video_url }
        });
      }
    }

    if (pinterest_image_file && pinterest_image_file instanceof File && pinterest_image_file.size > 0) {
      const validation = validateFileUpload(pinterest_image_file, {
        maxSize: 8 * 1024 * 1024,
        allowedTypes: ['image/jpeg', 'image/png', 'image/webp']
      });

      if (!validation.valid) {
        return fail(400, {
          error: validation.error || 'Arquivo inválido',
          post: {
            id: postId,
            title,
            slug: customSlug,
            content,
            excerpt,
            cover_image,
            published,
            pinterest_enabled,
            pinterest_image,
            youtube_video_url
          }
        });
      }

      try {
        const isCloudinaryConfigured = !!(env.CLOUDINARY_CLOUD_NAME && env.CLOUDINARY_API_KEY && env.CLOUDINARY_API_SECRET);
        if (isCloudinaryConfigured) {
          pinterest_image = await uploadImage(pinterest_image_file, 'blog/pinterest');
        } else {
          // Fallback: armazenamento local
          const buffer = Buffer.from(await pinterest_image_file.arrayBuffer());
          const filename = generateSafeFilename(pinterest_image_file.name);
          const uploadDir = path.join(process.cwd(), 'static', 'uploads', 'pinterest');
          if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
          }
          fs.writeFileSync(path.join(uploadDir, filename), buffer);
          pinterest_image = `/uploads/pinterest/${filename}`;
        }
      } catch (err) {
        console.error('Error uploading Pinterest image:', err);
        return fail(500, {
          error: 'Erro ao fazer upload da imagem do Pinterest',
          post: { id: postId, title, slug: customSlug, content, excerpt, cover_image, published, pinterest_enabled, pinterest_image, youtube_video_url }
        });
      }

    }

    if (!title || !content) {
      return fail(400, {
        error: 'Título e conteúdo são obrigatórios',
        post: {
          id: postId,
          title,
          slug: customSlug,
          content,
          excerpt,
          cover_image,
          published,
          pinterest_enabled,
          pinterest_image,
          youtube_video_url
        }
      });
    }

    if (title.length < 3) {
      return fail(400, {
        error: 'O título deve ter pelo menos 3 caracteres',
        post: { id: postId, title, slug: customSlug, content, excerpt, cover_image, published, pinterest_enabled, pinterest_image, youtube_video_url }
      });
    }

    if (title.length > 200) {
      return fail(400, {
        error: 'O título deve ter no máximo 200 caracteres',
        post: { id: postId, title, slug: customSlug, content, excerpt, cover_image, published, pinterest_enabled, pinterest_image, youtube_video_url }
      });
    }

    let slug: string;
    if (customSlug) {
      if (await slugExists(customSlug, postId)) {
        return fail(400, {
          error: 'Este slug já está em uso por outro post',
          post: { id: postId, title, slug: customSlug, content, excerpt, cover_image, published, pinterest_enabled, pinterest_image, youtube_video_url }
        });
      }
      slug = await generateUniqueSlug(customSlug);
    } else {
      slug = await generateUniqueSlug(title);
    }

    try {
      await updatePost(postId, {
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

      // Atribuir categorias e produtos ao post
      await assignCategoriesToPost(postId, categoryIds);
      await assignProductsToPost(postId, productIds);

      throw redirect(303, '/admin/posts');
    } catch (err) {
      if ((err as { status?: number }).status === 303) {
        throw err;
      }
      return fail(500, {
        error: 'Erro ao atualizar post. Tente novamente.',
        post: { id: postId, title, slug, content, excerpt, published, pinterest_enabled, pinterest_image, youtube_video_url }
      });
    }

  }
};
