import { redirect, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getCourseById, hasUserPurchasedCourse, createCoursePurchase, queryOne, getSettings } from '$lib/server/database';
import { createCustomer, createPayment, isAsaasConfigured } from '$lib/server/asaas';
import { createOneTimeCheckout, isStripeConfigured } from '$lib/server/stripe';
import {
  getActivePaymentGateway,
  requiresBrazilianProfileForCheckout
} from '$lib/server/payments';

export const GET: RequestHandler = async ({ params, locals, url }) => {
  const settings = await getSettings();
  if (settings.enable_member_login !== '1') throw error(403, 'Área de membros desativada');
  if (!locals.user) throw redirect(303, `/members/login?redirectTo=${encodeURIComponent(url.pathname)}`);

  const gateway = await getActivePaymentGateway();
  if ((await requiresBrazilianProfileForCheckout()) && (!locals.user.name || !locals.user.cpf)) {
    throw redirect(303, `/members/dashboard?redirectTo=${encodeURIComponent(url.pathname)}&error=update_profile`);
  }

  const courseId = parseInt(params.id);
  if (isNaN(courseId)) throw error(400, 'ID inválido');

  const course = await getCourseById(courseId);
  if (!course || !course.published) throw error(404, 'Curso não encontrado');
  if (course.access_type !== 'paid' || course.price_cents <= 0) throw redirect(303, `/members/area/${course.slug}`);

  const alreadyPurchased = await hasUserPurchasedCourse(locals.user.id, courseId);
  if (alreadyPurchased || locals.user.role === 'admin') throw redirect(303, `/members/area/${course.slug}`);

  // ── STRIPE ────────────────────────────────────────────────────────────
  if (gateway === 'stripe') {
    if (!(await isStripeConfigured())) throw error(500, 'Gateway Stripe não configurado');
    try {
      const checkout = await createOneTimeCheckout({
        productName: course.title,
        priceCents: course.price_cents,
        customerEmail: locals.user.username,
        userId: locals.user.id,
        kind: 'course',
        courseId: course.id,
        successPath: `/members/area/${course.slug}?checkout=success`,
        cancelPath: `/members/area/${course.slug}?checkout=cancelled`
      });

      await createCoursePurchase({
        userId: locals.user.id,
        courseId: course.id,
        stripeSessionId: checkout.sessionId,
        amountCents: course.price_cents,
        status: 'pending'
      });

      throw redirect(303, checkout.url);
    } catch (e: any) {
      if (e?.status === 303) throw e;
      console.error(e);
      throw error(500, 'Erro ao gerar checkout Stripe.');
    }
  }

  // ── ASAAS (default) ───────────────────────────────────────────────────
  if (!(await isAsaasConfigured())) throw error(500, 'Gateway de pagamentos não configurado');

  try {
    let customerId = '';
    const existingSub = await queryOne(
      'SELECT asaas_customer_id FROM premium_subscriptions WHERE user_id = ? AND asaas_customer_id IS NOT NULL LIMIT 1',
      [locals.user.id]
    );
    if (existingSub?.asaas_customer_id) {
      customerId = existingSub.asaas_customer_id;
    } else {
      const email = locals.user.username;
      const name = locals.user.name || email.split('@')[0] || 'Membro';
      const cpf = locals.user.cpf || undefined;
      const customer = await createCustomer(name, email, cpf);
      customerId = customer.id;
    }

    const paymentResult = await createPayment({
      productName: course.title,
      value: course.price_cents / 100,
      customerId
    });

    await createCoursePurchase({
      userId: locals.user.id,
      courseId: course.id,
      asaasPaymentId: paymentResult.id,
      amountCents: course.price_cents,
      status: 'pending'
    });

    throw redirect(303, paymentResult.invoiceUrl);
  } catch (e: any) {
    if (e?.status === 303) throw e;
    console.error(e);
    throw error(500, 'Erro ao gerar fatura. Tente novamente.');
  }
};
