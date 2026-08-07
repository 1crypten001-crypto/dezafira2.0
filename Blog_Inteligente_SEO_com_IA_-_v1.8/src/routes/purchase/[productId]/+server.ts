import { redirect, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
	getProductById,
	hasUserPurchasedProduct,
	createProductPurchase,
	queryOne,
	getSettings
} from '$lib/server/database';
import { createCustomer, createPayment, isAsaasConfigured } from '$lib/server/asaas';
import { createOneTimeCheckout, isStripeConfigured } from '$lib/server/stripe';
import {
	getActivePaymentGateway,
	requiresBrazilianProfileForCheckout
} from '$lib/server/payments';

export const GET: RequestHandler = async ({ params, locals, url }) => {
	const settings = await getSettings();
	const siteUrl = (settings.site_url || process.env.SITE_URL || '').replace(/\/$/, '');
	if (settings.enable_member_login !== '1') {
		throw error(403, 'A área de membros e compras está desativada no momento.');
	}

	if (!locals.user) {
		const redirectUrl = `/members/login?redirectTo=${encodeURIComponent(url.pathname + url.search)}`;
		throw redirect(303, redirectUrl);
	}

	const gateway = await getActivePaymentGateway();
	if ((await requiresBrazilianProfileForCheckout()) && (!locals.user.name || !locals.user.cpf)) {
		const redirectUrl = `/members/dashboard?redirectTo=${encodeURIComponent(url.pathname + url.search)}&error=update_profile`;
		throw redirect(303, redirectUrl);
	}

	const productId = parseInt(params.productId);
	if (isNaN(productId)) {
		throw error(400, 'ID do produto inválido');
	}

	const product = await getProductById(productId);
	if (!product) {
		throw error(404, 'Produto não encontrado');
	}

	if (product.price_cents <= 0) {
		throw redirect(303, '/');
	}

	const alreadyPurchased = await hasUserPurchasedProduct(locals.user.id, product.id);
	if (alreadyPurchased || locals.user.role === 'admin') {
		throw redirect(303, '/');
	}

	const buyerAccessId = url.searchParams.get('buyer_id') || null;
	const wantsExtra = url.searchParams.get('extra') === '1' || url.searchParams.get('extra') === 'true';

	let hasExtraService = 0;
	let extraServiceTitleSnapshot: string | null = null;
	let extraServicePriceCents = 0;
	let totalPriceCents = product.price_cents;

	if (wantsExtra && product.has_extra_service === 1 && product.extra_service_title) {
		hasExtraService = 1;
		extraServiceTitleSnapshot = product.extra_service_title;
		extraServicePriceCents = product.extra_service_price_cents || 0;
		totalPriceCents = product.price_cents + extraServicePriceCents;
	}

	const paymentItemName = hasExtraService === 1 && extraServiceTitleSnapshot
		? `${product.name} + ${extraServiceTitleSnapshot}`
		: product.name;

	// ── STRIPE ────────────────────────────────────────────────────────────
	if (gateway === 'stripe') {
		if (!(await isStripeConfigured())) {
			throw error(500, 'Gateway Stripe não configurado pelo administrador.');
		}
		try {
			const checkout = await createOneTimeCheckout({
				productName: paymentItemName,
				priceCents: totalPriceCents,
				customerEmail: locals.user.username,
				userId: locals.user.id,
				kind: 'product',
				productId: product.id,
				buyerAccessId,
				successPath: `/product/${product.slug}?checkout=success`,
				cancelPath: `/product/${product.slug}?checkout=cancelled`
			});

			await createProductPurchase({
				userId: locals.user.id,
				productId: product.id,
				productNameSnapshot: product.name,
				priceCents: totalPriceCents,
				stripeSessionId: checkout.sessionId,
				status: 'pending',
				buyerAccessId: buyerAccessId || null,
				hasExtraService,
				extraServiceTitleSnapshot,
				extraServicePriceCents
			});

			throw redirect(303, checkout.url);
		} catch (e) {
			if (e && (e as any).status === 303) throw e;
			console.error('Stripe product purchase error:', e);
			throw error(500, 'Erro ao gerar checkout Stripe. Tente novamente mais tarde.');
		}
	}

	// ── ASAAS (default) ───────────────────────────────────────────────────
	if (!(await isAsaasConfigured())) {
		throw error(500, 'Gateway de pagamentos (Asaas) não configurado pelo administrador.');
	}

	try {
		let customerId = '';
		const existingSub = await queryOne(
			'SELECT asaas_customer_id FROM premium_subscriptions WHERE user_id = ? AND asaas_customer_id IS NOT NULL LIMIT 1',
			[locals.user.id]
		);

		if (existingSub && existingSub.asaas_customer_id) {
			customerId = existingSub.asaas_customer_id;
		} else {
			const email = locals.user.username;
			const name = locals.user.name || email.split('@')[0] || 'Leitor';
			const cpf = locals.user.cpf || undefined;
			const customer = await createCustomer(name, email, cpf);
			customerId = customer.id;
		}

		const method = url.searchParams.get('method') || 'pix';
		const billingType = method === 'credit_card' ? 'CREDIT_CARD' : 'PIX';

		const amount = totalPriceCents / 100;
		const successUrl = siteUrl
			? `${siteUrl}/checkout/obrigado/${product.id}?method=${encodeURIComponent(method)}`
			: undefined;
		const paymentResult = await createPayment({
			productName: paymentItemName,
			value: amount,
			customerId,
			billingType,
			successUrl
		});

		await createProductPurchase({
			userId: locals.user.id,
			productId: product.id,
			productNameSnapshot: product.name,
			priceCents: totalPriceCents,
			asaasPaymentId: paymentResult.id,
			status: 'pending',
			buyerAccessId: buyerAccessId || null,
			hasExtraService,
			extraServiceTitleSnapshot,
			extraServicePriceCents
		});

		throw redirect(303, paymentResult.invoiceUrl);
	} catch (e) {
		if (e && (e as any).status === 303) {
			throw e;
		}
		console.error('Error generating product purchase payment:', e);
		throw error(500, 'Erro ao gerar fatura para pagamento. Tente novamente mais tarde.');
	}
};
