import { redirect, isRedirect, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import {
  getAllPremiumPlans,
  getUserSubscription,
  isUserPremium,
  getPremiumPlanById,
  queryOne,
  createSubscription as createDbSubscription,
  getSettings
} from '$lib/server/database';
import { isAsaasConfigured, createCustomer, createSubscription as createAsaasSubscription } from '$lib/server/asaas';
import { createSubscriptionCheckout, isStripeConfigured } from '$lib/server/stripe';
import {
  getActivePaymentGateway,
  isAnyPaymentGatewayConfigured,
  requiresBrazilianProfileForCheckout
} from '$lib/server/payments';

export const load: PageServerLoad = async ({ locals }) => {
  const plans = await getAllPremiumPlans();
  const settings = await getSettings();
  const paymentGateway = await getActivePaymentGateway();

  let userSubscription = null;
  let userIsPremium = false;

  if (locals.user) {
    userSubscription = await getUserSubscription(locals.user.id);
    userIsPremium = await isUserPremium(locals.user.id);
  }

  return {
    plans,
    settings,
    userSubscription,
    userIsPremium,
    paymentGateway,
    paymentConfigured: await isAnyPaymentGatewayConfigured(),
    // keep legacy flag for templates that still check it
    asaasConfigured: paymentGateway === 'asaas' ? await isAsaasConfigured() : await isStripeConfigured()
  };
};

export const actions: Actions = {
  subscribe: async ({ request, locals }) => {
    if (!locals.user) {
      throw redirect(303, '/members/login');
    }

    const data = await request.formData();
    const planId = data.get('plan_id') as string;

    if (!planId) {
      return fail(400, { error: 'PLAN_REQUIRED' });
    }

    const gateway = await getActivePaymentGateway();
    const needCpf = await requiresBrazilianProfileForCheckout();

    // CPF/name only required for Asaas (Brazilian gateway)
    if (needCpf && (!locals.user.name || !locals.user.cpf)) {
      throw redirect(
        303,
        `/members/dashboard?redirectTo=${encodeURIComponent(`/premium?plan_id=${planId}&auto=1`)}&error=update_profile`
      );
    }

    // Stripe still benefits from a display name when available, but email is enough
    if (gateway === 'stripe' && !locals.user.username) {
      return fail(400, { error: 'EMAIL_REQUIRED' });
    }

    const plan = await getPremiumPlanById(parseInt(planId));
    if (!plan) {
      return fail(400, { error: 'PLAN_NOT_FOUND' });
    }

    // ── STRIPE ────────────────────────────────────────────────────────────
    if (gateway === 'stripe') {
      if (!(await isStripeConfigured())) {
        return fail(500, { error: 'STRIPE_NOT_CONFIGURED' });
      }

      try {
        const checkout = await createSubscriptionCheckout({
          planName: plan.name,
          priceCents: plan.price_cents,
          intervalDays: plan.interval_days || 30,
          customerEmail: locals.user.username,
          userId: locals.user.id,
          planId: plan.id
        });

        // Local pending row — real Stripe subscription id is set by webhook after payment.
        // Store session id as cs_pending:… so we can correlate before activation.
        await createDbSubscription({
          user_id: locals.user.id,
          plan_id: plan.id,
          status: 'pending',
          started_at: new Date().toISOString(),
          expires_at: new Date(
            Date.now() + (plan.interval_days || 30) * 24 * 60 * 60 * 1000
          ).toISOString(),
          stripe_subscription_id: `cs_pending:${checkout.sessionId}`
        });

        throw redirect(303, checkout.url);
      } catch (e) {
        if (isRedirect(e)) throw e;
        console.error('Stripe Checkout Error:', e);
        return fail(500, { error: 'STRIPE_CHECKOUT_FAIL' });
      }
    }

    // ── ASAAS (default — production path) ─────────────────────────────────
    if (!(await isAsaasConfigured())) {
      return fail(500, { error: 'ASAAS_NOT_CONFIGURED' });
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
        const name = locals.user.name || email.split('@')[0] || 'Assinante';
        const cpf = locals.user.cpf || undefined;
        const customer = await createCustomer(name, email, cpf);
        customerId = customer.id;
      }

      const method = (data.get('method') as string) || 'pix';
      const billingType = method === 'credit_card' ? 'CREDIT_CARD' : 'PIX';

      const asaasSub = await createAsaasSubscription({
        planName: plan.name,
        value: plan.price_cents / 100,
        customerId,
        cycleDays: plan.interval_days || 30,
        billingType
      });

      await createDbSubscription({
        user_id: locals.user.id,
        plan_id: plan.id,
        status: 'pending',
        started_at: new Date().toISOString(),
        expires_at: new Date(
          Date.now() + (plan.interval_days || 30) * 24 * 60 * 60 * 1000
        ).toISOString(),
        asaas_subscription_id: asaasSub.id,
        asaas_customer_id: customerId
      });

      if (asaasSub.invoiceUrl) {
        throw redirect(303, asaasSub.invoiceUrl);
      }

      return fail(500, { error: 'ASAAS_CHECKOUT_URL' });
    } catch (e) {
      if (isRedirect(e)) throw e;
      console.error('Asaas Checkout Error:', e);
      return fail(500, { error: 'ASAAS_CHECKOUT_FAIL' });
    }
  }
};
