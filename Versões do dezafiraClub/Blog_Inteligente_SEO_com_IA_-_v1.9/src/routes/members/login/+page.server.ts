import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { verifyLogin, checkRateLimit, resetRateLimit, createSession, validateSession, hashPassword } from '$lib/server/auth';
import { getUserByUsername, getSettings, createUser, createOtp, verifyOtpCode, mergeAnonymousInterests, mergeAnonymousSeenPosts } from '$lib/server/database';
import { sendOtpEmail } from '$lib/server/resend';
import { parseSeenCookie } from '$lib/server/interest-engine';


export const load: PageServerLoad = async ({ cookies, url }) => {
  const settings = await getSettings();
  if (settings.enable_member_login !== '1') {
    throw redirect(303, '/');
  }

  const redirectTo = url.searchParams.get('redirectTo') || '';
  const sessionToken = cookies.get('member_session');
  if (sessionToken && await validateSession(sessionToken)) {
    throw redirect(303, redirectTo || '/members/dashboard');
  }

  return {
    enableOtpLogin: settings.enable_otp_login === '1',
    redirectTo
  };
};

export const actions: Actions = {
  // Traditional password-based login
  login: async ({ request, cookies, getClientAddress, url }) => {
    const settings = await getSettings();
    if (settings.enable_otp_login === '1') {
      return fail(400, { error: 'O login por senha está desativado. Use o login por e-mail.' });
    }

    const data = await request.formData();
    const email = data.get('email') as string;
    const password = data.get('password') as string;
    const clientIp = getClientAddress() || 'unknown';
    const redirectTo = url.searchParams.get('redirectTo') || '';

    if (!email || !password) {
      return fail(400, { error: 'Preencha todos os campos' });
    }

    const rateLimit = checkRateLimit(clientIp);
    if (!rateLimit.allowed) {
      return fail(429, {
        error: `Muitas tentativas. Aguarde ${rateLimit.waitSeconds} segundos`,
        waitSeconds: rateLimit.waitSeconds
      });
    }

    // Verify password match
    const valid = await verifyLogin(email, password);
    if (!valid) {
      return fail(400, { error: 'E-mail ou senha incorretos', remaining: rateLimit.remaining });
    }

    resetRateLimit(clientIp);

    // Create session token and set cookie
    const sessionToken = await createSession(email);
    cookies.set('member_session', sessionToken, {
      path: '/',
      httpOnly: true,
      sameSite: 'strict',
      maxAge: 60 * 60 * 24 * 30, // 30 days
      secure: url.protocol === 'https:'
    });

    // Mesclar interesses e histórico de visualização anônimos
    const user = await getUserByUsername(email);
    if (user) {
      const anonInterests = cookies.get('user_interests');
      if (anonInterests) {
        await mergeAnonymousInterests(user.id, anonInterests);
        cookies.delete('user_interests', { path: '/' });
      }
      const anonSeen = cookies.get('recently_seen_posts');
      if (anonSeen) {
        await mergeAnonymousSeenPosts(user.id, parseSeenCookie(anonSeen));
        cookies.delete('recently_seen_posts', { path: '/' });
      }
    }

    throw redirect(303, redirectTo || '/members/dashboard');

  },

  // OTP Phase 1: Send OTP Code
  sendOtp: async ({ request, getClientAddress }) => {
    const settings = await getSettings();
    if (settings.enable_otp_login !== '1') {
      return fail(400, { error: 'Login via e-mail desativado.' });
    }

    const data = await request.formData();
    const email = (data.get('email') as string || '').trim().toLowerCase();
    const clientIp = getClientAddress() || 'unknown';

    if (!email) {
      return fail(400, { error: 'Por favor, insira o seu e-mail' });
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return fail(400, { error: 'Formato de e-mail inválido' });
    }

    const rateLimit = checkRateLimit(clientIp);
    if (!rateLimit.allowed) {
      return fail(429, {
        error: `Muitas tentativas. Aguarde ${rateLimit.waitSeconds} segundos`,
        waitSeconds: rateLimit.waitSeconds
      });
    }

    // Generate a 6-digit numeric OTP code
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    
    // Set 10 minutes expiry time
    const expiresAt = new Date(Date.now() + 10 * 60 * 1000).toISOString().replace('T', ' ').substring(0, 19);

    try {
      // Save code to database
      await createOtp(email, code, expiresAt);

      // Print code to console for easy local developer validation/bypass
      console.log(`\n--- [OTP LOG BYPASS] ---`);
      console.log(`Destinatário: ${email}`);
      console.log(`Código OTP: ${code}`);
      console.log(`Expiração: ${expiresAt}`);
      console.log(`-------------------------\n`);

      // Send via Resend API
      const sent = await sendOtpEmail(email, code);
      
      if (!sent) {
        // Fallback for developers/sandbox: allow progressing to step 2 with the code shown in the logs
        console.warn('[RESEND] API key or configuration missing/failed. OTP email was not sent. Use the bypass log above to test.');
        return { 
          otpSent: true, 
          email,
          error: 'Falha ao enviar e-mail. Se você tiver acesso ao terminal do servidor, use o código OTP gerado lá para entrar.'
        };
      }

      return { otpSent: true, email };
    } catch (e) {
      console.error('Error generating/sending OTP:', e);
      return fail(500, { error: 'Erro ao gerar código de acesso' });
    }
  },

  // OTP Phase 2: Verify OTP Code and Login (or register)
  verifyOtp: async ({ request, cookies, getClientAddress, url }) => {
    const settings = await getSettings();
    if (settings.enable_otp_login !== '1') {
      return fail(400, { error: 'Login via e-mail desativado.' });
    }

    const data = await request.formData();
    const email = (data.get('email') as string || '').trim().toLowerCase();
    const code = (data.get('code') as string || '').trim();
    const clientIp = getClientAddress() || 'unknown';
    const redirectTo = url.searchParams.get('redirectTo') || '';

    if (!email || !code) {
      return fail(400, { error: 'Preencha todos os campos', otpSent: true, email });
    }

    const rateLimit = checkRateLimit(clientIp);
    if (!rateLimit.allowed) {
      return fail(429, {
        error: `Muitas tentativas. Aguarde ${rateLimit.waitSeconds} segundos`,
        waitSeconds: rateLimit.waitSeconds,
        otpSent: true,
        email
      });
    }

    try {
      // Verify OTP in database
      const isValid = await verifyOtpCode(email, code);
      if (!isValid) {
        return fail(400, { error: 'Código inválido ou expirado', otpSent: true, email });
      }

      resetRateLimit(clientIp);

      // Auto-register user if they do not exist
      let user = await getUserByUsername(email);
      if (!user) {
        const randomPassword = Math.random().toString(36).substring(2, 12);
        const hashedPassword = await hashPassword(randomPassword);
        await createUser(email, hashedPassword, 'member');
      }

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
      console.error('Error verifying OTP:', e);
      return fail(500, { error: 'Erro ao validar código de acesso', otpSent: true, email });
    }

    throw redirect(303, redirectTo || '/members/dashboard');

  }
};
