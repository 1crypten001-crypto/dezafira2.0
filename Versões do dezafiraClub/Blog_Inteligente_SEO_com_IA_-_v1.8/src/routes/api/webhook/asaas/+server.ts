import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { 
  getSubscriptionByAsaasId, 
  createPayment, 
  getPaymentByAsaasId, 
  updateSubscriptionByAsaasId, 
  getSettings,
  queryOne,
  run
} from '$lib/server/database';
import { env } from '$env/dynamic/private';

export const POST: RequestHandler = async ({ request }) => {
  try {
    // 1. Authenticate webhook request
    const asaasToken = request.headers.get('asaas-access-token');
    const settings = await getSettings();
    const webhookSecret = env.ASAAS_WEBHOOK_SECRET || settings.asaas_webhook_secret || '';

    if (!webhookSecret || asaasToken !== webhookSecret) {
      console.warn('[ASAAS WEBHOOK] Unauthorized request received');
      return json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const event = body.event;
    console.log(`[ASAAS WEBHOOK] Received event: ${event}`);

    // 2. Handle events
    if (event === 'PAYMENT_RECEIVED' || event === 'PAYMENT_CONFIRMED') {
      const payment = body.payment;
      
      if (payment.subscription) {
        // Find subscription in our DB
        const subscription = await getSubscriptionByAsaasId(payment.subscription);
        
        if (subscription) {
          // Check if payment is already recorded
          const existingPayment = await getPaymentByAsaasId(payment.id);
          
          if (!existingPayment) {
            // Record payment in premium_payments
            await createPayment({
              subscription_id: subscription.id,
              amount_cents: Math.round(payment.value * 100),
              status: 'approved',
              payment_method: payment.billingType || 'UNDEFINED',
              asaas_payment_id: payment.id
            });
          }

          // Fetch plan duration to calculate new expiration date
          const planInfo = await queryOne(`
            SELECT p.interval_days 
            FROM premium_subscriptions s 
            JOIN premium_plans p ON s.plan_id = p.id 
            WHERE s.asaas_subscription_id = ?
          `, [payment.subscription]);

          const intervalDays = planInfo?.interval_days || 30;
          
          // Calculate expiration date: interval days from now + 2 days buffer (grace period)
          const expiresAt = new Date();
          expiresAt.setDate(expiresAt.getDate() + intervalDays + 2);
          const expiresAtStr = expiresAt.toISOString().replace('T', ' ').substring(0, 19); // SQLite datetime format

          // Update subscription to active
          await updateSubscriptionByAsaasId(payment.subscription, {
            status: 'active',
            expires_at: expiresAtStr
          });

          console.log(`[ASAAS WEBHOOK] Updated subscription ${payment.subscription} to active. Expires at: ${expiresAtStr}`);
        } else {
          console.warn(`[ASAAS WEBHOOK] Subscription ${payment.subscription} not found in database`);
        }
      } else {
        // One-off payment (product purchase or course purchase)
        const purchase = await queryOne('SELECT pp.*, p.resource_type FROM product_purchases pp LEFT JOIN products p ON pp.product_id = p.id WHERE pp.asaas_payment_id = ?', [payment.id]);
        if (purchase) {
          // Produtos com entrega manual ficam 'pending_delivery' até o admin compartilhar e marcar como entregue
          const newStatus = purchase.resource_type === 'manual' ? 'pending_delivery' : 'completed';
          await run('UPDATE product_purchases SET status = ? WHERE asaas_payment_id = ?', [newStatus, payment.id]);
          console.log(`[ASAAS WEBHOOK] Updated product purchase ${purchase.id} to ${newStatus} (resource_type: ${purchase.resource_type || 'file'})`);
        } else {
          const coursePurchase = await queryOne('SELECT * FROM course_purchases WHERE asaas_payment_id = ?', [payment.id]);
          if (coursePurchase) {
            await run("UPDATE course_purchases SET status = 'approved' WHERE asaas_payment_id = ?", [payment.id]);
            console.log(`[ASAAS WEBHOOK] Updated course purchase ${coursePurchase.id} to approved`);
          } else {
            console.warn(`[ASAAS WEBHOOK] One-off payment ${payment.id} not associated with subscription, product purchase or course purchase`);
          }
        }
      }
    } else if (event === 'SUBSCRIPTION_DELETED') {
      const subscription = body.subscription;
      
      if (subscription && subscription.id) {
        // Mark subscription as cancelled in local database
        const result = await run(
          "UPDATE premium_subscriptions SET status = 'cancelled' WHERE asaas_subscription_id = ?",
          [subscription.id]
        );

        if (result.changes > 0) {
          console.log(`[ASAAS WEBHOOK] Subscription ${subscription.id} marked as cancelled`);
        } else {
          console.warn(`[ASAAS WEBHOOK] Subscription ${subscription.id} not found to cancel`);
        }
      }
    }

    return json({ received: true });
  } catch (e) {
    console.error('[ASAAS WEBHOOK] Error handling webhook:', e);
    return json({ error: 'Internal Server Error' }, { status: 500 });
  }
};
