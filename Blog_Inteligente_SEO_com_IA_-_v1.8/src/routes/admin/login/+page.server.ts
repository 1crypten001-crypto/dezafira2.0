import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import type { RequestEvent } from '@sveltejs/kit';
import { verifyLogin, checkRateLimit, resetRateLimit, createSession, validateSession } from '$lib/server/auth';

export const load: PageServerLoad = async ({ cookies }) => {
  const sessionToken = cookies.get('admin_session');
  if (sessionToken && await validateSession(sessionToken)) {
    throw redirect(303, '/admin');
  }
  return {};
};

export const actions: Actions = {
  login: async ({ request, cookies, getClientAddress, url }: RequestEvent) => {
    const data = await request.formData();
    const username = data.get('username') as string;
    const password = data.get('password') as string;
    const clientIp = getClientAddress() || 'unknown';

    if (!username || !password) {
      return fail(400, { error: 'Preencha todos os campos' });
    }

    const rateLimit = checkRateLimit(clientIp);

    if (!rateLimit.allowed) {
      return fail(429, {
        error: `Muitas tentativas. Aguarde ${rateLimit.waitSeconds} segundos`,
        waitSeconds: rateLimit.waitSeconds
      });
    }

    const valid = await verifyLogin(username, password);

    if (!valid) {
      return fail(400, { error: 'Usuário ou senha incorretos', remaining: rateLimit.remaining });
    }

    resetRateLimit(clientIp);

    // Gerar token seguro ao invés de string fixa
    const sessionToken = await createSession(username);

    cookies.set('admin_session', sessionToken, {
      path: '/',
      httpOnly: true,
      sameSite: 'strict',
      maxAge: 60 * 60 * 24 * 30, // 30 dias
      secure: url.protocol === 'https:'
    });

    throw redirect(303, '/admin');
  }
};
