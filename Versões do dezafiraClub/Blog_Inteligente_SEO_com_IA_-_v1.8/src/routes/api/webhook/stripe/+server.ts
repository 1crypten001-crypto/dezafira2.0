import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import {
  createPayment,
  getPaymentByStripeId,
  getSubscriptionByStripeId,
  updateSubscriptionByStripeId,
  queryOne,
  run
} from '$lib/server/database';
import { constructStripeEvent } from '$lib/server/stripe';

export const POST: RequestHandler = async ({ request }) => {
  try {
    const signature = request.headers.get('stripe-signature');
    if (!signature) {
      return json({ error: 'Missing stripe-signature' }, { status: 400 });
    }

    const rawBody = await request.text();
    let event;
    try {
      event = await constructStripeEvent(rawBody, signature);
    } catch (err) {
      console.warn('[STRIPE WEBHOOK] Signature verification failed:', err);
      return json({ error: 'Invalid signature' }, { status: 400 });
    }

    console.log(`[STRIPE WEBHOOK] Received event: ${event.type}`);

    if (event.type === 'checkout.session.completed') {
      const session = event.data.object as any;
      const meta = session.metadata || {};
      const type = meta.type;

      if (type === 'premium_subscription') {
        const userId = parseInt(meta.user_id, 10);
        const planId = parseInt(meta.plan_id, 10);
        const stripeSubId = session.subscription as string | null;
        const stripeCustomerId = (session.customer as string) || null;

        if (userId && planId && stripeSubId) {
          // Link pending local subscription created at checkout start, or create if missing
          let local = await getSubscriptionByStripeId(stripeSubId);
          if (!local) {
            // Prefer row tagged with this Checkout Session (cs_pending:cs_…)
            const sessionId = session.id as string;
            if (sessionId) {
              local = await getSubscriptionByStripeId(`cs_pending:${sessionId}`);
            }
            // Fallback: latest pending for this user/plan
            if (!local) {
              local = await queryOne(
                `SELECT * FROM premium_subscriptions
                 WHERE user_id = ? AND plan_id = ? AND status = 'pending'
                 ORDER BY id DESC LIMIT 1`,
                [userId, planId]
              );
            }
            if (local) {
              await run(
                `UPDATE premium_subscriptions
                 SET stripe_subscription_id = ?, stripe_customer_id = ?
                 WHERE id = ?`,
                [stripeSubId, stripeCustomerId, local.id]
              );
            }
          }

          const planInfo = await queryOne('SELECT interval_days FROM premium_plans WHERE id = ?', [
            planId
          ]);
          const intervalDays = planInfo?.interval_days || 30;
          const expiresAt = new Date();
          expiresAt.setDate(expiresAt.getDate() + intervalDays + 2);
          const expiresAtStr = expiresAt.toISOString().replace('T', ' ').substring(0, 19);

          await updateSubscriptionByStripeId(stripeSubId, {
            status: 'active',
            expires_at: expiresAtStr,
            stripe_customer_id: stripeCustomerId || undefined
          });

          // If still no row matched by stripe id (edge), force update by user pending
          if (!local) {
            await run(
              `UPDATE premium_subscriptions
               SET status = 'active', expires_at = ?, stripe_subscription_id = ?, stripe_customer_id = ?
               WHERE user_id = ? AND plan_id = ? AND status = 'pending'`,
              [expiresAtStr, stripeSubId, stripeCustomerId, userId, planId]
            );
          }

          console.log(`[STRIPE WEBHOOK] Premium sub activated for user ${userId} plan ${planId}`);
        }
      } else if (type === 'product_purchase') {
        const sessionId = session.id as string;
        const purchase = await queryOne(
          'SELECT pp.*, p.resource_type FROM product_purchases pp LEFT JOIN products p ON pp.product_id = p.id WHERE pp.stripe_session_id = ?',
          [sessionId]
        );
        if (purchase) {
          const newStatus = purchase.resource_type === 'manual' ? 'pending_delivery' : 'completed';
          await run('UPDATE product_purchases SET status = ? WHERE stripe_session_id = ?', [
            newStatus,
            sessionId
          ]);
          console.log(`[STRIPE WEBHOOK] Product purchase ${purchase.id} -> ${newStatus}`);
        }
      } else if (type === 'course_purchase') {
        const sessionId = session.id as string;
        const coursePurchase = await queryOne(
          'SELECT * FROM course_purchases WHERE stripe_session_id = ?',
          [sessionId]
        );
        if (coursePurchase) {
          await run("UPDATE course_purchases SET status = 'approved' WHERE stripe_session_id = ?", [
            sessionId
          ]);
          console.log(`[STRIPE WEBHOOK] Course purchase ${coursePurchase.id} approved`);
        }
      }
    } else if (event.type === 'invoice.paid') {
      // Renewal for subscriptions
      const invoice = event.data.object as any;
      const stripeSubId = invoice.subscription as string | null;
      if (stripeSubId) {
        const subscription = await getSubscriptionByStripeId(stripeSubId);
        if (subscription) {
          const paymentId = (invoice.payment_intent || invoice.id) as string;
          const existing = await getPaymentByStripeId(paymentId);
          if (!existing) {
            await createPayment({
              subscription_id: subscription.id,
              amount_cents: Math.round((invoice.amount_paid || 0)),
              status: 'approved',
              payment_method: 'stripe',
              stripe_payment_id: paymentId
            });
          }

          const planInfo = await queryOne(
            `SELECT p.interval_days FROM premium_subscriptions s
             JOIN premium_plans p ON s.plan_id = p.id
             WHERE s.stripe_subscription_id = ?`,
            [stripeSubId]
          );
          const intervalDays = planInfo?.interval_days || 30;
          const expiresAt = new Date();
          expiresAt.setDate(expiresAt.getDate() + intervalDays + 2);
          const expiresAtStr = expiresAt.toISOString().replace('T', ' ').substring(0, 19);

          await updateSubscriptionByStripeId(stripeSubId, {
            status: 'active',
            expires_at: expiresAtStr
          });
          console.log(`[STRIPE WEBHOOK] Renewed subscription ${stripeSubId} until ${expiresAtStr}`);
        }
      }
    } else if (event.type === 'customer.subscription.deleted') {
      const sub = event.data.object as any;
      if (sub?.id) {
        const result = await run(
          "UPDATE premium_subscriptions SET status = 'cancelled' WHERE stripe_subscription_id = ?",
          [sub.id]
        );
        if (result.changes > 0) {
          console.log(`[STRIPE WEBHOOK] Subscription ${sub.id} cancelled`);
        }
      }
    }

    return json({ received: true });
  } catch (e) {
    console.error('[STRIPE WEBHOOK] Error:', e);
    return json({ error: 'Internal Server Error' }, { status: 500 });
  }
};
