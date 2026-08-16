import { v2 as cloudinary } from 'cloudinary';
import { env } from '$env/dynamic/private';

cloudinary.config({
  cloud_name: env.CLOUDINARY_CLOUD_NAME,
  api_key: env.CLOUDINARY_API_KEY,
  api_secret: env.CLOUDINARY_API_SECRET,
  secure: true
});

/**
 * Faz upload de uma imagem para o Cloudinary.
 */
export async function uploadImage(file: File, folder: string = 'blog'): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);

  return new Promise((resolve, reject) => {
    const uploadStream = cloudinary.uploader.upload_stream(
      {
        folder,
        resource_type: 'image',
        use_filename: true,
        unique_filename: true,
      },
      (error, result) => {
        if (error || !result) {
          reject(error || new Error('Upload failed'));
          return;
        }
        resolve(result.secure_url);
      }
    );

    uploadStream.end(buffer);
  });
}

/**
 * Faz upload de arquivo raw (ZIP, PDF, RAR, etc.) para o Cloudinary.
 * Retorna a secure_url do arquivo.
 */
export async function uploadFile(file: File, folder: string = 'blog/products/files'): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);

  // Extrair extensão e nome original
  const ext = file.name.split('.').pop()?.toLowerCase() || '';
  const originalNameWithoutExt = file.name.substring(0, file.name.lastIndexOf('.'));
  
  // Sanitizar o nome do arquivo para ser um public_id válido no Cloudinary
  // IMPORTANTE: NÃO incluir extensão no public_id.
  // Cloudinary restringe acesso público a arquivos com extensões como .zip, .rar.
  // URLs sem extensão são públicas. O nome correto do arquivo é enviado via Content-Disposition no download.
  // O sufixo de extensão original é preservado no campo customizado abaixo para uso no download.
  const cleanName = originalNameWithoutExt
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9\s.-]/g, '')
    .replace(/[\s_]+/g, '_')
    .substring(0, 80);

  // Gerar sufixo único de 6 caracteres
  const uniqueHash = Math.random().toString(36).substring(2, 8);
  // public_id SEM extensão — garante URL pública no Cloudinary
  // Guardamos a extensão no nome do public_id separado por __ para recuperar no download
  const publicId = `${cleanName}_${uniqueHash}__${ext}`;

  return new Promise((resolve, reject) => {
    const uploadStream = cloudinary.uploader.upload_stream(
      {
        folder,
        resource_type: 'raw',
        public_id: publicId
        // SEM format — a URL fica sem extensão e é acessível publicamente
      },
      (error, result) => {
        if (error || !result) {
          reject(error || new Error('File upload failed'));
          return;
        }
        resolve(result.secure_url);
      }
    );

    uploadStream.end(buffer);
  });
}

/**
 * Deleta uma imagem do Cloudinary pelo public_id.
 */
export async function deleteImage(publicId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    cloudinary.uploader.destroy(publicId, (error) => {
      if (error) reject(error);
      else resolve();
    });
  });
}

/**
 * Deleta um arquivo raw (ZIP, PDF, etc.) do Cloudinary pelo public_id.
 */
export async function deleteFile(publicId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    cloudinary.uploader.destroy(publicId, { resource_type: 'raw' }, (error) => {
      if (error) reject(error);
      else resolve();
    });
  });
}

/**
 * Extrai o public_id de uma URL do Cloudinary.
 * Suporta imagens (image/upload) e raw files (raw/upload).
 */
export function getPublicIdFromUrl(url: string): string | null {
  if (!url) return null;
  // Raw files: .../raw/upload/v123/folder/filename.zip
  const rawMatch = url.match(/\/raw\/upload\/(?:v\d+\/)?(.+)$/);
  if (rawMatch) return rawMatch[1];
  // Images: .../image/upload/v123/folder/filename.jpg  (sem extensão no public_id)
  const imgMatch = url.match(/\/upload\/(.+)\.[a-z]+$/);
  return imgMatch ? imgMatch[1] : null;
}