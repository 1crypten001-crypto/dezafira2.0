# Área de Membros, Cursos e Integração com Asaas

A Área de Membros permite monetizar o blog por meio de venda de cursos individuais ou assinaturas premium completas.

---

## 🎓 Modelos de Acesso de Cursos

Cada curso criado pelo administrador no painel possui um tipo de acesso definido:

1. **Gratuito (`free`)**: Qualquer usuário logado (com cadastro de membro padrão no blog) pode assistir a todas as aulas.
2. **Premium (`premium`)**: Restrito a assinantes premium ativos que possuem uma assinatura recorrente ativa no blog.
3. **Pago (`paid`)**: Acesso disponível para assinantes premium **OU** para usuários que realizarem a compra avulsa do curso pelo valor (em centavos de Real) definido pelo administrador.

---

## 🎥 Segurança e Proteção de Vídeos

Para evitar piracy ou downloads não autorizados, as URLs brutas do YouTube ou Vimeo contendo as aulas **nunca são enviadas ao navegador do cliente**.

### Funcionamento da Proteção:
1. No painel de administração, as aulas são cadastradas informando a URL original (ex: `https://www.youtube.com/watch?v=XXXXXX`).
2. O frontend do curso, ao carregar uma aula protegida, não recebe o link do vídeo. Ele apenas renderiza o esqueleto da página e exibe um player de carregamento.
3. O cliente faz uma requisição fetch interna para o endpoint seguro `/api/members/lesson/[id]/video`.
4. O servidor do endpoint intercepta a requisição, analisa a sessão ativa e confere as regras de acesso do curso associado:
   * Se for uma aula marcada como **Preview**, o acesso é liberado de imediato.
   * Se for um curso **Gratuito**, confirma se o usuário está logado.
   * Se for um curso **Premium** ou **Pago**, confere se o usuário é assinante ativo ou se possui um registro de compra aprovado para aquele curso específico na tabela `course_purchases`.
5. Caso o acesso seja validado, o servidor extrai e retorna apenas o ID do vídeo (ou gera uma assinatura temporária) em JSON. Se o acesso for inválido, retorna `403 Forbidden` ou `401 Unauthorized`.

---

## 💳 Fluxo de Compra Avulsa de Cursos (Asaas)

Quando um curso é classificado como `paid` (Pago) e o usuário logado não possui assinatura ativa nem comprou o curso ainda:

1. É apresentado um botão de compra na página do curso.
2. Clicar no botão aciona a criação de uma ordem de cobrança na API do Asaas e gera um registro local na tabela `course_purchases` com status `pending`.
3. O usuário é redirecionado para o link de checkout do Asaas (onde pode realizar pagamento via Pix, Cartão de Crédito ou Boleto).
4. **Processamento do Webhook**:
   * O blog expõe o endpoint de recebimento de notificações de webhook em `/api/webhook/asaas`.
   * Quando o pagamento é aprovado, o Asaas envia uma requisição do tipo `PAYMENT_RECEIVED` ou `PAYMENT_CONFIRMED`.
   * O manipulador do webhook identifica o ID do pagamento, localiza o registro correspondente no banco de dados do blog e atualiza o status de `pending` para `approved`.
   * O acesso ao curso é liberado imediatamente para o membro.
