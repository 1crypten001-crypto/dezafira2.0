import { redirect, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getProductById, hasUserPurchasedProduct, getSettings, queryOne, recordProductDownload } from '$lib/server/database';
import fs from 'fs';
import path from 'path';
import { Readable } from 'stream';

/**
 * GET /api/download/[productId]
 *
 * Endpoint seguro de download de produtos digitais.
 * - Verifica autenticação do usuário
 * - Verifica se o usuário tem acesso (compra avulsa completed, assinatura ativa, ou admin)
 * - Busca SEMPRE o file_url atual do produto (não armazenado na compra)
 *   → se o admin trocar o ZIP, o comprador sempre recebe a versão mais recente
 * - Nunca expõe o file_url diretamente no HTML
 * - Serve o arquivo diretamente via stream com o nome correto do produto,
 *   evitando que o usuário baixe um arquivo com nome de UUID.
 */
export const GET: RequestHandler = async ({ params, locals, url }) => {
    const settings = await getSettings();

    // 1. Login obrigatório
    if (!locals.user) {
        throw redirect(303, `/members/login?redirectTo=${encodeURIComponent(url.pathname)}`);
    }

    const productId = parseInt(params.productId);
    if (isNaN(productId)) {
        throw error(400, 'ID do produto inválido.');
    }

    // 2. Buscar produto com file_url ATUAL (sempre a versão mais recente)
    const product = await getProductById(productId);
    if (!product) {
        throw error(404, 'Produto não encontrado.');
    }

    if (!product.file_url && !product.external_link) {
        throw error(404, 'Este produto não possui arquivo para download.');
    }

    // 3. Verificar acesso — mesma lógica do +page.server.ts
    let hasAccess = false;

    if (locals.user.role === 'admin') {
        // Admin sempre tem acesso
        hasAccess = true;

    } else if (product.price_cents <= 0) {
        // Produto gratuito — acesso livre
        hasAccess = true;

    } else {
        // Produto pago: verificar compra avulsa (permanente, independe de assinatura)
        const purchased = await hasUserPurchasedProduct(locals.user.id, product.id);

        if (purchased) {
            hasAccess = true;
        } else if (settings.enable_member_login === '1' && product.is_premium_included && product.is_premium_included >= 1) {
            // Verificar assinatura premium ativa (para produtos do tipo premium)
            let subscription;
            if (product.is_premium_included === 1) {
                // Qualquer plano ativo
                subscription = await queryOne(
                    `SELECT id FROM premium_subscriptions
                     WHERE user_id = ?
                       AND status = 'active'
                       AND (expires_at IS NULL OR expires_at > datetime('now'))`,
                    [locals.user.id]
                );
            } else {
                // Apenas plano específico ativo
                subscription = await queryOne(
                    `SELECT id FROM premium_subscriptions
                     WHERE user_id = ?
                       AND plan_id = ?
                       AND status = 'active'
                       AND (expires_at IS NULL OR expires_at > datetime('now'))`,
                    [locals.user.id, product.is_premium_included]
                );
            }
            hasAccess = !!subscription;
        }
    }

    if (!hasAccess) {
        // Redireciona de volta para a página do produto com aviso
        throw redirect(303, `/product/${product.slug}?error=no_access`);
    }

    // 4. Servir o arquivo — SEMPRE o link atual do produto
    if (product.file_url) {
        if (product.file_url.startsWith('http')) {
            // Arquivo no Cloudinary (ou outro storage remoto):
            // Proxy seguro — o servidor baixa e repassa ao usuário.
            // A URL do Cloudinary nunca é exposta no browser nem no DevTools.
            await recordProductDownload(locals.user.id, product.id);

            // Obter o nome do arquivo a partir da URL do Cloudinary
            const urlPath = product.file_url.split('?')[0];
            let remoteFilename = path.basename(urlPath);
            
            try {
                remoteFilename = decodeURIComponent(remoteFilename);
                // Padrão novo: public_id sem extensão, extensão codificada como __ext (ex: Blog_v1.5_abc123__zip)
                // Converte: Blog_v1.5_abc123__zip → Blog_v1.5.zip
                const newPatternMatch = remoteFilename.match(/^(.+)_[a-zA-Z0-9]{6}__([a-zA-Z0-9]+)$/);
                if (newPatternMatch) {
                    remoteFilename = `${newPatternMatch[1]}.${newPatternMatch[2]}`;
                } else {
                    // Padrão antigo: sufixo aleatório de 6 chars antes da extensão (ex: Blog_v1.5_abc123.zip)
                    remoteFilename = remoteFilename.replace(/_[a-zA-Z0-9]{6}(\.[a-zA-Z0-9]+)$/i, '$1');
                }
            } catch (e) {
                // fallback silencioso
            }

            // Se não encontrou um nome de arquivo válido, usa o nome do produto como fallback
            if (!remoteFilename || !remoteFilename.includes('.')) {
                const cleanNameRemote = product.name
                    .trim()
                    .normalize('NFD')
                    .replace(/[\u0300-\u036f]/g, '')
                    .replace(/[^a-zA-Z0-9\s.-]/g, '')
                    .replace(/[\s_]+/g, '_')
                    .substring(0, 100);
                const remoteExt = urlPath.match(/\.([a-z0-9]+)$/i)?.[1] || 'zip';
                remoteFilename = `${cleanNameRemote}.${remoteExt}`;
            }

            // Log seguro: mostra domínio e tamanho da URL mas nunca o link completo
            const urlDomain = (() => { try { return new URL(product.file_url).hostname; } catch { return 'unknown'; } })();
            console.log(`[Secure Download] Serving product ${product.id} (${product.name}) from Cloudinary`);
            console.log(`[Secure Download] Storage domain: ${urlDomain} | URL length: ${product.file_url.length} | Filename: ${remoteFilename}`);
            
            let cloudRes: globalThis.Response;
            try {
                cloudRes = await fetch(product.file_url);
            } catch (fetchErr) {
                console.error(`[Secure Download] Network error fetching from ${urlDomain}:`, (fetchErr as Error).message);
                throw error(502, 'Não foi possível conectar ao servidor de armazenamento.');
            }
            
            if (!cloudRes.ok) {
                console.error(`[Secure Download] Storage returned HTTP ${cloudRes.status} for product ${product.id}`);
                throw error(502, 'O arquivo não está mais disponível no servidor de armazenamento. Contacte o administrador.');
            }
            
            const headers = new Headers();
            headers.set('Content-Disposition', `attachment; filename="${remoteFilename}"`);
            headers.set('Content-Type', 'application/octet-stream');
            headers.set('x-download-source', 'cloudinary');
            
            // Previne cache no navegador, Cloudflare ou CDN do servidor
            headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
            headers.set('Pragma', 'no-cache');
            headers.set('Expires', '0');

            const contentLength = cloudRes.headers.get('content-length');
            if (contentLength) headers.set('Content-Length', contentLength);

            return new Response(cloudRes.body, { status: 200, headers });
        }

        // Caminho do arquivo físico no servidor (com suporte a pasta persistente fora do repositório Git)
        const filename = path.basename(product.file_url);
        const persistentPath = process.env.PRODUCT_UPLOADS_DIR
            ? path.join(process.env.PRODUCT_UPLOADS_DIR, filename)
            : null;
        
        const relativePath = product.file_url.startsWith('/') ? product.file_url.substring(1) : product.file_url;
        const staticPath = path.join(process.cwd(), 'static', relativePath);

        let finalPath = '';
        if (persistentPath && fs.existsSync(persistentPath)) {
            finalPath = persistentPath;
        } else if (fs.existsSync(staticPath)) {
            finalPath = staticPath;
        }

        if (finalPath) {
            const nodeStream = fs.createReadStream(finalPath);
            const webStream = Readable.toWeb(nodeStream);
            
            // Obter o nome de arquivo original e remover o sufixo único de 6 chars
            let downloadFilename = path.basename(finalPath);
            // Remove sufixo _abc123 antes da extensão: Blog_v1.5_abc123.zip → Blog_v1.5.zip
            downloadFilename = downloadFilename.replace(/_[a-zA-Z0-9]{6}(\.[a-zA-Z0-9]+)$/i, '$1');

            // Se por algum motivo não for válido, usa o nome do produto como fallback
            if (!downloadFilename || !downloadFilename.includes('.')) {
                const cleanName = product.name
                    .trim()
                    .normalize('NFD')
                    .replace(/[\u0300-\u036f]/g, '') // Remove acentos
                    .replace(/[^a-zA-Z0-9\s.-]/g, '') // Remove caracteres especiais
                    .replace(/[\s_]+/g, '_') // Substitui espaços por underscores
                    .substring(0, 100);

                const ext = path.extname(finalPath) || '.zip';
                downloadFilename = cleanName.toLowerCase().endsWith(ext.toLowerCase()) 
                    ? cleanName 
                    : `${cleanName}${ext}`;
            }

            console.log(`[Secure Download] Serving product ${product.id} (${product.name}) from Local Disk`);
            const headers = new Headers();
            headers.set('Content-Disposition', `attachment; filename="${downloadFilename}"`);
            headers.set('Content-Type', 'application/octet-stream');
            headers.set('x-download-source', 'local-disk');
            
            // Previne cache no navegador, Cloudflare ou CDN do servidor
            headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
            headers.set('Pragma', 'no-cache');
            headers.set('Expires', '0');
            
            try {
                const stats = fs.statSync(finalPath);
                headers.set('Content-Length', stats.size.toString());
            } catch (e) {
                console.error('Error reading file stats:', e);
            }

            // Log do download no banco de dados
            await recordProductDownload(locals.user.id, product.id);

            return new Response(webStream as any, {
                status: 200,
                headers
            });
        }
    }

    if (product.external_link) {
        // Para links externos: redirect direto.
        // Se o link aponta para o player de curso do Adm (/curso/...),
        // anexa token de acesso assinado (IMPORT_API_KEY compartilhada).
        await recordProductDownload(locals.user.id, product.id);
        const { decorateCourseLink } = await import('$lib/server/courseAccess');
        const finalUrl = decorateCourseLink(product.external_link, String(locals.user.id));
        throw redirect(302, finalUrl || product.external_link);
    }

    throw error(500, 'Erro ao localizar arquivo do produto.');
};
