import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { validateSession } from '$lib/server/auth';
import { uploadImage } from '$lib/server/cloudinary';
import fs from 'fs';
import path from 'path';

export const POST: RequestHandler = async ({ request, cookies }) => {
  // 1. Validar sessão admin
  const token = cookies.get('admin_session');
  const username = await validateSession(token || '');
  if (!username) {
    throw error(401, 'Não autorizado');
  }

  // 2. Processar o arquivo
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file || file.size === 0) {
      throw error(400, 'Nenhum arquivo enviado');
    }

    // Optional folder (whitelist) — defaults to newsletter for backward compatibility
    const rawFolder = String(formData.get('folder') || 'blog/newsletter').trim();
    const allowedFolders = new Set([
      'blog/newsletter',
      'blog/stories',
      'blog/posts',
      'blog/ads',
      'blog/products'
    ]);
    const folder = allowedFolders.has(rawFolder) ? rawFolder : 'blog/newsletter';
    const localSubdir = folder.split('/').pop() || 'uploads';

    // Tentar fazer upload para o Cloudinary
    try {
      const url = await uploadImage(file, folder);
      return json({ url, folder });
    } catch (cloudinaryErr) {
      console.warn('[UPLOAD API] Cloudinary failed or not configured, falling back to local storage:', cloudinaryErr);
      
      // Fallback local
      const arrayBuffer = await file.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      const ext = file.name.split('.').pop() || 'jpg';
      const filename = `${Date.now()}_${Math.random().toString(36).substring(2, 8)}.${ext}`;
      
      const uploadDir = path.join(process.cwd(), 'static', 'uploads', localSubdir);
      if (!fs.existsSync(uploadDir)) {
        fs.mkdirSync(uploadDir, { recursive: true });
      }

      fs.writeFileSync(path.join(uploadDir, filename), buffer);
      
      return json({ url: `/uploads/${localSubdir}/${filename}`, folder });
    }
  } catch (err: any) {
    console.error('[UPLOAD API] Error processing upload:', err);
    throw error(500, err?.message || 'Falha ao processar upload');
  }
};
