/**
 * Stripe payment gateway (optional).
 * Default production path remains Asaas — only used when payment_gateway=stripe
 * AND a Stripe secret key is configured.
 */
import Stripe from 'stripe';
import { env } from '$env/dynamic/private';
import { getSettings } from './database';

async function getStripeSettings() {
  const settings = await getSettings();
  // Currency: brl default (BR/Asaas-compatible); set stripe_currency=usd (etc.) for international
  const currency = (env.STRIPE_CURRENCY || settings.stripe_currency || 'brl').toLowerCase().trim() || 'brl';
  return {
    secretKey: env.STRIPE_SECRET_KEY || settings.stripe_secret_key || '',
    webhookSecret: env.STRIPE_WEBHOOK_SECRET || settings.stripe_webhook_secret || '',
    publishableKey: env.STRIPE_PUBLISHABLE_KEY || settings.stripe_publishable_key || '',
    siteUrl: env.SITE_URL || settings.site_url || 'https://seusite.com',
    currency
  };
}

export async function isStripeConfigured(): Promise<boolean> {
  const s = await getStripeSettings();
  return !!s.secretKey;
}

export async function getStripeClient(): Promise<Stripe> {
  const s = await getStripeSettings();
  if (!s.secretKey) throw new Error('Stripe secret key not configured');
  // Use package default API version for forward compatibility
  return new Stripe(s.secretKey);
}

/** Map plan interval_days to Stripe recurring price_data */
export function mapIntervalDays(days: number): { interval: Stripe.PriceCreateParams.Recurring.Interval; interval_count: number } {
  if (days <= 7) return { interval: 'week', interval_count: 1 };
  if (days <= 31) return { interval: 'month', interval_count: 1 };
  if (days <= 93) return { interval: 'month', interval_count: 3 };
  if (days <= 186) return { interval: 'month', interval_count: 6 };
  return { interval: 'year', interval_count: 1 };
}

export async function createSubscriptionCheckout(params: {
  planName: string;
  priceCents: number;
  intervalDays: number;
  customerEmail: string;
  userId: number;
  planId: number;
  currency?: string;
}): Promise<{ sessionId: string; url: string }> {
  const stripe = await getStripeClient();
  const settings = await getStripeSettings();
  const site = settings.siteUrl.replace(/\/$/, '');
  const recurring = mapIntervalDays(params.intervalDays || 30);
  const currency = (params.currency || settings.currency || 'brl').toLowerCase();

  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    customer_email: params.customerEmail,
    line_items: [
      {
        price_data: {
          currency,
          unit_amount: params.priceCents,
          recurring: {
            interval: recurring.interval,
            interval_count: recurring.interval_count
          },
          product_data: {
            name: params.planName
          }
        },
        quantity: 1
      }
    ],
    success_url: `${site}/members/dashboard?checkout=success`,
    cancel_url: `${site}/premium?checkout=cancelled`,
    allow_promotion_codes: true,
    billing_address_collection: 'auto',
    metadata: {
      type: 'premium_subscription',
      user_id: String(params.userId),
      plan_id: String(params.planId)
    },
    subscription_data: {
      metadata: {
        user_id: String(params.userId),
        plan_id: String(params.planId)
      }
    }
  });

  if (!session.url) throw new Error('Stripe Checkout session missing URL');
  return { sessionId: session.id, url: session.url };
}

export async function createOneTimeCheckout(params: {
  productName: string;
  priceCents: number;
  customerEmail: string;
  userId: number;
  kind: 'product' | 'course';
  productId?: number;
  courseId?: number;
  buyerAccessId?: string | null;
  currency?: string;
  successPath?: string;
  cancelPath?: string;
}): Promise<{ sessionId: string; url: string }> {
  const stripe = await getStripeClient();
  const settings = await getStripeSettings();
  const site = settings.siteUrl.replace(/\/$/, '');
  const currency = (params.currency || settings.currency || 'brl').toLowerCase();

  const session = await stripe.checkout.sessions.create({
    mode: 'payment',
    customer_email: params.customerEmail,
    line_items: [
      {
        price_data: {
          currency,
          unit_amount: params.priceCents,
          product_data: { name: params.productName }
        },
        quantity: 1
      }
    ],
    success_url: `${site}${params.successPath || '/members/dashboard?checkout=success'}`,
    cancel_url: `${site}${params.cancelPath || '/products?checkout=cancelled'}`,
    allow_promotion_codes: true,
    billing_address_collection: 'auto',
    metadata: {
      type: params.kind === 'product' ? 'product_purchase' : 'course_purchase',
      user_id: String(params.userId),
      product_id: params.productId != null ? String(params.productId) : '',
      course_id: params.courseId != null ? String(params.courseId) : '',
      buyer_access_id: params.buyerAccessId || ''
    }
  });

  if (!session.url) throw new Error('Stripe Checkout session missing URL');
  return { sessionId: session.id, url: session.url };
}

export async function cancelStripeSubscription(stripeSubscriptionId: string): Promise<void> {
  const stripe = await getStripeClient();
  await stripe.subscriptions.cancel(stripeSubscriptionId);
}

export async function constructStripeEvent(
  rawBody: string | Buffer,
  signature: string
): Promise<Stripe.Event> {
  const stripe = await getStripeClient();
  const settings = await getStripeSettings();
  if (!settings.webhookSecret) {
    throw new Error('Stripe webhook secret not configured');
  }
  return stripe.webhooks.constructEvent(rawBody, signature, settings.webhookSecret);
}
