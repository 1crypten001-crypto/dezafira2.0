import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { uploadImage } from '$lib/server/cloudinary';
import { requireCLIToken } from '../auth';

// POST /api/cli/upload — Faz upload de imagem para o Cloudinary e retorna a URL
// Content-Type: multipart/form-data
// Campo: "file" (arquivo de imagem)
// Campo opcional: "folder" (subpasta no Cloudinary, default: "blog")
export const POST: RequestHandler = async ({ request }) => {
  const authError = await requireCLIToken(request);
  if (authError) return authError;

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return json({ error: 'Esperado multipart/form-data com campo "file".' }, { status: 400 });
  }

  const file = formData.get('file');
  if (!file || !(file instanceof File)) {
    return json({ error: 'Campo "file" ausente ou inválido. Envie um arquivo de imagem.' }, { status: 400 });
  }

  // Validate file type
  const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/avif'];
  if (!allowed.includes(file.type)) {
    return json({
      error: `Tipo de arquivo não suportado: "${file.type}". Use: JPG, PNG, WEBP, GIF ou AVIF.`
    }, { status: 400 });
  }

  // Max 20MB
  const maxBytes = 20 * 1024 * 1024;
  if (file.size > maxBytes) {
    return json({ error: `Arquivo muito grande (${(file.size / 1024 / 1024).toFixed(1)}MB). Máximo: 20MB.` }, { status: 400 });
  }

  const folder = (formData.get('folder') as string) || 'blog';

  try {
    const url = await uploadImage(file, folder);
    return json({
      success: true,
      url,
      filename: file.name,
      size: file.size,
      type: file.type
    }, { status: 201 });
  } catch (err: any) {
    console.error('Cloudinary upload error:', err);
    return json({ error: 'Falha no upload para o Cloudinary. Verifique as credenciais no servidor.' }, { status: 500 });
  }
};
