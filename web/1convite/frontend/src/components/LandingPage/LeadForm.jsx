import React, { useState } from 'react';
import { sendLeadWebhook } from '../../services/webhookService';

export function LeadForm() {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await sendLeadWebhook({ phone });
      setSuccess(true);
    } catch (err) {
      alert('Erro ao enviar. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="form-success">
        <h3 className="form-success-title">Recebemos seu contato!</h3>
        <p className="form-success-body">Em breve nossa IA vai te enviar uma mensagem no WhatsApp.</p>
      </div>
    );
  }

  return (
    <form id="hero-form" className="hero-form" onSubmit={handleSubmit}>
        <div className="input-inline">
          <input id="hero-whatsapp" type="tel" placeholder="WhatsApp da clínica (com DDD)" autocomplete="tel" inputmode="tel" required aria-label="WhatsApp da clínica" />
          <button type="submit">
            Quero meu diagnóstico <span className="arrow" aria-hidden="true">→</span>
          </button>
        </div>
        <div className="form-hint">
          Sem custo. Sem compromisso. Apenas se fizer sentido pra sua clínica.
        </div>
      </form>
  );
}
