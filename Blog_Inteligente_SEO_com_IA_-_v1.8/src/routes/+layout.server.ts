import { getSettings, getUserByUsername, isUserPremium, getActiveAdsByPlacement, getAllPosts, getPublishedWebStories } from '$lib/server/database';
import { validateSession } from '$lib/server/auth';
import { sanitizeAds } from '$lib/server/sanitize';
import { getTenantId } from '$lib/server/tenant';
import { getActivePaymentGateway, isAnyPaymentGatewayConfigured } from '$lib/server/payments';

export async function load({ cookies }) {
    const tenantId = getTenantId();
    const settings = await getSettings();
    const token = cookies.get('member_session');
    
    let user = null;
    let isPremium = false;

    if (token) {
        const username = await validateSession(token);
        if (username) {
            const dbUser = await getUserByUsername(username);
            if (dbUser) {
                user = {
                    id: dbUser.id,
                    username: dbUser.username,
                    role: dbUser.role || 'member',
                    createdAt: dbUser.created_at
                };
                isPremium = await isUserPremium(dbUser.id);
            }
        }
    }

    // Carregar ads do sidebar e posts populares para o layout e página de erro
    const sidebarAds = sanitizeAds(await getActiveAdsByPlacement('sidebar', tenantId));
    const popularPosts = await getAllPosts({ limit: 4 }, tenantId);

    // Instagram-style stories bar (only when admin enables the visual option)
    let webStories: Array<{
        id: number;
        title: string;
        slug: string;
        cover_image: string | null;
        poster_portrait: string | null;
    }> = [];
    if (settings.enable_web_stories_bar === '1') {
        try {
            webStories = await getPublishedWebStories(24);
        } catch {
            webStories = [];
        }
    }

    // Active payment gateway for all public/member checkout UIs (default asaas)
    let paymentGateway: 'asaas' | 'stripe' = 'asaas';
    let paymentConfigured = false;
    try {
        paymentGateway = await getActivePaymentGateway();
        paymentConfigured = await isAnyPaymentGatewayConfigured();
    } catch {
        paymentGateway = 'asaas';
        paymentConfigured = false;
    }

    // Display currency: Stripe uses configured currency; Asaas is always BRL
    const stripeCurrency = (settings.stripe_currency || 'brl').toUpperCase();
    const displayCurrency =
        paymentGateway === 'stripe' ? (stripeCurrency || 'USD') : 'BRL';

    return {
        settings,
        user,
        isPremium,
        sidebarAds,
        popularPosts,
        webStories,
        language: settings.site_language || 'pt',
        paymentGateway,
        paymentConfigured,
        displayCurrency
    };
}