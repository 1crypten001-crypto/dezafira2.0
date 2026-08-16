import { fail, redirect, isRedirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { queryOne, query, updateSubscriptionByAsaasId, run } from '$lib/server/database';
import { cancelSubscription, isAsaasConfigured } from '$lib/server/asaas';
import { cancelStripeSubscription } from '$lib/server/stripe';
import {
  getActivePaymentGateway,
  requiresBrazilianProfileForCheckout
} from '$lib/server/payments';

export const load: PageServerLoad = async ({ locals }) => {
  if (!locals.user) {
    throw redirect(303, '/members/login');
  }

  // Get latest subscription and plan info
  const subscription = await queryOne(`
    SELECT s.*, p.name as plan_name, p.price_cents, p.interval_days 
    FROM premium_subscriptions s 
    LEFT JOIN premium_plans p ON s.plan_id = p.id 
    WHERE s.user_id = ? 
    ORDER BY s.id DESC 
    LIMIT 1
  `, [locals.user.id]);

  // Load payment history from all sources (subscriptions, standalone products, and courses)
  // Prefer stripe label when stripe_session_id / stripe payment method is present
  const payments = await query(`
    SELECT * FROM (
      SELECT 
        'subscription' as type,
        p.amount_cents,
        p.status,
        p.payment_method,
        p.created_at
      FROM premium_payments p
      JOIN premium_subscriptions s ON p.subscription_id = s.id
      WHERE s.user_id = ?

      UNION ALL

      SELECT 
        'product' as type,
        COALESCE(prod.price_cents, 0) as amount_cents,
        pp.status,
        CASE WHEN pp.stripe_session_id IS NOT NULL AND pp.stripe_session_id != '' THEN 'stripe' ELSE 'card_pix' END as payment_method,
        pp.created_at
      FROM product_purchases pp
      LEFT JOIN products prod ON pp.product_id = prod.id
      WHERE pp.user_id = ?

      UNION ALL

      SELECT 
        'course' as type,
        COALESCE(cp.amount_cents, mc.price_cents, 0) as amount_cents,
        cp.status,
        CASE WHEN cp.stripe_session_id IS NOT NULL AND cp.stripe_session_id != '' THEN 'stripe' ELSE 'card_pix' END as payment_method,
        cp.created_at
      FROM course_purchases cp
      LEFT JOIN member_courses mc ON cp.course_id = mc.id
      WHERE cp.user_id = ?
    ) AS combined_payments
    ORDER BY created_at DESC
    LIMIT 20
  `, [locals.user.id, locals.user.id, locals.user.id]);

  const purchasedProducts = await query(`
    SELECT p.*, pp.created_at as purchased_at
    FROM products p
    JOIN product_purchases pp ON p.id = pp.product_id
    WHERE pp.user_id = ? AND pp.status = 'completed'
    ORDER BY pp.id DESC
  `, [locals.user.id]);

  // Player de curso do Adm: anexa token de acesso assinado aos links de entrega.
  const { decorateCourseLink } = await import('$lib/server/courseAccess');
  const userId = locals.user ? String(locals.user.id) : '';
  const decoratedProducts = purchasedProducts.map((p: any) => ({
    ...p,
    external_link: decorateCourseLink(p.external_link, userId),
  }));

  const paymentGateway = await getActivePaymentGateway();

  return {
    user: locals.user,
    subscription,
    payments,
    purchasedProducts: decoratedProducts,
    paymentGateway,
    requiresCpf: await requiresBrazilianProfileForCheckout(),
    asaasConfigured: paymentGateway === 'asaas' ? await isAsaasConfigured() : true
  };
};

export const actions: Actions = {
  cancel: async ({ locals }) => {
    if (!locals.user) {
      throw redirect(303, '/members/login');
    }

    const subscription = await queryOne(`
      SELECT * FROM premium_subscriptions 
      WHERE user_id = ? AND status = 'active' 
      ORDER BY id DESC 
      LIMIT 1
    `, [locals.user.id]);

    if (!subscription) {
      return fail(400, { error: 'SUB_NOT_FOUND' });
    }

    // Asaas cancel (default production path)
    if (subscription.asaas_subscription_id) {
      try {
        await cancelSubscription(subscription.asaas_subscription_id);
        
        // Update local status to cancelled, keep the expiration date
        await updateSubscriptionByAsaasId(subscription.asaas_subscription_id, {
          status: 'cancelled',
          expires_at: subscription.expires_at
        });

        return { success: 'SUB_CANCEL_SUCCESS' };
      } catch (e) {
        console.error('Error cancelling subscription:', e);
        return fail(500, { error: 'SUB_CANCEL_GATEWAY' });
      }
    }

    // Stripe cancel (optional gateway)
    if (subscription.stripe_subscription_id && !String(subscription.stripe_subscription_id).startsWith('cs_pending:')) {
      try {
        await cancelStripeSubscription(subscription.stripe_subscription_id);
        await run(
          "UPDATE premium_subscriptions SET status = 'cancelled' WHERE stripe_subscription_id = ?",
          [subscription.stripe_subscription_id]
        );
        return { success: 'SUB_CANCEL_SUCCESS' };
      } catch (e) {
        console.error('Error cancelling Stripe subscription:', e);
        return fail(500, { error: 'SUB_CANCEL_GATEWAY' });
      }
    }

    return fail(400, { error: 'SUB_CANCEL_NOT_AUTO' });
  },

  updateProfile: async ({ request, locals, url }) => {
    if (!locals.user) {
      throw redirect(303, '/members/login');
    }

    const data = await request.formData();
    const name = (data.get('name') as string || '').trim();
    const cpf = (data.get('cpf') as string || '').trim().replace(/\D/g, '');
    const phone = (data.get('phone') as string || '').trim();
    const needCpf = await requiresBrazilianProfileForCheckout();

    if (!name) {
      return fail(400, { error: needCpf ? 'PROFILE_NAME_CPF_REQUIRED' : 'PROFILE_NAME_REQUIRED' });
    }

    if (needCpf) {
      if (!cpf) {
        return fail(400, { error: 'PROFILE_NAME_CPF_REQUIRED' });
      }
      if (cpf.length !== 11) {
        return fail(400, { error: 'PROFILE_CPF_INVALID' });
      }
    } else if (cpf && cpf.length > 0 && cpf.length !== 11) {
      // Optional CPF when present must still be valid
      return fail(400, { error: 'PROFILE_CPF_INVALID' });
    }

    try {
      await run('UPDATE users SET name = ?, cpf = ?, phone = ? WHERE id = ?', [
        name,
        cpf || null,
        phone,
        locals.user.id
      ]);
      
      const redirectTo = (data.get('redirectTo') as string || url.searchParams.get('redirectTo') || '').trim();
      if (redirectTo) {
        throw redirect(303, redirectTo);
      }

      return { success: 'PROFILE_UPDATE_SUCCESS' };
    } catch (e) {
      if (isRedirect(e)) throw e;
      console.error('Error updating user profile:', e);
      return fail(500, { error: 'PROFILE_UPDATE_FAIL' });
    }
  }
};
