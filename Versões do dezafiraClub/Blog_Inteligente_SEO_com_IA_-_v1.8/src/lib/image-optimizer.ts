/**
 * Utilitário para otimizar URLs de imagem (especialmente Cloudinary) dinamicamente.
 */
export function optimizeImageUrl(url: string | null | undefined, width?: number, quality: string = 'auto'): string {
  if (!url) return '';
  
  // Se for uma URL do Cloudinary
  if (url.includes('res.cloudinary.com/')) {
    // Evita aplicar transformações duplicadas se a URL já tiver parâmetros
    const uploadIndex = url.indexOf('/image/upload/');
    if (uploadIndex !== -1) {
      const prefix = url.substring(0, uploadIndex + 14); // inclui "/image/upload/"
      const suffix = url.substring(uploadIndex + 14);
      
      // Se a URL já possui transformações comuns (ex: q_auto), retorna a original
      if (suffix.match(/q_[a-z0-9]+/i)) {
        return url;
      }
      
      const transformations = [
        `q_${quality}` // qualidade automática
      ];
      
      if (width) {
        transformations.push(`w_${width}`);
        transformations.push('c_limit'); // limita o tamanho sem esticar imagem menor
      }
      
      return `${prefix}${transformations.join(',')}/${suffix}`;
    }
  }
  
  return url;
}
