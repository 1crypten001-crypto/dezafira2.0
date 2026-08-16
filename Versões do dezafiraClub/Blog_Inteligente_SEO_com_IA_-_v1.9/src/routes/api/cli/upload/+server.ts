import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { uploadImage } from '$lib/server/cloudinary';
import { requireCLIToken } from '../auth';

async function hasValidImageSignature(file: File): Promise<boolean> {
  const bytes = new Uint8Array(await file.slice(0, 16).arrayBuffer());
  const ascii = (start: number, end: number) => String.fromCharCode(...bytes.slice(start, end));
  if (file.type === 'image/jpeg') return bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
  if (file.type === 'image/png') {
    return [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a].every((value, index) => bytes[index] === value);
  }
  if (file.type === 'image/gif') return ['GIF87a', 'GIF89a'].includes(ascii(0, 6));
  if (file.type === 'image/webp') return ascii(0, 4) === 'RIFF' && ascii(8, 12) === 'WEBP';
  if (file.type === 'image/avif') {
    return ascii(4, 8) === 'ftyp' && ['avif', 'avis'].includes(ascii(8, 12));
  }
  return false;
}

// POST /api/cli/upload — Faz upload de imagem para o Cloudinary e retorna a URL
// Content-Type: multipart/form-data
// Campo: "file" (arquivo de imagem)
// Campo opcional: "folder" (subpasta no Cloudinary, default: "blog")
export const POST: RequestHandler = async ({ request, getClientAddress }) => {
  const authError = await requireCLIToken(request, getClientAddress());
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
  if (!(await hasValidImageSignature(file))) {
    return json({ error: 'O conteúdo do arquivo não corresponde ao tipo de imagem informado.' }, { status: 400 });
  }

  // Max 20MB
  const maxBytes = 20 * 1024 * 1024;
  if (file.size === 0) {
    return json({ error: 'O arquivo está vazio.' }, { status: 400 });
  }
  if (file.size > maxBytes) {
    return json({ error: `Arquivo muito grande (${(file.size / 1024 / 1024).toFixed(1)}MB). Máximo: 20MB.` }, { status: 400 });
  }

  const requestedFolder = String(formData.get('folder') || 'blog').trim();
  const allowedFolders = new Set(['blog', 'blog/posts', 'blog/pinterest', 'blog/stories', 'blog/landings']);
  if (!allowedFolders.has(requestedFolder)) {
    return json({ error: 'Pasta inválida.', allowed_folders: [...allowedFolders] }, { status: 400 });
  }
  const folder = requestedFolder;

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
