import { error, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { 
    getProductBySlug, 
    hasUserPurchasedProduct, 
    getProductPurchaseForUser, 
    getSettings, 
    queryOne, 
    getRelatedProducts,
    getProductReviews,
    getProductReviewSummary,
    hasUserReviewedProduct,
    createProductReview
} from '$lib/server/database';

export const load: PageServerLoad = async ({ params, locals }) => {
    const product = await getProductBySlug(params.slug);
    if (!product) {
        throw error(404, 'Produto não encontrado');
    }

    const settings = await getSettings();

    let hasPurchased = false;
    let isPremiumAccess = false;
    let purchaseStatus: string | null = null;
    let hasReviewed = false;

    if (product.price_cents <= 0) {
        // Produto gratuito — acesso livre
        hasPurchased = true;
    } else if (locals.user) {
        if (locals.user.role === 'admin') {
            hasPurchased = true;
        } else {
            // Compra avulsa (permanente) — inclui pending_delivery para produtos manuais
            hasPurchased = await hasUserPurchasedProduct(locals.user.id, product.id);

            // Busca status detalhado da compra (para mostrar estado pending_delivery ao comprador)
            if (hasPurchased) {
                const purchaseRecord = await getProductPurchaseForUser(locals.user.id, product.id);
                purchaseStatus = purchaseRecord?.status || null;
            }

            // Se não comprou avulso, verifica assinatura premium ativa APENAS se o produto estiver incluso no Premium
            if (!hasPurchased && settings.enable_member_login === '1' && product.is_premium_included && product.is_premium_included >= 1) {
                let subscription;
                if (product.is_premium_included === 1) {
                    // Incluso em qualquer plano ativo
                    subscription = await queryOne(
                        `SELECT id FROM premium_subscriptions
                         WHERE user_id = ?
                           AND status = 'active'
                           AND (expires_at IS NULL OR expires_at > datetime('now'))`,
                        [locals.user.id]
                    );
                } else {
                    // Incluso apenas no plano correspondente ativo
                    subscription = await queryOne(
                        `SELECT id FROM premium_subscriptions
                         WHERE user_id = ?
                           AND plan_id = ?
                           AND status = 'active'
                           AND (expires_at IS NULL OR expires_at > datetime('now'))`,
                        [locals.user.id, product.is_premium_included]
                    );
                }
                if (subscription) {
                    hasPurchased = true;
                    isPremiumAccess = true;
                }
            }
        }
    }

    // Carregar dados de avaliações
    const [reviews, reviewSummary] = await Promise.all([
        getProductReviews(product.id),
        getProductReviewSummary(product.id)
    ]);

    // Verificar se o usuário atual logado já avaliou este produto
    if (locals.user) {
        hasReviewed = await hasUserReviewedProduct(locals.user.id, product.id);
    }

    // Segurança: nunca expõe file_url nem external_link no HTML para quem não comprou.
    // Para produtos com entrega manual (resource_type='manual'), external_link é o link
    // privado do Drive/GitHub — NUNCA exposto ao comprador, mesmo após a compra.
    const isManual = product.resource_type === 'manual';
    let safeExternalLink = (hasPurchased && !isManual) ? product.external_link : undefined;
    // Player de curso do Adm: anexa token de acesso assinado para o comprador.
    // Produtos grátis expõem o link até sem login (user_ref fixo 'free' — o
    // token assina o acesso, e o curso é de acesso livre por definição).
    if (safeExternalLink) {
        const { decorateCourseLink } = await import('$lib/server/courseAccess');
        const userRef = locals.user ? String(locals.user.id) : 'free';
        safeExternalLink = decorateCourseLink(safeExternalLink, userRef) || undefined;
    }
    const safeProduct = {
        ...product,
        file_url:      hasPurchased ? product.file_url : undefined,
        // external_link: apenas para tipos 'link' (não para 'manual' — esse é link privado do admin)
        external_link: safeExternalLink,
    };

    const relatedProducts = await getRelatedProducts(product.id, product.category_id || null, 3);
    const safeRelatedProducts = relatedProducts.map((p) => ({
        ...p,
        file_url: undefined,
        external_link: undefined,
    }));

    return {
        product: safeProduct,
        hasPurchased,
        isPremiumAccess,
        purchaseStatus,
        hasReviewed,
        reviews,
        reviewSummary,
        user: locals.user ?? null,
        settings,
        relatedProducts: safeRelatedProducts,
    };
};

export const actions: Actions = {
    addReview: async ({ request, locals, params }) => {
        // 1. Validar autenticação
        if (!locals.user) {
            return fail(401, { message: 'Você precisa estar logado para avaliar.' });
        }

        const product = await getProductBySlug(params.slug);
        if (!product) {
            return fail(404, { message: 'Produto não encontrado.' });
        }

        const settings = await getSettings();

        // 2. Validar se o usuário tem permissão para avaliar (se comprou ou se é grátis ou se é admin)
        let canReview = false;
        if (product.price_cents <= 0) {
            canReview = true;
        } else if (locals.user.role === 'admin') {
            canReview = true;
        } else {
            // Verifica se comprou
            canReview = await hasUserPurchasedProduct(locals.user.id, product.id);
            
            // Se não comprou avulso, verifica assinatura ativa
            if (!canReview && settings.enable_member_login === '1') {
                const subscription = await queryOne(
                    `SELECT id FROM premium_subscriptions
                     WHERE user_id = ? AND status = 'active'
                     AND (expires_at IS NULL OR expires_at > datetime('now'))`,
                    [locals.user.id]
                );
                if (subscription) canReview = true;
            }
        }

        if (!canReview) {
            return fail(403, { message: 'Apenas compradores deste produto podem deixar uma avaliação.' });
        }

        // 3. Validar se já avaliou
        const alreadyReviewed = await hasUserReviewedProduct(locals.user.id, product.id);
        if (alreadyReviewed) {
            return fail(400, { message: 'Você já deixou uma avaliação para este produto.' });
        }

        const data = await request.formData();
        const rating = parseInt(data.get('rating') as string);
        const comment = data.get('comment') as string;

        // 4. Validar nota
        if (isNaN(rating) || rating < 1 || rating > 5) {
            return fail(400, { message: 'A nota deve ser entre 1 e 5 estrelas.' });
        }

        try {
            await createProductReview({
                productId: product.id,
                userId: locals.user.id,
                rating,
                comment: comment ? comment.trim() : null
            });
        } catch (e) {
            console.error('Error creating product review:', e);
            return fail(500, { message: 'Erro interno ao salvar sua avaliação.' });
        }

        return { success: true, message: 'Avaliação enviada com sucesso! Obrigado por avaliar.' };
    }
};
