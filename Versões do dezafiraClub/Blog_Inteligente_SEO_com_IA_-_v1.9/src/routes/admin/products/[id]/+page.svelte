<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from "$app/forms";
    import type { PageData } from "./$types";

  const lang = $derived($page.data.language || 'pt');

let { data, form }: { data: PageData; form: any } = $props();

    let name = $state(data.product.name);
    let slug = $state(data.product.slug || '');
    let description = $state(data.product.description || '');
    let priceValue = $state(data.product.price_cents > 0 ? String(data.product.price_cents / 100).replace('.', ',') : '');
    const isCurrentlyCloudinary = !!(data.product.file_url && data.product.file_url.startsWith('http'));
    let resourceType = $state(data.product.resource_type || (data.product.file_url
        ? (isCurrentlyCloudinary ? 'cloudinary' : 'file')
        : (data.product.external_link ? 'link' : 'file'))); // 'file', 'cloudinary', 'link' ou 'manual'
    let externalLink = $state(data.product.external_link || '');
    // Novos campos de entrega manual preenchidos com os valores atuais do produto
    let accessLabel = $state(data.product.access_label || '');
    let driveInstructions = $state(data.product.drive_instructions || '');
    let deliveryDeadline = $state(data.product.delivery_deadline || '');
    let selectedFileName = $state<string | null>(null);
    let loading = $state(false);
    let imagePreviewUrl = $state<string | null>(data.product.image_url);
    let removeImage = $state(false);
    let removeFile = $state(false);
    let notifyBuyers = $state(false);
    let updateMessage = $state('');
    let categoryId = $state(data.product.category_id ? String(data.product.category_id) : '');
    let youtubeVideoUrl = $state(data.product.youtube_video_url || '');
    let isPremiumIncludedVal = $state(data.product.is_premium_included || 0);

    // Campos de serviço extra / Order bump
    let hasExtraService = $state(data.product.has_extra_service === 1);
    let extraServiceTitle = $state(data.product.extra_service_title || '');
    let extraServicePriceValue = $state(data.product.extra_service_price_cents && data.product.extra_service_price_cents > 0 ? String(data.product.extra_service_price_cents / 100).replace('.', ',') : '');
    let extraServiceDescription = $state(data.product.extra_service_description || '');

    // Esteira de produtos: upsell/downsell pós-compra
    let upsellProductId = $state(data.product.upsell_product_id ? String(data.product.upsell_product_id) : '');
    let downsellProductId = $state(data.product.downsell_product_id ? String(data.product.downsell_product_id) : '');

    function handleImageChange(e: Event) {
        const file = (e.target as HTMLInputElement).files?.[0];
        if (file) {
            imagePreviewUrl = URL.createObjectURL(file);
            removeImage = false;
        } else {
            imagePreviewUrl = data.product.image_url;
        }
    }

    function formatPrice(cents: number) {
        return (cents / 100).toLocaleString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR', { style: 'currency', currency: 'BRL' });
    }

    function parsePrice(value: string) {
        if (!value) return 0;
        const str = value.trim();
        if (!str) return 0;

        if (str.includes(',') || str.includes('.')) {
            const normalized = str.replace(',', '.');
            const num = parseFloat(normalized);
            return isNaN(num) ? 0 : Math.round(num * 100);
        }

        const num = parseInt(str, 10);
        return isNaN(num) ? 0 : num * 100;
    }
</script>

<div class="edit-product-page">
    <div class="page-header">
        <h1>{t(lang, "admin.products.edit")} Digital</h1>
        <p class="subtitle">Modifique as informações do seu recurso digital</p>
    </div>

    <form method="POST" use:enhance={({ formData, action }) => {
        console.log("=== ENHANCE FORM SUBMISSION ===");
        console.log("Action URL:", action.toString());
        console.log("Form Resource Type:", formData.get('resource_type'));
        
        const file = formData.get('product_file');
        if (file instanceof File) {
            console.log("Product File Selected:", file.name, "Size:", file.size, "bytes", "Type:", file.type);
        } else {
            console.log("No product file selected or invalid file object:", file);
        }
        
        loading = true;
        
        return async ({ result, update }) => {
            console.log("=== SERVER SUBMISSION RESULT ===");
            console.log("Result Type:", result.type);
            if (result.type === 'failure') {
                console.error("Submission Failure Status:", result.status, "Data:", result.data);
            } else if (result.type === 'success') {
                console.log("Submission Success Data:", result.data);
            } else if (result.type === 'error') {
                console.error("Submission Server Error:", result.error);
            }
            loading = false;
            update();
        };
    }} enctype="multipart/form-data" class="product-form">
        
        <div class="form-section">
            <div class="form-group">
                <label for="name">Nome do Produto</label>
                <input type="text" id="name" name="name" bind:value={name} placeholder="Ex: E-book de Introdução ao Svelte em PDF" required />
            </div>

            <div class="form-group">
                <label for="slug">Slug do Produto (URL)</label>
                <input type="text" id="slug" name="slug" bind:value={slug} placeholder="url-do-produto" />
                <small style="color: var(--text-muted); display: block; margin-top: 0.25rem;">Deixe em branco para gerar automaticamente com base no nome.</small>
            </div>

            <div class="form-group">
                <label for="description">{t(lang, "admin.ui.description")}</label>
                <textarea id="description" name="description" bind:value={description} rows="3" placeholder="Breve resumo sobre o arquivo/link..."></textarea>
            </div>

            <div class="form-group">
                <label for="category_id">{t(lang, "admin.ui.category")}</label>
                <select id="category_id" name="category_id" bind:value={categoryId} style="background: var(--bg-secondary); border: 1px solid var(--border-color); color: var(--text-primary); padding: 0.75rem; border-radius: var(--radius-md); width: 100%;">
                    <option value="">Sem Categoria (Geral)</option>
                    {#each data.categories as cat}
                        <option value={String(cat.id)}>{cat.name}</option>
                    {/each}
                </select>
                <small style="margin-top: 0.25rem; display: block;">
                    <a href="/admin/products/categories" target="_blank" style="color: var(--accent-color, #3b82f6); text-decoration: none; font-weight: 600;">Gerenciar Categorias →</a>
                </small>
            </div>

            <div class="form-group">
                <label for="youtube_video_url">URL do Vídeo do YouTube (Opcional)</label>
                <input type="text" id="youtube_video_url" name="youtube_video_url" bind:value={youtubeVideoUrl} placeholder="Ex: https://www.youtube.com/watch?v=..." />
                <small style="color: var(--text-muted); display: block; margin-top: 0.25rem;">Se preenchido, um player de vídeo explicativo com autoplay/mute expandirá automaticamente 2 segundos após a pessoa entrar na página do produto.</small>
            </div>

            <div class="form-group">
                <label for="product_image">Imagem Ilustrativa (Opcional)</label>
                
                {#if data.product.image_url}
                    <div style="margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                        <input type="checkbox" id="remove_image_checkbox" bind:checked={removeImage} onchange={() => {
                            if (removeImage) {
                                imagePreviewUrl = null;
                                const input = document.getElementById('product_image') as HTMLInputElement;
                                if (input) input.value = '';
                            } else {
                                imagePreviewUrl = data.product.image_url;
                            }
                        }} style="width: auto; margin: 0;" />
                        <label for="remove_image_checkbox" style="font-weight: normal; cursor: pointer; margin: 0;">Remover imagem ilustrativa atual</label>
                    </div>
                {/if}
                <input type="hidden" name="remove_image" value={removeImage ? "1" : "0"} />

                {#if imagePreviewUrl}
                    <div class="image-preview-container">
                        <img src={imagePreviewUrl} alt="Imagem do produto" class="image-preview" />
                        <span class="preview-badge">{imagePreviewUrl === data.product.image_url ? 'Imagem atual' : 'Nova imagem selecionada'}</span>
                        {#if imagePreviewUrl !== data.product.image_url}
                            <button type="button" class="btn-remove-image" onclick={() => {
                                imagePreviewUrl = data.product.image_url;
                                const input = document.getElementById('product_image') as HTMLInputElement;
                                if (input) input.value = '';
                                removeImage = false;
                            }}>Cancelar alteração</button>
                        {/if}
                    </div>
                {/if}
                <input type="file" id="product_image" name="product_image" class="file-input" accept="image/jpeg,image/png,image/gif,image/webp" onchange={handleImageChange} />
                <small>Envie uma nova imagem para substituir a atual. (Formatos: JPG, PNG, WebP. Máx. 5MB)</small>
            </div>
        </div>

        <div class="section-divider"></div>

        <div class="form-section">
            <div class="form-row">
                <div class="form-group">
                    <label for="price_display">Preço (opcional, em R$)</label>
                    <div class="price-input-group">
                        <input type="text" id="price_display" name="price_display" 
                            placeholder="19,90" 
                            value={priceValue}
                            oninput={(e) => {
                                const val = parsePrice((e.target as HTMLInputElement).value);
                                priceValue = (e.target as HTMLInputElement).value;
                                const hidden = document.getElementById('price_cents_val') as HTMLInputElement;
                                if (hidden) hidden.value = String(val);
                            }}
                        />
                        <span class="input-suffix">R$</span>
                    </div>
                    <input type="hidden" id="price_cents_val" name="price_cents" value={data.product.price_cents} />
                    {#if priceValue && parsePrice(priceValue) > 0}
                        {#if parsePrice(priceValue) < 500}
                            <small style="color: #dc2626; font-weight: 600; display: block; margin-top: 0.25rem;">⚠️ Atenção: O Asaas exige um valor mínimo de R$ 5,00 para pagamentos. Valores menores que R$ 5,00 darão erro na compra.</small>
                        {:else}
                            <small>Valor cadastrado: {formatPrice(parsePrice(priceValue))}</small>
                        {/if}
                    {:else}
                        <small class="free-info">Deixe em branco ou 0 para download gratuito. (Mínimo de R$ 5,00 para produtos pagos)</small>
                    {/if}
                </div>


                <div class="form-group">
                    <label for="resource_type">Tipo de Recurso</label>
                    <select id="resource_type" name="resource_type" bind:value={resourceType}>
                        <option value="file">Upload no Servidor (disco)</option>
                        <option value="cloudinary">☁️ Upload no Cloudinary (ZIP/PDF)</option>
                        <option value="link">Link de Terceiros (URL)</option>
                        <option value="manual">🤝 Entrega Manual (Drive, GitHub, etc.)</option>
                    </select>
                </div>
            </div>

            <div class="form-group" style="display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.5rem; background: #f8fafc; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; width: 100%; box-sizing: border-box;">
                <label for="is_premium_included" style="font-weight: 700; margin: 0; text-transform: none; letter-spacing: 0; font-size: 0.95rem; color: #0f172a;">
                    Disponibilidade na Assinatura Premium
                </label>
                <select id="is_premium_included" name="is_premium_included" bind:value={isPremiumIncludedVal} style="background: #fff; border: 1px solid #cbd5e1; color: #0f172a; padding: 0.6rem; border-radius: 6px; width: 100%; font-size: 0.9rem; cursor: pointer; outline: none;">
                    <option value={0}>Não incluso no Premium (apenas venda avulsa)</option>
                    <option value={1}>🌟 Incluso em qualquer Plano Premium (Livre para todos os assinantes)</option>
                    {#each data.premiumPlans as plan}
                        <option value={plan.id}>🔒 Included only in Plan: {plan.name}</option>
                    {/each}
                </select>
                <span style="font-size: 0.8rem; color: #64748b; line-height: 1.4; margin-top: 0.25rem;">
                    Selecione qual nível de assinatura premium do site dará acesso gratuito a este produto digital. 
                    <strong>Acesso vitalício permanente:</strong> quem comprar de forma avulsa sempre manterá acesso definitivo, mesmo que cancele a assinatura ou não seja Premium.
                </span>
            </div>

            <!-- Seção Esteira de Produtos: Upsell / Downsell pós-compra -->
            <div class="form-group" style="background: #fdf4ff; padding: 1.25rem; border-radius: 8px; border: 1px solid #f5d0fe; margin-bottom: 1.5rem;">
                <label style="font-weight: 700; font-size: 0.95rem; color: #a21caf; display: block; margin-bottom: 0.35rem;">
                    🎯 Esteira de Produtos (Upsell / Downsell)
                </label>
                <span style="font-size: 0.8rem; color: #c026d3; display: block; margin-bottom: 1rem; line-height: 1.4;">
                    Após a compra, o cliente vê uma página de obrigado com o produto de Upsell. Se recusar, vê o Downsell. Deixe vazio para pular.
                </span>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        <label for="upsell_product_id" style="font-size: 0.85rem; font-weight: 600; color: #a21caf; display: block; margin-bottom: 0.3rem;">Produto de Upsell (pós-compra)</label>
                        <select id="upsell_product_id" name="upsell_product_id" bind:value={upsellProductId} style="background: #fff; border: 1px solid #f5d0fe; border-radius: 6px; padding: 0.6rem; font-size: 0.9rem; width: 100%; box-sizing: border-box;">
                            <option value="">— Nenhum —</option>
                            {#each data.products || [] as p}
                                <option value={p.id} selected={String(p.id) === upsellProductId}>{p.name} ({formatPrice(p.price_cents)})</option>
                            {/each}
                        </select>
                    </div>
                    <div>
                        <label for="downsell_product_id" style="font-size: 0.85rem; font-weight: 600; color: #a21caf; display: block; margin-bottom: 0.3rem;">Produto de Downsell (se recusar o upsell)</label>
                        <select id="downsell_product_id" name="downsell_product_id" bind:value={downsellProductId} style="background: #fff; border: 1px solid #f5d0fe; border-radius: 6px; padding: 0.6rem; font-size: 0.9rem; width: 100%; box-sizing: border-box;">
                            <option value="">— Nenhum —</option>
                            {#each data.products || [] as p}
                                <option value={p.id} selected={String(p.id) === downsellProductId}>{p.name} ({formatPrice(p.price_cents)})</option>
                            {/each}
                        </select>
                    </div>
                </div>
            </div>

            <!-- Seção de Oferta Extra / Order Bump (Serviço Opcional) -->
            <div class="form-group order-bump-group" style="background: #f0f9ff; padding: 1.25rem; border-radius: 8px; border: 1px solid #bae6fd; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <label for="has_extra_service" style="font-weight: 700; font-size: 0.95rem; color: #0369a1; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; text-transform: none; letter-spacing: 0; margin: 0;">
                            <input type="checkbox" id="has_extra_service" name="has_extra_service" bind:checked={hasExtraService} style="width: 18px; height: 18px; accent-color: #0284c7; cursor: pointer;" />
                            ⚡ Oferecer Serviço ou Item Extra no Checkout (Order Bump)
                        </label>
                        <span style="font-size: 0.8rem; color: #0891b2; display: block; margin-top: 0.35rem; line-height: 1.4;">
                            Ofereça um serviço complementar opcional no momento da compra (ex: Instalação no servidor, suporte VIP, mentoria).
                        </span>
                    </div>
                </div>

                {#if hasExtraService}
                    <div style="margin-top: 1rem; display: flex; flex-direction: column; gap: 1rem; padding-top: 1rem; border-top: 1px dashed #7dd3fc;">
                        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1rem;">
                            <div>
                                <label for="extra_service_title" style="font-size: 0.85rem; font-weight: 600; color: #0369a1; display: block; margin-bottom: 0.3rem;">Título do Serviço / Item Extra *</label>
                                <input type="text" id="extra_service_title" name="extra_service_title" bind:value={extraServiceTitle} placeholder="Ex: Serviço de Instalação e Configuração" required={hasExtraService} style="background: #fff; border: 1px solid #7dd3fc; border-radius: 6px; padding: 0.6rem; font-size: 0.9rem; width: 100%; box-sizing: border-box;" />
                            </div>
                            <div>
                                <label for="extra_service_price_display" style="font-size: 0.85rem; font-weight: 600; color: #0369a1; display: block; margin-bottom: 0.3rem;">Valor Adicional (R$)</label>
                                <input type="text" id="extra_service_price_display" placeholder="50,00" bind:value={extraServicePriceValue} style="background: #fff; border: 1px solid #7dd3fc; border-radius: 6px; padding: 0.6rem; font-size: 0.9rem; width: 100%; box-sizing: border-box;" />
                                <input type="hidden" name="extra_service_price_cents" value={parsePrice(extraServicePriceValue)} />
                                <small style="font-size: 0.75rem; color: #0284c7; margin-top: 0.2rem; display: block;">
                                    {extraServicePriceValue ? formatPrice(parsePrice(extraServicePriceValue)) : 'R$ 0,00'}
                                </small>
                            </div>
                        </div>

                        <div>
                            <label for="extra_service_description" style="font-size: 0.85rem; font-weight: 600; color: #0369a1; display: block; margin-bottom: 0.3rem;">Descrição do Serviço (Opcional)</label>
                            <textarea id="extra_service_description" name="extra_service_description" bind:value={extraServiceDescription} rows="2" placeholder="Ex: Deixamos a aplicação instalada e rodando perfeitamente no seu servidor em até 24 horas." style="background: #fff; border: 1px solid #7dd3fc; border-radius: 6px; padding: 0.6rem; font-size: 0.9rem; width: 100%; box-sizing: border-box;"></textarea>
                        </div>
                    </div>
                {/if}
            </div>

            {#if resourceType === 'file'}
                <div class="form-group file-upload-group">
                    <label for="product_file">Arquivo Digital no Servidor (Deixe vazio para manter o atual)</label>
                    
                    {#if data.product.file_url && !isCurrentlyCloudinary}
                        <div style="margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                            <input type="checkbox" id="remove_file_checkbox" bind:checked={removeFile} onchange={() => {
                                if (removeFile) {
                                    selectedFileName = null;
                                    const input = document.getElementById('product_file') as HTMLInputElement;
                                    if (input) input.value = '';
                                }
                            }} style="width: auto; margin: 0;" />
                            <label for="remove_file_checkbox" style="font-weight: normal; cursor: pointer; margin: 0;">Remover arquivo digital atual</label>
                        </div>
                    {/if}

                    <input type="hidden" name="remove_file" value={removeFile ? "1" : "0"} />

                    {#if data.product.file_url && !isCurrentlyCloudinary && !removeFile}
                        <div class="current-file-badge">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                            </svg>
                            <span>Arquivo atual (disco): <strong>{data.product.file_url.split('/').pop()}</strong></span>
                        </div>
                    {:else if data.product.file_url && !isCurrentlyCloudinary && removeFile}
                        <div class="current-file-badge" style="background: #fef2f2; color: #991b1b; border-color: #fecaca; display: flex; justify-content: space-between; align-items: center;">
                            <span style="display: flex; align-items: center; gap: 0.5rem;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                                </svg>
                                <span>Arquivo atual: <strong style="text-decoration: line-through;">{data.product.file_url.split('/').pop()}</strong> (será removido)</span>
                            </span>
                        </div>
                    {/if}
                    <div class="file-dropzone" class:has-file={!!selectedFileName}>
                        <input type="file" id="product_file" name="product_file" accept=".pdf,.zip,.rar,.7z,.png,.jpg,.jpeg,.gif,.webp,.mp3,.mp4,.txt" onchange={(e) => {
                            const file = e.currentTarget.files?.[0];
                            selectedFileName = file ? file.name : null;
                            if (file) {
                                removeFile = false;
                            }
                        }} />
                        <div class="dropzone-text">
                            {#if selectedFileName}
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2">
                                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span class="selected-file-name">Novo arquivo selecionado: <strong>{selectedFileName}</strong></span>
                            {:else}
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                                </svg>
                                <span>Clique para selecionar um novo arquivo para substituir o atual</span>
                            {/if}
                            <span class="file-types">Formatos suportados: PDF, ZIP, RAR, 7Z, Imagens, Vídeo, Áudio (Máx. 30MB)</span>
                        </div>
                    </div>
                </div>

            {:else if resourceType === 'cloudinary'}
                <div class="form-group file-upload-group">
                    <label for="product_file">☁️ Arquivo no Cloudinary (Deixe vazio para manter o atual)</label>
                    <div class="cloudinary-info">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        Download via proxy seguro — a URL do Cloudinary nunca é exposta. Ao enviar novo arquivo, o antigo é deletado automaticamente.
                    </div>

                    {#if data.product.file_url && isCurrentlyCloudinary}
                        <div class="current-file-badge cloudinary-badge">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>
                            <span>Arquivo atual no Cloudinary — envie um novo para substituir</span>
                        </div>
                    {/if}

                    <input type="hidden" name="remove_file" value="0" />

                    <div class="file-dropzone" class:has-file={!!selectedFileName}>
                        <input type="file" id="product_file" name="product_file"
                            accept=".pdf,.zip,.rar,.7z,.txt"
                            onchange={(e) => {
                                const file = e.currentTarget.files?.[0];
                                selectedFileName = file ? file.name : null;
                            }} />
                        <div class="dropzone-text">
                            {#if selectedFileName}
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2">
                                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span class="selected-file-name">Novo arquivo: <strong>{selectedFileName}</strong> (vai substituir o atual)</span>
                            {:else}
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                                </svg>
                                <span>Clique para enviar nova versão (substitui o arquivo anterior)</span>
                            {/if}
                            <span class="file-types">Formatos: PDF, ZIP, RAR, 7Z, TXT (Máx. 100MB)</span>
                        </div>
                    </div>
                </div>

            {:else if resourceType === 'manual'}
                <!-- Entrega Manual: Drive, GitHub, Notion, etc. -->
                <div class="manual-delivery-fields">
                    <div class="manual-delivery-info">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        O comprador informará o Gmail, GitHub ou outro identificador antes de pagar. Você entrega manualmente e marca como entregue no painel de vendas.
                    </div>

                    <div class="form-group">
                        <label for="external_link">🔗 Link do Recurso (Drive/GitHub/etc.) <span class="required-mark">*</span></label>
                        <input type="url" id="external_link" name="external_link" bind:value={externalLink} placeholder="https://drive.google.com/..." required />
                        <small>⚠️ Este link é <strong>privado</strong> — nunca é exposto ao comprador. Use-o como referência para você ao compartilhar.</small>
                    </div>

                    <div class="form-group">
                        <label for="access_label">🏷️ Label do campo para o comprador</label>
                        <input type="text" id="access_label" name="access_label" bind:value={accessLabel} placeholder="Ex: Seu Gmail, Seu usuário do GitHub..." />
                        <small>Texto exibido ao comprador pedindo o identificador. Ex: "Seu Gmail para receber o acesso".</small>
                    </div>

                    <div class="form-group">
                        <label for="drive_instructions">📝 Instruções pós-compra</label>
                        <textarea id="drive_instructions" name="drive_instructions" rows="3" bind:value={driveInstructions} placeholder="Ex: Após o pagamento confirmado, compartilharemos o acesso em até 24h no Gmail informado."></textarea>
                        <small>Texto exibido ao comprador após a compra (na página do produto).</small>
                    </div>

                    <div class="form-group">
                        <label for="delivery_deadline">⏱️ Prazo estimado de entrega</label>
                        <input type="text" id="delivery_deadline" name="delivery_deadline" bind:value={deliveryDeadline} placeholder="Ex: até 24h, até 48h, imediato..." />
                        <small>Exibido ao comprador enquanto aguarda o compartilhamento.</small>
                    </div>
                </div>

            {:else}
                <div class="form-group">
                    <label for="external_link">Link Externo</label>
                    <input type="url" id="external_link" name="external_link" bind:value={externalLink} placeholder="https://exemplo.com/recurso" required />
                    <small>Insira a URL completa (incluindo https://) para redirecionamento do download.</small>
                </div>
            {/if}

        </div>

        {#if form?.message}
            <div class="alert error">{form.message}</div>
        {/if}

        <div class="section-divider"></div>

        <div class="form-section notify-box">
            <div class="form-group" style="display: flex; align-items: flex-start; gap: 0.6rem; margin-bottom: 0.5rem;">
                <input type="checkbox" id="notify_buyers" name="notify_buyers" value="on" bind:checked={notifyBuyers} style="width: auto; margin: 0.2rem 0 0 0; cursor: pointer;" />
                <div>
                    <label for="notify_buyers" style="font-weight: 600; cursor: pointer; margin: 0; text-transform: none; letter-spacing: 0; font-size: 0.9rem;">
                        Notificar compradores por e-mail sobre esta atualização
                    </label>
                    <small style="display: block; color: var(--text-muted); margin-top: 0.25rem; line-height: 1.4;">
                        Envia via <strong>Resend</strong> para quem comprou o produto (status pago) e, se for recurso Premium, para assinantes ativos.
                        Exige API key e e-mail From em <a href="/admin/settings">Configurações → Resend</a>.
                    </small>
                </div>
            </div>

            {#if notifyBuyers}
                <div class="form-group" style="margin-top: 1rem;">
                    <label for="update_message">O que mudou nesta versão? (opcional)</label>
                    <textarea 
                        id="update_message" 
                        name="update_message" 
                        bind:value={updateMessage}
                        rows="3" 
                        placeholder="Ex: Corrigimos o bug de scroll e adicionamos a pasta de documentação..."
                    ></textarea>
                </div>
            {/if}
        </div>

        <div class="form-actions">
            <a href="/admin/products" class="btn">{t(lang, "admin.ui.cancel")}</a>
            <button type="submit" class="btn btn-primary" disabled={loading}>
                {loading ? t(lang, "admin.ui.saving") : t(lang, "admin.ui.save_changes")}
            </button>
        </div>
    </form>
</div>

<style>
    .edit-product-page {
        max-width: 700px;
        margin: 0 auto;
    }

    .page-header {
        margin-bottom: 2rem;
    }

    h1 {
        font-family: var(--font-sans);
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: var(--text-primary);
    }

    .subtitle {
        color: var(--text-muted);
    }

    .product-form {
        background: var(--bg-primary);
        padding: 2rem;
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-color);
    }

    .form-section {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .form-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
    }

    label {
        font-weight: 500;
        color: var(--text-primary);
        font-size: 0.875rem;
    }

    input[type="text"], input[type="url"], select, textarea {
        width: 100%;
        padding: 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        font-family: var(--font-sans);
        transition: border-color var(--transition-fast);
    }

    input:focus, select:focus, textarea:focus {
        outline: none;
        border-color: var(--text-primary);
    }

    .price-input-group {
        position: relative;
        display: flex;
        align-items: center;
    }

    .price-input-group input {
        padding-left: 2.5rem;
    }

    .input-suffix {
        position: absolute;
        left: 0.75rem;
        color: var(--text-muted);
        font-weight: 500;
    }

    .current-file-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
        border-radius: var(--radius-md);
        font-size: 0.8rem;
        margin-bottom: 0.5rem;
    }

    .file-input {
        width: 100%;
        padding: 0.5rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        font-family: var(--font-sans);
        font-size: 0.875rem;
    }

    .file-input::file-selector-button {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        padding: 0.375rem 0.75rem;
        border-radius: var(--radius-sm);
        cursor: pointer;
        margin-right: 0.75rem;
        font-weight: 500;
        font-family: var(--font-sans);
        transition: background var(--transition-fast), border-color var(--transition-fast);
    }

    .file-input::file-selector-button:hover {
        background: var(--bg-secondary);
        border-color: var(--text-muted);
    }

    .image-preview-container {
        position: relative;
        display: inline-flex;
        align-items: center;
        gap: 1rem;
        padding: 0.5rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        margin-bottom: 0.5rem;
        width: fit-content;
    }

    .image-preview {
        width: 80px;
        height: 80px;
        object-fit: cover;
        border-radius: var(--radius-sm);
        border: 1px solid var(--border-color);
    }

    .preview-badge {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .btn-remove-image {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        border-radius: var(--radius-sm);
        cursor: pointer;
        font-weight: 500;
        transition: background 0.2s ease;
    }

    .btn-remove-image:hover {
        background: #fee2e2;
    }

    .file-upload-group {
        margin-top: 0.5rem;
    }

    .file-dropzone {
        position: relative;
        border: 2px dashed var(--border-color);
        border-radius: var(--radius-lg);
        padding: 2rem;
        text-align: center;
        background: var(--bg-secondary);
        cursor: pointer;
        transition: border-color 0.2s ease;
    }

    .file-dropzone:hover {
        border-color: var(--text-secondary);
    }

    .file-dropzone input[type="file"] {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0;
        cursor: pointer;
    }

    .dropzone-text {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        color: var(--text-secondary);
        pointer-events: none;
    }

    .dropzone-text svg {
        color: var(--text-muted);
    }

    .file-types {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .section-divider {
        height: 1px;
        background: var(--border-light);
        margin: 1.5rem 0;
    }

    .form-actions {
        margin-top: 2rem;
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
    }

    .alert {
        padding: 1rem;
        border-radius: var(--radius-md);
        margin-top: 1.5rem;
        font-size: 0.875rem;
    }

    .error {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
    }

    small {
        color: var(--text-muted);
        font-size: 0.75rem;
    }

    .free-info {
        color: #059669;
    }

    @media (max-width: 640px) {
        .form-row {
            grid-template-columns: 1fr;
        }
    }

    .file-dropzone.has-file {
        border-color: #22c55e;
        background: rgba(34, 197, 94, 0.05);
    }

    .selected-file-name {
        color: #166534;
        font-weight: 600;
        font-size: 0.95rem;
    }

    .cloudinary-info {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        padding: 0.65rem 0.85rem;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: var(--radius-md);
        color: #1d4ed8;
        font-size: 0.8rem;
        line-height: 1.4;
        margin-bottom: 0.5rem;
    }

    .cloudinary-info svg {
        flex-shrink: 0;
        margin-top: 1px;
    }

    .cloudinary-badge {
        background: #eff6ff;
        border-color: #bfdbfe;
        color: #1d4ed8;
    }
</style>
