<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatMoney } from "$lib/i18n";

  let { data }: { data: any } = $props();

  const lang = $derived($page.data.language || 'pt');
  const product = $derived(data.product);

  // Snapshots de inicialização (dados de load não mudam durante a visita)
  const hasBundleOffer = $derived(!!data.bundleOffer);
  const hasUpsell = $derived(!!data.upsell);
  const hasDownsell = $derived(!!data.downsell);

  // Fluxo da esteira: Oferta principal → PACOTE COMPLETO → UPSELL → (recusou?) → DOWNSELL → (recusou?) → Dashboard
  // Sem combo/upsell configurado, pula direto para o próximo estágio (ou para o fim).
  let stage = $state(hasBundleOffer ? 'bundle' : (hasUpsell ? 'upsell' : (hasDownsell ? 'downsell' : 'done')));
  const showBundle = $derived(stage === 'bundle' && hasBundleOffer);
  const showUpsell = $derived(stage === 'upsell' && hasUpsell);
  const showDownsell = $derived(stage === 'downsell' && hasDownsell);

  const bundleEconomyPct = $derived(
    data.bundleOffer && data.bundleOffer.bundle_original_cents > 0
      ? Math.round((1 - data.bundleOffer.price_cents / data.bundleOffer.bundle_original_cents) * 100)
      : 0
  );

  function declineBundle() {
    stage = hasUpsell ? 'upsell' : (hasDownsell ? 'downsell' : 'done');
  }

  function declineUpsell() {
    stage = hasDownsell ? 'downsell' : 'done';
  }

  function declineDownsell() {
    stage = 'done';
  }

  function goDashboard() {
    window.location.href = '/members/dashboard';
  }

  function formatPrice(cents: number) {
    return formatMoney(lang, cents);
  }
</script>

<svelte:head>
  <title>{t(lang, 'checkout.obrigado_title') || 'Compra confirmada'} | Dezafira</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<div style="min-height: 100vh; background: #f8fafc; display: flex; align-items: center; justify-content: center; padding: 24px; font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;">
  <div style="max-width: 640px; width: 100%;">

    {#if !data.purchased}
      <!-- Sem compra confirmada: orienta para o produto -->
      <div style="background: #fff; border-radius: 20px; padding: 40px 32px; text-align: center; box-shadow: 0 12px 40px rgba(2,6,23,.08); border: 1px solid #e2e8f0;">
        <div style="font-size: 44px;">🔒</div>
        <h1 style="font-size: 22px; font-weight: 800; color: #0f172a; margin: 16px 0 8px;">Compra não localizada</h1>
        <p style="color: #64748b; font-size: 15px; margin: 0 0 24px;">Não encontramos uma compra confirmada para este acesso. Verifique sua área de membros.</p>
        <a href="/members/dashboard" style="display:inline-block; padding: 14px 32px; background: #0f172a; color:#fff; border-radius: 10px; font-weight: 700; text-decoration: none;">Ir para a área de membros</a>
      </div>

    {:else if !showBundle && !showUpsell && !showDownsell && stage === 'done'}
      <!-- Final: tudo recusado → dashboard -->
      <div style="background: #fff; border-radius: 20px; padding: 40px 32px; text-align: center; box-shadow: 0 12px 40px rgba(2,6,23,.08); border: 1px solid #e2e8f0;">
        <div style="font-size: 44px;">🎉</div>
        <h1 style="font-size: 22px; font-weight: 800; color: #0f172a; margin: 16px 0 8px;">Compra confirmada!</h1>
        <p style="color: #64748b; font-size: 15px; margin: 0 0 8px;">
          <strong style="color:#0f172a;">{product.name}</strong> já está disponível na sua área de membros.
        </p>
        <p style="color: #94a3b8; font-size: 14px; margin: 0 0 24px;">Sempre que quiser aproveitar outra oferta, é só voltar aqui. 😉</p>
        <button onclick={goDashboard} style="padding: 14px 32px; background: #16a34a; color:#fff; border: none; border-radius: 10px; font-weight: 700; font-size: 15px; cursor: pointer;">Acessar minha área de membros</button>
      </div>

    {:else}
      <!-- Confirmação da compra principal -->
      <div style="background: #fff; border-radius: 20px; padding: 32px; box-shadow: 0 12px 40px rgba(2,6,23,.08); border: 1px solid #e2e8f0; margin-bottom: 16px;">
        <div style="display:flex; align-items:center; gap:14px; margin-bottom: 6px;">
          <div style="width: 46px; height: 46px; border-radius: 50%; background: #dcfce7; display:flex; align-items:center; justify-content:center; font-size: 22px;">✅</div>
          <div>
            <div style="font-weight: 800; color: #16a34a; font-size: 15px;">Pagamento confirmado</div>
            <div style="color: #64748b; font-size: 13px;">{product.name} disponível na sua área de membros.</div>
          </div>
        </div>
      </div>

      {#if showBundle}
        <!-- Upsell do combo/pacote: quem comprou só o principal recebe a oferta do pacote completo -->
        <div style="background: linear-gradient(135deg, #78350f, #b45309); border-radius: 20px; padding: 32px; color: #fff; box-shadow: 0 16px 48px rgba(180,83,9,.35); border: 1px solid rgba(251,191,36,.35);">
          <div style="display:flex; justify-content: space-between; align-items:center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
            <span style="background: #fbbf24; color:#451a03; font-size: 11px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; padding: 5px 12px; border-radius: 999px;">🎁 PACOTE COMPLETO {bundleEconomyPct > 0 ? `— economize ${bundleEconomyPct}%` : ''}</span>
          </div>
          <h2 style="font-size: 24px; font-weight: 800; margin: 0 0 8px; line-height: 1.2;">{data.bundleOffer.name}</h2>
          {#if data.bundleOffer.description}
            <p style="color: #fde68a; font-size: 14px; line-height: 1.6; margin: 0 0 18px;">{data.bundleOffer.description}</p>
          {/if}
          {#if data.bundleOffer.bundle_items_list?.length}
            <div style="display:flex; flex-direction: column; gap: 8px; margin-bottom: 20px;">
              {#each data.bundleOffer.bundle_items_list as item}
                <div style="display:flex; align-items:center; gap: 10px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); border-radius: 10px; padding: 10px 12px;">
                  {#if item.image_url}
                    <img src={item.image_url} alt={item.name} style="width: 34px; height: 34px; object-fit: cover; border-radius: 8px;" />
                  {:else}
                    <span style="font-size: 18px;">🎁</span>
                  {/if}
                  <div style="flex: 1; font-size: 13px; font-weight: 600;">{item.name}</div>
                  <div style="font-size: 12px; color: #fde68a;">{formatPrice(item.price_cents)}</div>
                </div>
              {/each}
            </div>
          {/if}
          <div style="display:flex; align-items: baseline; gap: 10px; margin-bottom: 24px; flex-wrap: wrap;">
            {#if data.bundleOffer.bundle_original_cents > 0}
              <span style="font-size: 18px; color: #fcd34d; text-decoration: line-through;">{formatPrice(data.bundleOffer.bundle_original_cents)}</span>
            {/if}
            <span style="font-size: 34px; font-weight: 800;">{formatPrice(data.bundleOffer.price_cents)}</span>
            <span style="color:#fde68a; font-size: 13px;">pagamento único · todos os produtos</span>
          </div>
          {#if data.gatewayConfigured}
            <div style="display:flex; flex-direction: column; gap: 10px;">
              <a href="/purchase/{data.bundleOffer.id}?method=pix" style="display:block; text-align:center; padding: 15px; background: #22c55e; color:#fff; border-radius: 12px; font-weight: 800; text-decoration: none; font-size: 15px;">Quero o pacote completo agora</a>
              <a href="/purchase/{data.bundleOffer.id}?method=credit_card" style="display:block; text-align:center; padding: 14px; background: rgba(255,255,255,.12); color:#fff; border: 1px solid rgba(255,255,255,.25); border-radius: 12px; font-weight: 600; text-decoration: none; font-size: 14px;">Pagar com cartão de crédito</a>
              <button onclick={declineBundle} style="background: none; border: none; color: #fde68a; font-size: 13px; cursor: pointer; padding: 8px; text-decoration: underline;">Não, obrigado — quero só o que já comprei</button>
            </div>
          {:else}
            <p style="color:#fbbf24; font-size: 13px;">Pagamento temporariamente indisponível. Sua compra principal já está liberada.</p>
            <button onclick={goDashboard} style="margin-top: 12px; padding: 14px 32px; background: #22c55e; color:#fff; border:none; border-radius: 12px; font-weight: 800; cursor: pointer;">Ir para a área de membros</button>
          {/if}
        </div>

      {:else if showUpsell}
        <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 20px; padding: 32px; color: #fff; box-shadow: 0 16px 48px rgba(49,46,129,.35);">
          <div style="display:inline-block; background: #f59e0b; color:#451a03; font-size: 11px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; padding: 5px 12px; border-radius: 999px; margin-bottom: 14px;">⚡ Oferta exclusiva para você</div>
          <h2 style="font-size: 24px; font-weight: 800; margin: 0 0 8px; line-height: 1.2;">{data.upsell.name}</h2>
          {#if data.upsell.description}
            <p style="color: #c7d2fe; font-size: 14px; line-height: 1.6; margin: 0 0 20px;">{data.upsell.description}</p>
          {/if}
          <div style="display:flex; align-items: baseline; gap: 10px; margin-bottom: 24px;">
            {#if data.upsell.price_cents}
              <span style="font-size: 32px; font-weight: 800;">{formatPrice(data.upsell.price_cents)}</span>
            {/if}
            <span style="color:#a5b4fc; font-size: 13px;">pagamento único</span>
          </div>
          {#if data.gatewayConfigured}
            <div style="display:flex; flex-direction: column; gap: 10px;">
              <a href="/purchase/{data.upsell.id}?method=pix" style="display:block; text-align:center; padding: 15px; background: #22c55e; color:#fff; border-radius: 12px; font-weight: 800; text-decoration: none; font-size: 15px;">Quero aproveitar agora</a>
              <a href="/purchase/{data.upsell.id}?method=credit_card" style="display:block; text-align:center; padding: 14px; background: rgba(255,255,255,.12); color:#fff; border: 1px solid rgba(255,255,255,.25); border-radius: 12px; font-weight: 600; text-decoration: none; font-size: 14px;">Pagar com cartão de crédito</a>
              <button onclick={declineUpsell} style="background: none; border: none; color: #a5b4fc; font-size: 13px; cursor: pointer; padding: 8px; text-decoration: underline;">Não, obrigado — quero só o que já comprei</button>
            </div>
          {:else}
            <p style="color:#fbbf24; font-size: 13px;">Pagamento temporariamente indisponível. Sua compra principal já está liberada.</p>
            <button onclick={goDashboard} style="margin-top: 12px; padding: 14px 32px; background: #22c55e; color:#fff; border:none; border-radius: 12px; font-weight: 800; cursor: pointer;">Ir para a área de membros</button>
          {/if}
        </div>

      {:else if showDownsell}
        <div style="background: #fff; border-radius: 20px; padding: 32px; box-shadow: 0 12px 40px rgba(2,6,23,.08); border: 1px solid #e2e8f0;">
          <div style="display:inline-block; background: #fef3c7; color:#92400e; font-size: 11px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; padding: 5px 12px; border-radius: 999px; margin-bottom: 14px;">💛 Última chance com desconto</div>
          <h2 style="font-size: 22px; font-weight: 800; color:#0f172a; margin: 0 0 8px;">{data.downsell.name}</h2>
          {#if data.downsell.description}
            <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin: 0 0 20px;">{data.downsell.description}</p>
          {/if}
          <div style="display:flex; align-items: baseline; gap: 10px; margin-bottom: 24px;">
            {#if data.downsell.price_cents}
              <span style="font-size: 30px; font-weight: 800; color:#0f172a;">{formatPrice(data.downsell.price_cents)}</span>
            {/if}
            <span style="color:#94a3b8; font-size: 13px;">pagamento único</span>
          </div>
          {#if data.gatewayConfigured}
            <div style="display:flex; flex-direction: column; gap: 10px;">
              <a href="/purchase/{data.downsell.id}?method=pix" style="display:block; text-align:center; padding: 14px; background: #0f172a; color:#fff; border-radius: 12px; font-weight: 800; text-decoration: none; font-size: 15px;">Sim, quero aproveitar</a>
              <button onclick={declineDownsell} style="background: none; border: none; color: #64748b; font-size: 13px; cursor: pointer; padding: 8px; text-decoration: underline;">Não, obrigado</button>
            </div>
          {:else}
            <button onclick={goDashboard} style="margin-top: 12px; padding: 14px 32px; background: #0f172a; color:#fff; border:none; border-radius: 12px; font-weight: 800; cursor: pointer;">Ir para a área de membros</button>
          {/if}
        </div>
      {/if}
    {/if}

  </div>
</div>
