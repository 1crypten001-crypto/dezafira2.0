import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

// Simulated contact storage
const contacts: Array<{
  id: string;
  name: string;
  email: string;
  phone?: string;
  subject: string;
  message: string;
  created_at: string;
}> = [];

export const POST: RequestHandler = async ({ request }) => {
  try {
    const body = await request.json();
    const { name, email, phone, subject, message } = body;

    // Validation
    if (!name || name.trim().length < 2) {
      return json({ error: 'Nome é obrigatório (mínimo 2 caracteres)' }, { status: 400 });
    }

    if (!email || !isValidEmail(email)) {
      return json({ error: 'E-mail inválido' }, { status: 400 });
    }

    if (!subject) {
      return json({ error: 'Assunto é obrigatório' }, { status: 400 });
    }

    if (!message || message.trim().length < 10) {
      return json({ error: 'Mensagem é obrigatória (mínimo 10 caracteres)' }, { status: 400 });
    }

    // Create contact entry
    const contact = {
      id: crypto.randomUUID(),
      name: name.trim(),
      email: email.trim().toLowerCase(),
      phone: phone?.trim() || null,
      subject: subject.trim(),
      message: message.trim(),
      created_at: new Date().toISOString()
    };

    contacts.push(contact);

    // In production, you would:
    // 1. Save to database
    // 2. Send email notification
    // 3. Integrate with CRM

    console.log('New contact:', contact);

    return json({ 
      success: true, 
      message: 'Mensagem enviada com sucesso!',
      id: contact.id 
    });
  } catch (error) {
    console.error('Contact API error:', error);
    return json({ error: 'Erro ao processar solicitação' }, { status: 500 });
  }
};

export const GET: RequestHandler = async () => {
  // Return contacts for admin (in production, add authentication)
  return json({ contacts: contacts.slice(-100) });
};

function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}