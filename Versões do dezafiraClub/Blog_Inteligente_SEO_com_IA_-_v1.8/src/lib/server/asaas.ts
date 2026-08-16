import { env } from '$env/dynamic/private';
import { getSettings } from './database';

async function getAsaasSettings() {
  const settings = await getSettings();
  
  let apiUrl = env.ASAAS_API_URL || settings.asaas_api_url || 'https://api-sandbox.asaas.com/v3';
  
  // Normalize URLs to remove the extra '/api' in api.asaas.com/api/v3 or sandbox
  if (apiUrl.includes('api.asaas.com/api/v3')) {
    apiUrl = 'https://api.asaas.com/v3';
  } else if (apiUrl.includes('sandbox.asaas.com/api/v3')) {
    apiUrl = 'https://api-sandbox.asaas.com/v3';
  } else if (apiUrl.includes('sandbox.asaas.com/v3')) {
    apiUrl = 'https://api-sandbox.asaas.com/v3';
  }

  return {
    apiKey: env.ASAAS_API_KEY || settings.asaas_api_key || '',
    apiUrl,
    webhookSecret: env.ASAAS_WEBHOOK_SECRET || settings.asaas_webhook_secret || '',
    siteUrl: env.SITE_URL || settings.site_url || 'https://seusite.com'
  };
}

export async function isAsaasConfigured(): Promise<boolean> {
  const settings = await getAsaasSettings();
  return !!settings.apiKey;
}

async function request(path: string, options: RequestInit = {}) {
  const settings = await getAsaasSettings();
  
  if (!settings.apiKey) {
    throw new Error('Asaas API key not configured');
  }

  const url = `${settings.apiUrl.replace(/\/$/, '')}${path}`;
  const headers = {
    'access_token': settings.apiKey,
    'Content-Type': 'application/json',
    ...options.headers
  };

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`Asaas API error on ${path}:`, errorText);
    throw new Error(`Asaas API error: ${response.statusText} (${response.status}) - ${errorText}`);
  }

  return response.json();
}

export async function createCustomer(name: string, email: string, cpfCnpj?: string): Promise<{ id: string }> {
  try {
    const data = await request('/customers', {
      method: 'POST',
      body: JSON.stringify({
        name,
        email,
        cpfCnpj: cpfCnpj || undefined
      })
    });
    return { id: data.id };
  } catch (e) {
    console.error('Error creating customer on Asaas:', e);
    throw e;
  }
}

export async function createSubscription(params: {
  planName: string;
  value: number;
  customerId: string;
  cycleDays: number;
  billingType?: string;
}): Promise<{ id: string; invoiceUrl: string }> {
  try {
    // Map cycle days to Asaas cycles
    // Asaas cycle options: WEEKLY, BIWEEKLY, MONTHLY, BIMONTHLY, QUARTERLY, SEMIANNUALLY, YEARLY
    let cycle = 'MONTHLY';
    if (params.cycleDays === 7) cycle = 'WEEKLY';
    else if (params.cycleDays === 14) cycle = 'BIWEEKLY';
    else if (params.cycleDays === 30) cycle = 'MONTHLY';
    else if (params.cycleDays === 60) cycle = 'BIMONTHLY';
    else if (params.cycleDays === 90) cycle = 'QUARTERLY';
    else if (params.cycleDays === 180) cycle = 'SEMIANNUALLY';
    else if (params.cycleDays === 365) cycle = 'YEARLY';

    // Set first charge due date to tomorrow to allow billing link creation
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const nextDueDate = tomorrow.toISOString().split('T')[0];

    const settings = await getAsaasSettings();
    let data;
    try {
      data = await request('/subscriptions', {
        method: 'POST',
        body: JSON.stringify({
          customer: params.customerId,
          billingType: params.billingType || 'UNDEFINED', // Let user choose credit card, bank slip, or PIX
          value: params.value,
          nextDueDate,
          cycle,
          description: `Plano Premium: ${params.planName}`,
          updatePendingPayments: true,
          callback: {
            successUrl: `${settings.siteUrl.replace(/\/$/, '')}/members/dashboard`,
            autoRedirect: true
          }
        })
      });
    } catch (err: any) {
      if (err.message && (err.message.includes('domínio') || err.message.includes('domain') || err.message.includes('invalid_object'))) {
        console.warn('Asaas domain check failed, retrying subscription creation without callback redirect...');
        data = await request('/subscriptions', {
          method: 'POST',
          body: JSON.stringify({
            customer: params.customerId,
            billingType: params.billingType || 'UNDEFINED',
            value: params.value,
            nextDueDate,
            cycle,
            description: `Plano Premium: ${params.planName}`,
            updatePendingPayments: true
          })
        });
      } else {
        throw err;
      }
    }

    // Retrieve generated payment invoiceUrl for subscription checkout redirection
    const payments = await request(`/subscriptions/${data.id}/payments`);
    const invoiceUrl = payments.data?.[0]?.invoiceUrl || data.bankSlipUrl || `https://sandbox.asaas.com/checkoutSession/show?id=${data.id}`;

    return {
      id: data.id,
      invoiceUrl
    };
  } catch (e) {
    console.error('Error creating subscription on Asaas:', e);
    throw e;
  }
}

export async function cancelSubscription(asaasSubscriptionId: string): Promise<void> {
  try {
    await request(`/subscriptions/${asaasSubscriptionId}`, {
      method: 'DELETE'
    });
  } catch (e) {
    console.error(`Error deleting subscription ${asaasSubscriptionId} on Asaas:`, e);
    throw e;
  }
}

export async function getSubscriptionPayments(asaasSubscriptionId: string): Promise<any[]> {
  try {
    const response = await request(`/subscriptions/${asaasSubscriptionId}/payments`);
    return response.data || [];
  } catch (e) {
    console.error(`Error fetching payments for subscription ${asaasSubscriptionId} from Asaas:`, e);
    return [];
  }
}

export async function createPayment(params: {
  productName: string;
  value: number;
  customerId: string;
  externalReference?: string;
  billingType?: string;
  successUrl?: string;
}): Promise<{ id: string; invoiceUrl: string }> {
  try {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dueDate = tomorrow.toISOString().split('T')[0];

    const settings = await getAsaasSettings();
    const successUrl = params.successUrl || `${settings.siteUrl.replace(/\/$/, '')}/members/dashboard`;
    let data;
    try {
      data = await request('/payments', {
        method: 'POST',
        body: JSON.stringify({
          customer: params.customerId,
          billingType: params.billingType || 'UNDEFINED', // PIX, Boleto, Cartão de Crédito
          value: params.value,
          dueDate,
          description: `Produto Digital: ${params.productName}`,
          externalReference: params.externalReference || undefined,
          callback: {
            successUrl,
            autoRedirect: true
          }
        })
      });
    } catch (err: any) {
      if (err.message && (err.message.includes('domínio') || err.message.includes('domain') || err.message.includes('invalid_object'))) {
        console.warn('Asaas domain check failed, retrying payment creation without callback redirect...');
        data = await request('/payments', {
          method: 'POST',
          body: JSON.stringify({
            customer: params.customerId,
            billingType: params.billingType || 'UNDEFINED',
            value: params.value,
            dueDate,
            description: `Produto Digital: ${params.productName}`,
            externalReference: params.externalReference || undefined
          })
        });
      } else {
        throw err;
      }
    }

    return {
      id: data.id,
      invoiceUrl: data.invoiceUrl || data.bankSlipUrl
    };
  } catch (e) {
    console.error('Error creating payment on Asaas:', e);
    throw e;
  }
}
