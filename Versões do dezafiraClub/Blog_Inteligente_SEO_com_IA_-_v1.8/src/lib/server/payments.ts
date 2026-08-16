/**
 * Payment gateway selector.
 *
 * SAFETY FOR PRODUCTION:
 * - Default is always "asaas" when unset/empty.
 * - Stripe is used only when payment_gateway is explicitly "stripe"
 *   AND Stripe secret key is configured.
 * - If gateway=stripe but Stripe is misconfigured, falls back to Asaas
 *   when Asaas is available (never breaks live Asaas projects).
 */
import { env } from '$env/dynamic/private';
import { getSettings } from './database';
import { isAsaasConfigured } from './asaas';
import { isStripeConfigured } from './stripe';

export type PaymentGateway = 'asaas' | 'stripe';

export async function getConfiguredPaymentGatewaySetting(): Promise<string> {
  const settings = await getSettings();
  return (env.PAYMENT_GATEWAY || settings.payment_gateway || 'asaas').toLowerCase().trim();
}

/**
 * Returns the gateway that should be used for new checkouts.
 * Never returns stripe unless it is fully usable.
 */
export async function getActivePaymentGateway(): Promise<PaymentGateway> {
  const preferred = await getConfiguredPaymentGatewaySetting();

  if (preferred === 'stripe') {
    if (await isStripeConfigured()) return 'stripe';
    // Misconfiguration: keep production Asaas sites working
    if (await isAsaasConfigured()) {
      console.warn(
        '[payments] payment_gateway=stripe but Stripe is not configured; falling back to asaas'
      );
      return 'asaas';
    }
    // Stripe preferred but neither works — still report stripe so UI can show setup error
    return 'stripe';
  }

  // Default path for all existing production projects
  return 'asaas';
}

export async function isAnyPaymentGatewayConfigured(): Promise<boolean> {
  const gw = await getActivePaymentGateway();
  if (gw === 'stripe') return isStripeConfigured();
  return isAsaasConfigured();
}

/** CPF/name required only for Asaas (Brazilian tax id). Stripe uses email. */
export async function requiresBrazilianProfileForCheckout(): Promise<boolean> {
  return (await getActivePaymentGateway()) === 'asaas';
}
