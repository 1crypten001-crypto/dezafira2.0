import { redirect, error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getProductById, hasUserPurchasedProduct, queryOne, getSettings, findBundleForProduct, getBundleProducts } from '$lib/server/database';
import { getActivePaymentGateway, isAnyPaymentGatewayConfigured } from '$lib/server/payments';

export const load: PageServerLoad = async ({ params, locals, url }) => {
	const settings = await getSettings();
	if (settings.enable_member_login !== '1') {
		throw redirect(303, '/');
	}

	if (!locals.user) {
		const redirectTo = `/members/login?redirectTo=${encodeURIComponent(url.pathname + url.search)}`;
		throw redirect(303, redirectTo);
	}

	const productId = parseInt(params.productId);
	if (isNaN(productId)) {
		throw error(400, 'ID do produto inválido');
	}

	const product = await getProductById(productId);
	if (!product) {
		throw error(404, 'Produto não encontrado');
	}

	const gateway = await getActivePaymentGateway();
	const gatewayConfigured = await isAnyPaymentGatewayConfigured();

	// O upsell só deve aparecer se o usuário realmente comprou o produto principal.
	// Aceitamos status 'pending' também: o Asaas redireciona o comprador para cá
	// ANTES do webhook atualizar a compra — tratar pending como compra legítima
	// evita a tela "Compra não localizada" logo após o pagamento.
	const purchase = await queryOne(
		`SELECT id FROM product_purchases
		 WHERE user_id = ? AND product_id = ? AND status IN ('pending', 'completed', 'pending_delivery')
		 LIMIT 1`,
		[locals.user.id, product.id]
	);
	const purchased = !!purchase;
	const isAdmin = locals.user.role === 'admin';

	let upsell = null;
	let downsell = null;

	if (product.upsell_product_id) {
		const u = await getProductById(product.upsell_product_id);
		if (u && u.price_cents > 0) {
			const alreadyBought = await hasUserPurchasedProduct(locals.user.id, u.id);
			if (!alreadyBought && !(isAdmin)) {
				upsell = u;
			}
		}
	}

	if (product.downsell_product_id) {
		const d = await getProductById(product.downsell_product_id);
		if (d && d.price_cents > 0) {
			const alreadyBought = await hasUserPurchasedProduct(locals.user.id, d.id);
			if (!alreadyBought && !(isAdmin)) {
				downsell = d;
			}
		}
	}

	// Upsell do combo/pacote no pós-compra: se o produto comprado faz parte de
	// um bundle, oferece o pacote completo (com o preço original riscado).
	let bundleOffer: any = null;
	const b = await findBundleForProduct(product.id);
	if (b) {
		const alreadyBoughtBundle = await hasUserPurchasedProduct(locals.user.id, b.id);
		if (!alreadyBoughtBundle && !(isAdmin)) {
			const items = await getBundleProducts(b.id);
			const originalCents = items.reduce((s: number, it: any) => s + (it.price_cents || 0), 0);
			bundleOffer = { ...b, bundle_original_cents: originalCents, bundle_items_list: items };
		}
	}

	return {
		user: locals.user,
		product,
		purchased: purchased || isAdmin,
		upsell,
		downsell,
		bundleOffer,
		gateway,
		gatewayConfigured
	};
};
