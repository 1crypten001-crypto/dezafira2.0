import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { getUserByUsername, createUser, getSettings, mergeAnonymousInterests, mergeAnonymousSeenPosts } from '$lib/server/database';
import { hashPassword, createSession, validateSession } from '$lib/server/auth';
import { parseSeenCookie } from '$lib/server/interest-engine';


export const load: PageServerLoad = async ({ cookies }) => {
  const settings = await getSettings();
  if (settings.enable_member_login !== '1') {
    throw redirect(303, '/');
  }

  const sessionToken = cookies.get('member_session');
  if (sessionToken && await validateSession(sessionToken)) {
    throw redirect(303, '/members/dashboard');
  }

  return {};
};

export const actions: Actions = {
  default: async ({ request, cookies, url }) => {
    const settings = await getSettings();
    if (settings.enable_member_login !== '1') {
      return fail(403, { error: 'O cadastro de membros está desativado' });
    }

    const data = await request.formData();
    const email = (data.get('email') as string || '').trim();
    const password = data.get('password') as string;
    const confirmPassword = data.get('confirmPassword') as string;

    if (!email || !password || !confirmPassword) {
      return fail(400, { error: 'Preencha todos os campos' });
    }

    if (password !== confirmPassword) {
      return fail(400, { error: 'As senhas não coincidem' });
    }

    if (password.length < 6) {
      return fail(400, { error: 'A senha deve conter no mínimo 6 caracteres' });
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return fail(400, { error: 'Por favor, insira um e-mail válido' });
    }

    try {
      const existingUser = await getUserByUsername(email);
      if (existingUser) {
        return fail(400, { error: 'Este e-mail já está sendo utilizado' });
      }

      // Hash password and save new member
      const hashedPassword = await hashPassword(password);
      await createUser(email, hashedPassword, 'member');

      // Create session and set cookie
      const sessionToken = await createSession(email);
      cookies.set('member_session', sessionToken, {
        path: '/',
        httpOnly: true,
        sameSite: 'strict',
        maxAge: 60 * 60 * 24 * 30, // 30 days
        secure: url.protocol === 'https:'
      });

      // Mesclar interesses e histórico de visualização anônimos
      const dbUser = await getUserByUsername(email);
      if (dbUser) {
        const anonInterests = cookies.get('user_interests');
        if (anonInterests) {
          await mergeAnonymousInterests(dbUser.id, anonInterests);
          cookies.delete('user_interests', { path: '/' });
        }
        const anonSeen = cookies.get('recently_seen_posts');
        if (anonSeen) {
          await mergeAnonymousSeenPosts(dbUser.id, parseSeenCookie(anonSeen));
          cookies.delete('recently_seen_posts', { path: '/' });
        }
      }

    } catch (e) {
      console.error('Error registering member:', e);
      return fail(500, { error: 'Erro interno ao realizar o cadastro. Tente novamente mais tarde.' });
    }

    throw redirect(303, '/members/dashboard');
  }
};
