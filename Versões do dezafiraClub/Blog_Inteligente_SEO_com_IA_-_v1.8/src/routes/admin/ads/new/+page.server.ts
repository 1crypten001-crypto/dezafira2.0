import { redirect, fail } from '@sveltejs/kit';
import { createAd } from '$lib/server/database';
import { uploadImage } from '$lib/server/cloudinary';
import { env } from '$env/dynamic/private';
import fs from 'fs';
import path from 'path';

export const actions = {
    default: async ({ request }) => {
        const data = await request.formData();

        let image_url = (data.get('image_url') as string) || '';
        const image_file = data.get('image_file');

        if (image_file && image_file instanceof File && image_file.size > 0) {
            try {
                const isCloudinaryConfigured = !!(env.CLOUDINARY_CLOUD_NAME && env.CLOUDINARY_API_KEY && env.CLOUDINARY_API_SECRET);

                if (isCloudinaryConfigured) {
                    // Upload para Cloudinary
                    image_url = await uploadImage(image_file, 'blog/ads');
                } else {
                    // Fallback: armazenamento local
                    const buffer = Buffer.from(await image_file.arrayBuffer());
                    const extension = image_file.name.split('.').pop() || 'jpg';
                    const filename = `ad-${Date.now()}.${extension}`;

                    const uploadDir = path.join(process.cwd(), 'static', 'uploads', 'ads');
                    if (!fs.existsSync(uploadDir)) {
                        fs.mkdirSync(uploadDir, { recursive: true });
                    }

                    fs.writeFileSync(path.join(uploadDir, filename), buffer);
                    image_url = `/uploads/ads/${filename}`;
                }
            } catch (e) {
                console.error('Error uploading ad image:', e);
                return fail(500, { message: 'Erro ao fazer upload da imagem' });
            }
        }

        const styleStr = data.get('style') as string;
        let style = null;
        if (styleStr) {
            try {
                style = JSON.parse(styleStr);
            } catch {}
        }

        const ad = {
            name: data.get('name') as string,
            placement: data.get('placement') as string,
            type: data.get('type') as string,
            content: (data.get('content') as string) || '',
            image_url: image_url || null,
            link_url: (data.get('link_url') as string) || '',
            is_active: data.get('is_active') === 'on' ? 1 : 0,
            weight: parseInt(data.get('weight') as string) || 1,
            style,
            youtube_video_url: (data.get('youtube_video_url') as string) || null
        };

        if (!ad.name || !ad.placement || !ad.type) {
            return fail(400, { message: 'Nome, posicionamento e tipo são obrigatórios' });
        }

        if (ad.type === 'video' && !ad.youtube_video_url) {
            return fail(400, { message: 'A URL do vídeo do YouTube é obrigatória para anúncios do tipo Vídeo.' });
        }

        await createAd(ad);
        throw redirect(303, '/admin/ads');
    }
};
