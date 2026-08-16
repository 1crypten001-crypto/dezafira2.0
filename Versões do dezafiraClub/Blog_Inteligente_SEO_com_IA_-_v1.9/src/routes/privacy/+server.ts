import type { RequestHandler } from './$types';

const privacy = `
# Política de Privacidade

**Última atualização:** ${new Date().toLocaleDateString('pt-BR')}

## 1. Introdução

Respeitamos sua privacidade e estamos comprometidos em proteger seus dados 
pessoais. Esta política explica como coletamos, usamos e protegemos suas informações.

## 2. Coleta de Dados

### Dados que coletamos:

- **Dados de navegação**: páginas visitadas, tempo de permanência
- **Cookies**: preferências, analytics
- **Formulários**: nome, e-mail ao comentar ou se inscrever

### Não coletamos:

- Dados de cartão de crédito
- Senhas de outras contas
- Informações sensíveis

## 3. Uso dos Dados

Utilizamos seus dados para:

- Melhorar a experiência do usuário
- Enviar newsletters (com seu consentimento)
- Analisar tráfego do site
- Responder a contatos

## 4. Cookies

Utilizamos cookies para:

- Lembrar suas preferências
- Analytics (Google Analytics ou similar)
- Publicidade (se aplicável)

Você pode desativar cookies nas configurações do seu navegador.

## 5. Compartilhamento

Não vendemos, trocamos ou transferimos seus dados pessoais para terceiros, 
exceto:

- Quando exigido por lei
- Para proteger nossos direitos
- Com provedores de serviços confiáveis

## 6. Armazenamento

Seus dados são armazenados em servidores seguros. Mantemos apenas os 
dados necessários pelo tempo requerido.

## 7. Seus Direitos

Você tem direito a:

- Solicitar acesso aos seus dados
- Pedir correção de dados incorretos
- Solicitar exclusão de seus dados
- Cancelar inscrição da newsletter

## 8. Segurança

Implementamos medidas de segurança técnicas e organizacionais para proteger 
seus dados contra acesso não autorizado.

## 9. Crianças

Nosso site não é direcionado a crianças menores de 13 anos. Não coletamos 
intencionalmente dados de crianças.

## 10. Alterações

Esta política pode ser atualizada periodicamente. Notificaremos sobre 
alterações significativas através do site.

## 11. Contato

Para questões sobre esta política, entre em contato:

- E-mail: privacidade@blog.com
- Página: /contact
`;

export const POST: RequestHandler = async () => {
  return new Response(privacy, {
    status: 405,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8'
    }
  });
};
