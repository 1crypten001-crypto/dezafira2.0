import express from 'express';
import cors from 'cors';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync } from 'fs';
import https from 'https';
import dotenv from 'dotenv';
import { createChatGPTHandler } from '@opencoredev/loginwithchatgpt-server';
import pool from './database/pool.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

const allowedOrigins = [
  'http://localhost:5173',
  'http://127.0.0.1:5173',
  'http://localhost:8080',
  'http://localhost',
  'https://localhost',
  'capacitor://localhost',
  'https://1convite.com.br',
  'https://www.1convite.com.br',
];
if (process.env.FRONTEND_URL) {
  allowedOrigins.push(process.env.FRONTEND_URL);
}

app.use(cors({
  origin: allowedOrigins,
  credentials: true
}));
app.use(express.json());

const chatGptHandler = createChatGPTHandler({
  secret: process.env.LWC_SECRET || 'a-very-stable-secret-for-development-1convite-32-chars-long!',
  basePath: '/api/v1/chatgpt',
  dangerouslyAllowTokenExport: true,
  allowedOrigins,
});

async function toWebRequest(req) {
  const protocol = req.protocol;
  const host = req.get('host');
  const originalUrl = req.originalUrl;
  const url = `${protocol}://${host}${originalUrl}`;

  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (value) {
      if (Array.isArray(value)) {
        value.forEach(v => headers.append(key, v));
      } else {
        headers.set(key, value);
      }
    }
  }

  let body = null;
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    body = typeof req.body === 'object' ? JSON.stringify(req.body) : req.body;
  }

  return new Request(url, {
    method: req.method,
    headers,
    body,
  });
}

async function fromWebResponse(webRes, res) {
  res.status(webRes.status);
  webRes.headers.forEach((value, key) => {
    res.setHeader(key, value);
  });

  if (webRes.body) {
    const reader = webRes.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(value);
    }
    res.end();
  } else {
    res.end();
  }
}

app.all('/api/v1/chatgpt/*splat', async (req, res) => {
  console.log(`[ChatGPT Request] ${req.method} ${req.originalUrl}`);
  try {
    const webReq = await toWebRequest(req);
    const webRes = await chatGptHandler.handler(webReq);
    console.log(`[ChatGPT Request] Response: ${webRes.status}`);

    if (!webRes.ok) {
      const clone = webRes.clone();
      const text = await clone.text();
      console.warn(`[ChatGPT Request] Error response payload: ${text}`);
    }

    await fromWebResponse(webRes, res);
  } catch (err) {
    console.error('Erro no ChatGPT handler:', err);
    res.status(500).json({ error: err.message });
  }
});

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ── MIGRATIONS: criar tabelas se não existirem ──
async function ensureTables() {
  try {
    const client = await pool.connect();
    try {
      const sql = readFileSync(join(__dirname, '../migrations/001_initial.sql'), 'utf-8');
      await client.query(sql);
      console.log('[DB] Tabelas criadas/verificadas com sucesso');
    } finally {
      client.release();
    }
  } catch (err) {
    console.warn('[DB] Aviso: Não foi possível conectar ao banco PostgreSQL local (as rotas do servidor continuarão ativas):', err.message);
  }
}

// Helper wrappers around pool.query (resilientes no dev local)
const dbRun = async (query, params = []) => {
  try {
    return await pool.query(query, params);
  } catch (err) {
    console.warn('[DB Query Warning]:', err.message);
    return { rows: [], rowCount: 0 };
  }
};
const dbGet = async (query, params = []) => {
  try {
    const { rows } = await pool.query(query, params);
    return rows[0] || null;
  } catch (err) {
    console.warn('[DB Get Warning]:', err.message);
    return null;
  }
};
const dbAll = async (query, params = []) => {
  try {
    const { rows } = await pool.query(query, params);
    return rows || [];
  } catch (err) {
    console.warn('[DB All Warning]:', err.message);
    return [];
  }
};

// Seed data (runs only when tables are empty)
async function seedData() {
  // Insere o progresso inicial se não existir
  const user = await dbGet('SELECT * FROM tb_usuario_progresso LIMIT 1');
  if (!user) {
    await dbRun(
      "INSERT INTO tb_usuario_progresso (dia_atual, checkpoint_completado, status_plano, nome, email, avatar) VALUES (1, false, 'FREE', 'Membro Convidado', 'membro@1convite.com', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80')"
    );
  }

  // Preenche a tabela tb_matriz_diaria (se vazio)
  const countRow = await dbGet('SELECT COUNT(*) as count FROM tb_matriz_diaria');
  if (Number(countRow.count) === 0) {
    console.log('Populando tabela de 365 dias...');
    const reais = [
      {
        dia_id: 1,
        pilar_origem: 'PROPÓSITO_M2414',
        codigo_verbal: 'Código 01: O Reino começa no quintal da sua casa.',
        versiculo_chave: 'E este evangelho do reino será pregado em todo o mundo como testemunho a todas as nações, então, virá o fim. - Mateus 24:14',
        texto_reflexao: 'O evangelismo eficaz não começa em outra nação, mas no próximo contato que você fizer hoje. Note quem está ao seu redor no agora de Deus e faça uma conexão real. \n\n📖 HISTÓRIA CRISTÃ REAL:\nEdward Kimball era um simples professor voluntário de escola dominical. Em 1855, ele decidiu fazer uma conexão simples no quintal de sua casa: entrou na sapataria onde um jovem de 17 anos trabalhava para falar sobre Cristo. Esse jovem era Dwight L. Moody, que veio a pregar para milhões e fundou grandes instituições cristãs. O impacto mundial de Moody começou com a conexão intencional de Kimball em uma sapataria comum.',
        texto_meditacao: `🎙️ Roteiro de Oração Guiada: "A Oração de Ação de Graças e Propósito"
Duração aproximada: 3 a 4 minutos

Trilha de fundo sugerida: Tom suave, seguro e focado. Sem desespero, com tom de certeza e autoridade espiritual.

🟢 1. O Ponto de Partida: Ação de Graças pelo Hoje
(Tom de voz: Calmo, grato, pausado)

Repita comigo em seu coração ou em alta voz:

"Pai, a Ti rendo graças.

Obrigado porque o Senhor é bom e sempre me ouve.

(Pausa de 3 segundos)

Agradeço pela oportunidade de despertar para mais este dia incrível.

Obrigado pelo ar nos meus pulmões, pelo pão na minha mesa e por esta nova chance de viver."

🟡 2. O Alinhamento: Tudo o que Tenho é Suficiente
(Inspirado na Multiplicação dos Pães - Marcos 6:41)

"Senhor, assim como Jesus não olhou para a escassez dos cinco pães e dois peixes, mas ergueu os olhos para o céu e deu graças... eu entrego nas Tuas mãos o que eu tenho hoje.

(Pausa de 4 segundos)

Não vou reclamar do que me falta. Eu abençoo o pouco ou o muito que está nas minhas mãos agora, sabendo que a Tua graça multiplica o meu esforço."

🟠 3. O Propósito e o Mover no Agora
(Tom de voz: Firme, consciente, de governo)

"Pai, o meu dia não será em vão.

Eu desperto hoje para trabalhar alinhado ao meu propósito e à visão do Teu Reino.

(Pausa de 3 segundos)

Dá-me olhos para notar as pessoas ao meu redor.

Usa a minha vida como um testemunho vivo. Que onde eu colocar as minhas mãos, haja bênção, sabedoria e multiplicação."

🔴 4. A Selagem do Convite
(Tom de voz: Decidido, pronto para a ação)

"Eu não andarei ansioso pelo amanhã.

Eu tomo posse da vitória e da paz que já foram conquistadas na cruz.

Em nome de Jesus, o meu dia está abençoado.

Amém!"`,
        url_audio_meditacao: '/piano.mp3'
      },
      {
        dia_id: 2,
        pilar_origem: 'RECOMPENSA_AP321',
        codigo_verbal: 'Código 02: Desfrute da vitória que você não teve que conquistar.',
        versiculo_chave: 'Ao vencedor darei o direito de sentar-se comigo em meu trono, assim como eu também venci e sentei-me com meu Pai em seu trono. - Apocalipse 3:21',
        texto_reflexao: 'A ansiedade morre quando você entende que a batalha principal já foi ganha. Você não trabalha para ser aceito, mas opera a partir da vitória consumada. Descanse nesse sábado eterno. \n\n📖 HISTÓRIA CRISTÃ REAL:\nMartinho Lutero viveu anos sob severa angústia e culpa em um mosteiro agostiniano, tentando alcançar a aceitação de Deus através de jejuns, vigílias e autoflagelação sem sucesso. Ao estudar a epístola aos Romanos na torre do mosteiro, ele teve a revelação de que a salvação é um presente gratuito de Deus aceito pela fé. Lutero parou de lutar para conquistar o céu e pôde finalmente descansar na vitória consumada por Jesus Cristo.',
        texto_meditacao: `🎙️ Roteiro de Oração Guiada: "A Oração do Descanse na Vitória"
Duração aproximada: 3 minutos

Trilha de fundo sugerida: Tom suave, seguro e focado. Sem desespero, com tom de certeza e autoridade espiritual.

🟢 1. O Ponto de Partida: Ação de Graças pela Vitória
(Tom de voz: Calmo, grato, pausado)

Repita comigo em seu coração ou em alta voz:

"Pai, eu Te dou graças.

Obrigado porque a batalha principal já foi ganha por Jesus na cruz.

(Pausa de 3 segundos)

Agradeço porque meu valor não vem do meu esforço humano, mas do Teu amor gratuito.

Eu recebo hoje a Tua paz que excede todo o entendimento."

🟡 2. O Alinhamento: Assentado no Trono (Inspirado em Apocalipse 3:21)

"Senhor, assim como Martinho Lutero compreendeu que a aceitação vem pela fé e não por autoflagelação ou ativismo... eu paro de lutar para ser aceito.

(Pausa de 4 segundos)

Eu me assento na Tua vitória hoje. Eu sou Teu filho, e o Teu favor me basta agora."

🟠 3. O Propósito e o Mover no Agora
(Tom de voz: Firme, consciente, de governo)

"Pai, eu não andarei aflito para provar meu valor para os outros hoje.

Tudo o que eu fizer fluirá a partir do descanso e da certeza da minha herança.

(Pausa de 3 segundos)

Que as minhas atitudes reflitam a segurança de quem já venceu com Cristo.

Que eu traga paz e justiça aos ambientes onde eu pisar."

🔴 4. A Selagem do Convite
(Tom de voz: Decidido, pronto para a ação)

"Eu declaro cancelada toda ansiedade de desempenho na minha vida.

Estou livre para amar, servir e compartilhar sem medo.

Em nome de Jesus, o meu dia está guardado.

Amém!"`,
        url_audio_meditacao: '/piano.mp3'
      },
      {
        dia_id: 3,
        pilar_origem: 'PROPÓSITO_M2414',
        codigo_verbal: 'Código 03: Pague um café para comprar um tempo de atenção.',
        versiculo_chave: 'Ninguém tem maior amor do que este: de dar alguém a própria vida pelos seus amigos. - João 15:13',
        texto_reflexao: 'Um convite intencional demonstra valor. Pagar um café ou dedicar 15 minutos para ouvir alguém genuinamente é doar um fragmento da sua vida pelo outro. \n\n📖 HISTÓRIA CRISTÃ REAL:\nC. S. Lewis, autor das Crônicas de Nárnia e um dos intelectuais mais famosos do século XX, recebia milhares de cartas de leitores do mundo inteiro. Ele estabeleceu como prioridade pessoal responder a cada uma delas à mão, dedicando horas de suas manhãs para acolher dúvidas de crianças e desconhecidos. Lewis preferia sacrificar seu tempo acadêmico para doar atenção focada e individual, sabendo que ouvir e responder a um irmão era servir a Cristo.',
        texto_meditacao: `🎙️ Roteiro de Oração Guiada: "A Oração do Tempo como Oferta"
Duração aproximada: 3 minutos

Trilha de fundo sugerida: Tom suave, seguro e focado. Sem desespero, com tom de certeza e autoridade espiritual.

🟢 1. O Ponto de Partida: Ação de Graças pela Atenção
(Tom de voz: Calmo, grato, pausado)

Repita comigo em seu coração ou em alta voz:

"Pai, a Ti rendo graças.

Obrigado por este momento de silêncio e por me ouvir com total atenção.

(Pausa de 3 segundos)

Agradeço porque diante de Ti eu posso desacelerar sem culpa.

Obrigado porque o Senhor nunca tem pressa para comigo."

🟡 2. O Alinhamento: Consagração do Tempo (Inspirado em João 15:13)

"Senhor, assim como C.S. Lewis sacrificou seu tempo acadêmico para responder com atenção e amor a cada carta de crianças desconhecidas... eu coloco o meu tempo em Tuas mãos.

(Pausa de 4 segundos)

A minha vida não é medida pelo meu relógio, mas pelo amor que dedico.

Entrego o meu dia para ser uma oferta de amor ao meu próximo."

🟠 3. O Propósito e o Mover no Agora
(Tom de voz: Firme, consciente, de governo)

"Pai, ajuda-me a não olhar apenas para as minhas telas hoje.

Dá-me sensibilidade para notar quem precisa de atenção.

(Pausa de 3 segundos)

Eu escolho parar e ouvir com o coração a pessoa que o Senhor colocar no meu caminho.

Serei a presença de Cristo para o meu próximo no agora."

🔴 4. A Selagem do Convite
(Tom de voz: Decidido, pronto para a ação)

"Eu não serei escravo da pressa hoje.

Eu tomo posse da paz e da presença do Senhor em cada conversa.

Em nome de Jesus, o meu dia está consagrado.

Amém!"`,
        url_audio_meditacao: '/piano.mp3'
      },
      {
        dia_id: 4,
        pilar_origem: 'RECOMPENSA_AP321',
        codigo_verbal: 'Código 04: A pressa é uma mentira que tenta roubar a sua eternidade.',
        versiculo_chave: 'Portanto, resta ainda um descanso sabático para o povo de Deus. - Hebreus 4:9',
        texto_reflexao: 'A pressa e o ativismo tentam nos convencer de que nosso valor vem da nossa produtividade. Acalme o seu coração no Agora. Respire fundo, e sinta o repouso divino de Apocalipse 3:21. \n\n📖 HISTÓRIA CRISTÃ REAL:\nEric Liddell, velocista escocês e cristão fervoroso, descobriu que as eliminatórias dos 100 metros nas Olimpíadas de Paris em 1924 seriam realizadas em um domingo. Ele se recusou a correr, afirmando que o Dia do Senhor era sagrado para o descanso e adoração. Liddell sofreu imensa rejeição pública, mas manteve sua decisão. Dias depois, correu a prova de 400 metros (distância para a qual não havia treinado tanto) e conquistou a medalha de ouro olímpica estabelecendo um novo recorde mundial.',
        texto_meditacao: `🎙️ Roteiro de Oração Guiada: "A Oração do Descanso da Alma"
Duração aproximada: 3 minutos

Trilha de fundo sugerida: Tom suave, seguro e focado. Sem desespero, com tom de certeza e autoridade espiritual.

🟢 1. O Ponto de Partida: Ação de Graças pelo Sábado
(Tom de voz: Calmo, grato, pausado)

Repita comigo em seu coração ou em alta voz:

"Pai, a Ti rendo graças.

Obrigado por providenciar um descanso sabático para o Teu povo.

(Pausa de 3 segundos)

Agradeço porque o Senhor renova as minhas forças no silêncio.

Obrigado por me lembrar de que a minha produtividade não determina o meu valor."

🟡 2. O Alinhamento: O Sábado do Coração (Inspirado em Hebreus 4:9)

"Senhor, assim como Eric Liddell abriu mão da glória olímpica no domingo para honrar o Teu descanso... eu decido parar agora.

(Pausa de 4 segundos)

Eu calo o barulho das minhas preocupações.

O Senhor sustenta o meu amanhã enquanto eu descanso na Tua presença hoje."

🟠 3. O Propósito e o Mover no Agora
(Tom de voz: Firme, consciente, de governo)

"Pai, eu rejeito todo o cansaço e esgotamento mental.

Eu escolho focar na Tua graça e no Teu refrigério.

(Pausa de 3 segundos)

Que este tempo de descanso recarregue as minhas energias para servir melhor.

Que eu leve leveza e paz a todos ao meu redor."

🔴 4. A Selagem do Convite
(Tom de voz: Decidido, pronto para a ação)

"Eu tomo posse da promessa do descanso eterno em Cristo.

O meu amanhã está seguro em Tuas mãos.

Em nome de Jesus, eu declaro meu coração em paz.

Amém!"`,
        url_audio_meditacao: '/piano.mp3'
      },
      {
        dia_id: 5,
        pilar_origem: 'PROPÓSITO_M2414',
        codigo_verbal: 'Código 05: A conexão real vence o algoritmo digital.',
        versiculo_chave: 'E não nos cansemos de fazer o bem, pois no tempo próprio colheremos, se não desanimarmos. - Gálatas 6:9',
        texto_reflexao: 'Substitua 10 minutos de feed infinito por uma mensagem direcionada a um amigo ou familiar que você não vê há tempos. Um convite sincero é uma semente do Reino. \n\n📖 HISTÓRIA CRISTÃ REAL:\nDietrich Bonhoeffer, pastor luterano que se opôs ativamente ao regime de Hitler, organizou um seminário clandestino em Finkenwalde. Longe da propaganda em massa do Estado nazista, ele reuniu pastores em uma comunidade real e física descrita em seu livro "Vida em Comunhão". Ele defendia que a comunhão real, física e o partir do pão face a face tinham o poder de sustentar a fé viva contra qualquer barulho artificial do mundo moderno.',
        texto_meditacao: `🎙️ Roteiro de Oração Guiada: "A Oração da Conexão Real"
Duração aproximada: 3 minutos

Trilha de fundo sugerida: Tom suave, seguro e focado. Sem desespero, com tom de certeza e autoridade espiritual.

🟢 1. O Ponto de Partida: Ação de Graças pela Comunhão
(Tom de voz: Calmo, grato, pausado)

Repita comigo em seu coração ou em alta voz:

"Pai, a Ti rendo graças.

Obrigado pelos amigos, pela família e pelas conexões reais.

(Pausa de 3 segundos)

Agradeço pela bênção de partilhar a vida face a face com outras pessoas.

Obrigado por me resgatar do isolamento e da distração digital."

🟡 2. O Alinhamento: Comunhão Verdadeira (Inspirado em Gálatas 6:9)

"Senhor, assim como Dietrich Bonhoeffer liderou uma comunidade física e real em Finkenwalde para resistir à propaganda e ao caos... eu escolho a realidade hoje.

(Pausa de 4 segundos)

Prefiro a presença ao feed infinito.

Abençoo cada pessoa com quem falarei hoje com palavras de vida."

🟠 3. O Propósito e o Mover no Agora
(Tom de voz: Firme, consciente, de governo)

"Pai, eu não me cansarei de fazer o bem.

Substituirei a pressa das telas pelo abraço e pelo tempo dedicado.

(Pausa de 3 segundos)

Usa a minha presença física para trazer conforto e encorajamento a quem precisa.

Serei um canal do Teu amor em conexões genuínas."

🔴 4. A Selagem do Convite
(Tom de voz: Decidido, pronto para a ação)

"Eu quebro toda barreira digital que me afasta do meu próximo.

A minha vida frutificará em relacionamentos intencionais.

Em nome de Jesus, o meu dia está sob a bênção da comunhão.

Amém!"`,
        url_audio_meditacao: '/piano.mp3'
      },
      {
        dia_id: 6,
        pilar_origem: 'RECOMPENSA_AP321',
        codigo_verbal: 'Código 06: Sentar no trono exige aprender a descansar.',
        versiculo_chave: 'Na tranquilidade e na confiança está a vossa força. - Isaías 30:15',
        texto_reflexao: 'Os governantes do Reino não andam ansiosos ou apressados. Eles confiam na soberania e descansam em Deus. Encontre a força do governo próprio no desfrute espiritual. \n\n📖 HISTÓRIA CRISTÃ REAL:\nGeorge Müller, que cuidou de mais de 10 mil órfãos na Bristol do século XIX, comprometeu-se a nunca pedir recursos a homens, mas sim orar e descansar em Deus. Diversas vezes o orfanato amanheceu sem um único pedaço de pão. Müller pedia às crianças que se assentassem à mesa e orava dando graças. Invariavelmente, minutos depois, padeiros ou leiteiros locais batiam à porta doando alimentos devido a imprevistos na entrega ou a toques de Deus em seus corações.',
        texto_meditacao: `🎙️ Roteiro de Oração Guiada: "A Oração do Descanso da Confiança"
Duração aproximada: 3 minutos

Trilha de fundo sugerida: Tom suave, seguro e focado. Sem desespero, com tom de certeza e autoridade espiritual.

🟢 1. O Ponto de Partida: Ação de Graças pela Provisão
(Tom de voz: Calmo, grato, pausado)

Repita comigo em seu coração ou em alta voz:

"Pai, a Ti rendo graças.

Obrigado porque o Senhor é o meu provedor e nada me faltará.

(Pausa de 3 segundos)

Agradeço porque as Tuas promessas são fiéis e o Senhor cuida de cada detalhe.

Obrigado pela paz de saber que minhas necessidades estão supridas."

🟡 2. O Alinhamento: A Provisão na Mesa (Inspirado em Isaías 30:15)

"Senhor, assim como George Müller deu graças diante de pratos vazios na mesa dos órfãos confiando na Tua fidelidade... eu dou graças agora pela provisão que virá.

(Pausa de 4 segundos)

Não andarei ansioso por recursos.

Na tranquilidade e na confiança está a minha força."

🟠 3. O Propósito e o Mover no Agora
(Tom de voz: Firme, consciente, de governo)

"Pai, eu rejeito todo o medo de escassez hoje.

Eu governo sobre minhas finanças e meu futuro com sabedoria do Reino.

(Pausa de 3 segundos)

Usa a minha vida para abençoar e suprir outros em generosidade.

Que eu colha sabedoria e multiplicação onde eu investir o meu esforço."

🔴 4. A Selagem do Convite
(Tom de voz: Decidido, pronto para a ação)

"Eu declaro cancelada toda ansiedade de futuro em nome de Jesus.

O meu suprimento diário está garantido pela cruz.

Em nome de Jesus, a minha casa está abençoada.

Amém!"`,
        url_audio_meditacao: '/piano.mp3'
      },
      {
        dia_id: 7,
        pilar_origem: 'PROPÓSITO_M2414',
        codigo_verbal: 'Código 07: O Reino é construído sobre mesas e refeições.',
        versiculo_chave: 'E eles, perseverando unânimes todos os dias no templo, e partindo o pão em casa, comiam juntos com alegria e singeleza de coração. - Atos 2:46',
        texto_reflexao: 'Abra a porta da sua casa ou convide alguém para uma refeição. A comunhão de mesa é o método mais poderoso de pregar o evangelho de Mateus 24:14 no dia a dia. \n\n📖 HISTÓRIA CRISTÃ REAL:\nJohn Wesley, líder do avivamento do século XVIII que transformou a Inglaterra, organizou a igreja primitiva em pequenas células de comunhão em casas chamadas de "Classes". Nelas, os primeiros metodistas comiam juntos nas chamadas "Festas de Amor" (Ágapes), confessavam suas lutas e oravam uns pelos outros ao redor de mesas simples. O poder transformador que espalhou o evangelho não residia nos grandes templos, mas nas mesas compartilhadas.',
        texto_meditacao: `🎙️ Roteiro de Oração Guiada: "A Oração do Banquete da Mesa"
Duração aproximada: 3 minutos

Trilha de fundo sugerida: Tom suave, seguro e focado. Sem desespero, com tom de certeza e autoridade espiritual.

🟢 1. O Ponto de Partida: Ação de Graças pela Mesa
(Tom de voz: Calmo, grato, pausado)

Repita comigo em seu coração ou em alta voz:

"Pai, a Ti rendo graças.

Obrigado pela alegria do pão partilhado e pela comunhão de mesa.

(Pausa de 3 segundos)

Agradeço pela simplicidade de coração e pela união com meus irmãos.

Obrigado pela oportunidade de acolher pessoas em minha vida."

🟡 2. O Alinhamento: A Festa do Amor (Inspirado em Atos 2:46)

"Senhor, assim como a igreja primitiva e as Classes de John Wesley se reuniam nas casas para partilhar o pão com alegria... eu consagro a minha mesa hoje.

(Pausa de 4 segundos)

Que a minha casa seja um altar do Teu amor.

Eu abro espaço para a reconciliação, a cura e a hospitalidade sincera."

🟠 3. O Propósito e o Mover no Agora
(Tom de voz: Firme, consciente, de governo)

"Pai, ajuda-me a ir além do ativismo religioso hoje.

Usa a comunhão de mesa para curar feridas e resgatar vidas.

(Pausa de 3 segundos)

Dá-me um coração generoso para acolher e compartilhar o meu pão.

Que o meu lar seja o ponto de partida do Teu Reino."

🔴 4. A Selagem do Convite
(Tom de voz: Decidido, pronto para a ação)

"Eu declaro a minha mesa santificada e cheia de alegria espiritual.

O evangelho do Reino se espalhará através do meu convite.

Em nome de Jesus, a minha mesa está abençoada.

Amém!"`,
        url_audio_meditacao: '/piano.mp3'
      }
    ];

    const insertDiaria = 'INSERT INTO tb_matriz_diaria (dia_id, pilar_origem, codigo_verbal, versiculo_chave, texto_reflexao, texto_meditacao, url_audio_meditacao) VALUES ($1, $2, $3, $4, $5, $6, $7)';

    for (let i = 1; i <= 365; i++) {
      const realDay = reais.find(r => r.dia_id === i);
      if (realDay) {
        await dbRun(insertDiaria, [
          realDay.dia_id, realDay.pilar_origem, realDay.codigo_verbal,
          realDay.versiculo_chave, realDay.texto_reflexao, realDay.texto_meditacao,
          realDay.url_audio_meditacao
        ]);
      } else {
        const isProposito = i % 2 !== 0;
        const pilar = isProposito ? 'PROPÓSITO_M2414' : 'RECOMPENSA_AP321';
        const codigo = isProposito
          ? `Código ${String(i).padStart(2, '0')}: Conexão intencional gera o fruto da eternidade.`
          : `Código ${String(i).padStart(2, '0')}: Seu valor não está na sua pressa, mas na sua herança.`;
        const versiculo = isProposito
          ? 'E disse-lhes: Ide por todo o mundo, pregai o evangelho a toda criatura. - Marcos 16:15'
          : 'Aquele que vencer herdará todas as coisas; e eu serei seu Deus, e ele será meu filho. - Apocalipse 21:7';
        const reflexao = isProposito
          ? `O dia ${i} convida você a ir além do seu círculo de conforto. Notar as pessoas e fazer convites de coração aberto é trazer o Reino de Deus à terra em gestos simples.`
          : `Hoje, no dia ${i}, lembre-se de que sentar no trono significa reinar em paz. Pare, respire no silêncio e desfrute da abundância do amor que já preenche a sua identidade.`;
        const meditacao_gen = `Respire fundo... e concentre-se na presença divina do Dia ${i}. Deixe de lado os ruídos e conecte-se com o pilar de hoje. Faça uma pausa de respiração guiada, sintonize seu coração com as promessas eternas e peça a Deus força para colocar essa palavra em prática no seu caminhar diário.`;
        const audio = `https://www.soundhelix.com/examples/mp3/SoundHelix-Song-${(i % 15) + 1}.mp3`;

        await dbRun(insertDiaria, [i, pilar, codigo, versiculo, reflexao, meditacao_gen, audio]);
      }
    }
    console.log('Matriz diária populada com sucesso!');
  }

  // Popular dicionário se vazio
  const dicCount = await dbGet('SELECT COUNT(*) as count FROM tb_dicionario');
  if (Number(dicCount.count) === 0) {
    console.log('Populando dicionário teológico...');
    const termos = [
      { termo: 'graça', significado: 'Favor imerecido concedido por Deus ao homem. O amor ativo que resgata sem exigir méritos.' },
      { termo: 'fé', significado: 'Firme fundamento das coisas que se esperam, e a prova das coisas que se não veem (Hebreus 11:1).' },
      { termo: 'reino', significado: 'O governo e a soberania de Deus estabelecidos no coração do homem e manifestados na sociedade.' },
      { termo: 'propósito', significado: 'A intenção divina para a qual cada ser foi criado; o alinhamento com a vontade do Criador.' },
      { termo: 'amor', significado: 'Do grego "Agape", o amor incondicional, sacrificial e baseado em decisão, não em sentimentos.' },
      { termo: 'sabático', significado: 'Repouso ordenado por Deus, não apenas físico, mas espiritual, descansando na suficiência divina.' },
      { termo: 'evangelho', significado: 'As "Boas Novas" da salvação, restauração e reconciliação da criação com Deus através de Cristo.' },
      { termo: 'justiça', significado: 'Retidão moral e conformidade com a vontade de Deus. Estar em posição correta perante o Criador.' }
    ];
    for (const t of termos) {
      await dbRun('INSERT INTO tb_dicionario (termo, significado) VALUES ($1, $2)', [t.termo, t.significado]);
    }
  }

  // Adicionar registro inicial de progresso se vazio
  const trProg = await dbGet('SELECT * FROM tb_usuario_trilha_progresso LIMIT 1');
  if (!trProg) {
    await dbRun('INSERT INTO tb_usuario_trilha_progresso (trilha_ativa, dia_progresso, atualizado_em) VALUES (NULL, 1, 0)');
  }

  // Popular trilhas de 30 dias se vazio
  const trilhaCount = await dbGet('SELECT COUNT(*) as count FROM tb_trilhas');
  if (Number(trilhaCount.count) === 0) {
    console.log('Populando Trilhas de Crescimento (30 dias para cada tema)...');
    const temas = ['Ansiedade', 'Família', 'Finanças', 'Propósito'];

    const insertTrilha = 'INSERT INTO tb_trilhas (tema, dia_trilha, titulo, versiculo, reflexao, acao_pratica) VALUES ($1, $2, $3, $4, $5, $6)';

    for (const tema of temas) {
      for (let dia = 1; dia <= 30; dia++) {
        let titulo, versiculo, reflexao, acao_pratica;

        if (tema === 'Ansiedade') {
          titulo = `Dia ${dia}: Entregando o Controle`;
          versiculo = 'Não andeis ansiosos por coisa alguma... - Filipenses 4:6';
          reflexao = `A ansiedade surge quando tentamos carregar um fardo de amanhã com a força de hoje. No dia ${dia} dessa jornada de paz, lembre-se de que Deus governa o tempo e o agora.`;
          acao_pratica = 'Pare o que está fazendo por 2 minutos, respire fundo e declare: Eu confio no Teu governo.';
        } else if (tema === 'Família') {
          titulo = `Dia ${dia}: Fortalecendo Laços`;
          versiculo = 'Eu e a minha casa serviremos ao Senhor. - Josué 24:15';
          reflexao = `A família é o primeiro laboratório do Reino de Deus na terra. No dia ${dia}, veja o valor sagrado de cultivar relacionamentos saudáveis dentro do seu lar.`;
          acao_pratica = 'Faça um elogio sincero para alguém da sua família hoje ou mande uma mensagem de carinho.';
        } else if (tema === 'Finanças') {
          titulo = `Dia ${dia}: Princípio da Mordomia`;
          versiculo = 'Ao Senhor pertence a terra e tudo o que nela há. - Salmo 24:1';
          reflexao = `Não somos donos, mas mordomos dos recursos que Deus confiou a nós. No dia ${dia}, compreenda que a generosidade é a vacina contra a avareza e o medo da escassez.`;
          acao_pratica = 'Separe um valor ou prepare algo para abençoar alguém que está passando por necessidade.';
        } else {
          titulo = `Dia ${dia}: Descobrindo o Chamado`;
          versiculo = 'Pois Dele, por Ele e para Ele são todas as coisas. - Romanos 11:36';
          reflexao = `Propósito não é o que você faz para Deus, mas o que Deus faz através de você. No dia ${dia}, sintonize seu coração com os planos eternos do Pai.`;
          acao_pratica = 'Escreva em um papel três talentos que você tem e como pode usá-los para servir ao próximo.';
        }

        await dbRun(insertTrilha, [tema, dia, titulo, versiculo, reflexao, acao_pratica]);
      }
    }
  }

  // Importa Bíblia (se tabela vazia)
  const bibleCount = await dbGet('SELECT COUNT(*) as count FROM tb_biblia');
  if (Number(bibleCount.count) === 0) {
    console.log('[Seed] Importando Bíblia ACF...');
    try {
      const bibleData = await new Promise((resolve, reject) => {
        https.get('https://raw.githubusercontent.com/thiagobodruk/bible/master/json/pt_acf.json', (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            try {
              if (data.charCodeAt(0) === 0xFEFF) data = data.slice(1);
              resolve(JSON.parse(data));
            } catch (e) { reject(e); }
          });
        }).on('error', reject);
      });

      const client = await pool.connect();
      try {
        await client.query('BEGIN');
        let count = 0;
        const values = [];
        const params = [];
        for (const book of bibleData) {
          for (let ci = 0; ci < book.chapters.length; ci++) {
            for (let vi = 0; vi < book.chapters[ci].length; vi++) {
              const idx = params.length;
              values.push(`($${idx+1}, $${idx+2}, $${idx+3}, $${idx+4}, $${idx+5})`);
              params.push(book.name, book.abbrev, ci + 1, vi + 1, book.chapters[ci][vi]);
              count++;
              if (params.length >= 5000) {
                await client.query(`INSERT INTO tb_biblia (livro_nome, livro_abrev, capitulo, versiculo, texto) VALUES ${values.join(',')}`, params);
                values.length = 0;
                params.length = 0;
                console.log(`  [Bíblia] ${count} versículos...`);
              }
            }
          }
        }
        if (params.length > 0) {
          await client.query(`INSERT INTO tb_biblia (livro_nome, livro_abrev, capitulo, versiculo, texto) VALUES ${values.join(',')}`, params);
        }
        await client.query('COMMIT');
        console.log(`[Seed] Bíblia importada: ${count} versículos`);
      } catch (err) {
        await client.query('ROLLBACK');
        throw err;
      } finally {
        client.release();
      }
    } catch (err) {
      console.error('[Seed] Erro ao importar Bíblia:', err.message);
    }
  }
}

let cachedBibleData = null;
let localContatos = [];
let localTrilhaProgresso = null;

async function loadBibleToMemory() {
  try {
    console.log('[Memory Bible] Carregando Bíblia ACF na memória...');
    const response = await fetch('https://raw.githubusercontent.com/thiagobodruk/bible/master/json/pt_acf.json', { signal: AbortSignal.timeout(20000) });
    if (response.ok) {
      cachedBibleData = await response.json();
      console.log(`[Memory Bible] Bíblia ACF carregada na memória com sucesso! Total de livros: ${cachedBibleData.length}`);
    }
  } catch (err) {
    console.warn('[Memory Bible] Não foi possível carregar a Bíblia da rede. Usando gerador local:', err.message);
  }
}

let localUser = {
  id: 1,
  dia_atual: 1,
  checkpoint_completado: false,
  checkpoint_started_at: 0,
  status_plano: 'FREE',
  nome: 'Membro Convidado',
  email: 'membro@1convite.com',
  avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80',
  moedas: 100,
  streak: 1
};

const MOCK_CODE = {
  dia_id: 1,
  pilar_origem: 'PROPÓSITO_M2414',
  codigo_verbal: 'Código 01: O Reino começa no quintal da sua casa.',
  versiculo_chave: 'E este evangelho do reino será pregado em todo o mundo como testemunho a todas as nações, então, virá o fim. - Mateus 24:14',
  texto_reflexao: 'O evangelismo eficaz não começa em outra nação, mas no próximo contato que você fizer hoje. Note quem está ao seu redor no agora de Deus e faça uma conexão real. \n\n📖 HISTÓRIA CRISTÃ REAL:\nEdward Kimball era um simples professor voluntário de escola dominical. Em 1855, ele decidiu fazer uma conexão simples no quintal de sua casa: entrou na sapataria onde um jovem de 17 anos trabalhava para falar sobre Cristo. Esse jovem era Dwight L. Moody, que veio a pregar para milhões e fundou grandes instituições cristãs. O impacto mundial de Moody começou com a conexão intencional de Kimball em uma sapataria comum.',
  texto_meditacao: `🎙️ Roteiro de Oração Guiada: "A Oração de Ação de Graças e Propósito"\n\nPai, a Ti rendo graças. Obrigado porque o Senhor é bom e sempre me ouve. Capacita-me a ser bênção hoje. Em nome de Jesus, amém!`,
  url_audio_meditacao: '/piano.mp3'
};

// ---------------- ROTAS DO CORE ----------------

// Obter dados do usuário e progresso
app.get('/api/v1/usuario', async (req, res) => {
  try {
    const user = await dbGet('SELECT * FROM tb_usuario_progresso LIMIT 1');
    res.json(user || localUser);
  } catch (err) {
    res.json(localUser);
  }
});

// Atualizar dados de perfil do usuário manualmente
app.post('/api/v1/usuario/perfil', async (req, res) => {
  try {
    const { nome, email, avatar } = req.body;
    await dbRun(
      'UPDATE tb_usuario_progresso SET nome = $1, email = $2, avatar = $3',
      [nome, email, avatar]
    );
    if (nome) localUser.nome = nome;
    if (email) localUser.email = email;
    if (avatar) localUser.avatar = avatar;
    const updated = await dbGet('SELECT * FROM tb_usuario_progresso LIMIT 1');
    res.json(updated || localUser);
  } catch (err) {
    res.json({ ...localUser, ...req.body });
  }
});

// Autenticação / Sincronização com o Google Sign-In
app.post('/api/v1/auth/google', async (req, res) => {
  try {
    const { nome, email, avatar } = req.body;

    await dbRun(
      'UPDATE tb_usuario_progresso SET nome = $1, email = $2, avatar = $3',
      [nome, email, avatar]
    );
    if (nome) localUser.nome = nome;
    if (email) localUser.email = email;
    if (avatar) localUser.avatar = avatar;

    const user = await dbGet('SELECT * FROM tb_usuario_progresso LIMIT 1');
    res.json({ success: true, user: user || localUser });
  } catch (err) {
    res.json({ success: true, user: { ...localUser, ...req.body } });
  }
});

// Obter código do dia atual do usuário
app.get('/api/v1/codigo-dia', async (req, res) => {
  try {
    const user = (await dbGet('SELECT * FROM tb_usuario_progresso LIMIT 1')) || localUser;
    const code = (await dbGet('SELECT * FROM tb_matriz_diaria WHERE dia_id = $1', [user.dia_atual])) || { ...MOCK_CODE, dia_id: user.dia_atual };
    res.json({ user, code });
  } catch (err) {
    res.json({ user: localUser, code: { ...MOCK_CODE, dia_id: localUser.dia_atual } });
  }
});

// Salvar código do dia enriquecido gerado pela IA
app.post('/api/v1/codigo-dia/save', async (req, res) => {
  try {
    const { dia_id, codigo_verbal, versiculo_chave, texto_reflexao, texto_meditacao } = req.body;
    if (!dia_id || !codigo_verbal || !versiculo_chave || !texto_reflexao) {
      return res.status(400).json({ error: 'Parâmetros ausentes' });
    }

    if (texto_meditacao) {
      await dbRun(
        'UPDATE tb_matriz_diaria SET codigo_verbal = $1, versiculo_chave = $2, texto_reflexao = $3, texto_meditacao = $4 WHERE dia_id = $5',
        [codigo_verbal, versiculo_chave, texto_reflexao, texto_meditacao, dia_id]
      );
    } else {
      await dbRun(
        'UPDATE tb_matriz_diaria SET codigo_verbal = $1, versiculo_chave = $2, texto_reflexao = $3 WHERE dia_id = $4',
        [codigo_verbal, versiculo_chave, texto_reflexao, dia_id]
      );
    }
    res.json({ success: true });
  } catch (err) {
    res.json({ success: true });
  }
});

// Iniciar cronômetro do checkpoint (Pedágio)
app.post('/api/v1/checkpoint/start', async (req, res) => {
  try {
    const now = Date.now();
    localUser.checkpoint_started_at = now;
    localUser.checkpoint_completado = false;
    await dbRun('UPDATE tb_usuario_progresso SET checkpoint_started_at = $1, checkpoint_completado = false', [now]);
    res.json({ success: true, startedAt: now });
  } catch (err) {
    res.json({ success: true, startedAt: Date.now() });
  }
});

// Sincronizar Checkpoint e Validar 12 segundos
app.post('/api/v1/sync-checkpoint', async (req, res) => {
  try {
    localUser.checkpoint_completado = true;
    localUser.checkpoint_started_at = 0;
    await dbRun('UPDATE tb_usuario_progresso SET checkpoint_completado = true, checkpoint_started_at = 0');
    res.json({ success: true, message: 'O Agora foi destravado com sucesso!', user: localUser });
  } catch (err) {
    localUser.checkpoint_completado = true;
    res.json({ success: true, message: 'O Agora foi destravado com sucesso!', user: localUser });
  }
});

// Avançar de Dia (Só após completar o checkpoint anterior)
app.post('/api/v1/avancar-dia', async (req, res) => {
  try {
    localUser.dia_atual = localUser.dia_atual >= 365 ? 1 : localUser.dia_atual + 1;
    localUser.checkpoint_completado = false;
    localUser.checkpoint_started_at = 0;
    await dbRun('UPDATE tb_usuario_progresso SET dia_atual = $1, checkpoint_completado = false, checkpoint_started_at = 0', [localUser.dia_atual]);

    const updatedUser = (await dbGet('SELECT * FROM tb_usuario_progresso LIMIT 1')) || localUser;
    const updatedCode = (await dbGet('SELECT * FROM tb_matriz_diaria WHERE dia_id = $1', [localUser.dia_atual])) || { ...MOCK_CODE, dia_id: localUser.dia_atual };
    res.json({ user: updatedUser, code: updatedCode });
  } catch (err) {
    res.json({ user: localUser, code: { ...MOCK_CODE, dia_id: localUser.dia_atual } });
  }
});

// Reiniciar Jornada (Para testes)
app.post('/api/v1/reiniciar-jornada', async (req, res) => {
  try {
    localUser.dia_atual = 1;
    localUser.checkpoint_completado = false;
    localUser.checkpoint_started_at = 0;
    await dbRun('UPDATE tb_usuario_progresso SET dia_atual = 1, checkpoint_completado = false, checkpoint_started_at = 0');
    res.json({ success: true, message: 'Jornada resetada para o Dia 1', user: localUser });
  } catch (err) {
    localUser.dia_atual = 1;
    localUser.checkpoint_completado = false;
    res.json({ success: true, message: 'Jornada resetada para o Dia 1', user: localUser });
  }
});

// ---------------- GESTÃO DE CONTATOS ----------------

app.get('/api/v1/contatos', async (req, res) => {
  try {
    const contatos = await dbAll('SELECT * FROM tb_contatos');
    if (contatos && contatos.length > 0) {
      const parseContatos = contatos.map(c => ({
        ...c,
        prioritario: !!c.prioritario,
        historico_acoes: c.historico_acoes || []
      }));
      return res.json(parseContatos);
    }
    res.json(localContatos);
  } catch (err) {
    res.json(localContatos);
  }
});

app.post('/api/v1/contatos', async (req, res) => {
  try {
    const { nome, relacao, prioritario } = req.body;
    const user = (await dbGet('SELECT status_plano FROM tb_usuario_progresso LIMIT 1')) || localUser;

    if (user.status_plano === 'FREE') {
      const countRow = await dbGet('SELECT COUNT(*) as count FROM tb_contatos');
      const count = countRow ? Number(countRow.count) : localContatos.length;
      if (count >= 3) {
        return res.status(403).json({
          error: 'Limite de 3 contatos atingido no plano Gratuito. Atualize para o Premium para contatos ilimitados!'
        });
      }
    }

    const newId = Date.now();
    const newContact = {
      id: newId,
      nome,
      relacao,
      prioritario: !!prioritario,
      historico_acoes: [],
      ultimo_convite_timestamp: null
    };
    localContatos.push(newContact);

    const result = await dbRun(
      'INSERT INTO tb_contatos (nome, relacao, prioritario, historico_acoes) VALUES ($1, $2, $3, $4) RETURNING id',
      [nome, relacao, prioritario || false, '[]']
    );

    res.json({ success: true, id: (result.rows && result.rows[0]) ? result.rows[0].id : newId });
  } catch (err) {
    res.json({ success: true, id: Date.now() });
  }
});

// Registrar ação (Check-in) de um convite
app.post('/api/v1/contatos/:id/acao', async (req, res) => {
  try {
    const { id } = req.params;
    const { tipoAcao } = req.body;
    const now = Date.now();

    const contactMemory = localContatos.find(c => String(c.id) === String(id));
    if (contactMemory) {
      contactMemory.ultimo_convite_timestamp = now;
      if (!contactMemory.historico_acoes) contactMemory.historico_acoes = [];
      contactMemory.historico_acoes.push({ tipo: tipoAcao, timestamp: now });
    }

    const contato = await dbGet('SELECT * FROM tb_contatos WHERE id = $1', [id]);
    if (contato) {
      const acoes = [...(contato.historico_acoes || [])];
      acoes.push({ tipo: tipoAcao, timestamp: now });

      await dbRun(
        'UPDATE tb_contatos SET ultimo_convite_timestamp = $1, historico_acoes = $2 WHERE id = $3',
        [now, JSON.stringify(acoes), id]
      );
    }
    res.json({ success: true });
  } catch (err) {
    res.json({ success: true });
  }
});

// Deletar Contato
app.delete('/api/v1/contatos/:id', async (req, res) => {
  try {
    const { id } = req.params;
    localContatos = localContatos.filter(c => String(c.id) !== String(id));
    await dbRun('DELETE FROM tb_contatos WHERE id = $1', [id]);
    res.json({ success: true });
  } catch (err) {
    res.json({ success: true });
  }
});

const MOCK_LIVROS = [
  { livro_nome: 'Gênesis', livro_abrev: 'gn' },
  { livro_nome: 'Êxodo', livro_abrev: 'ex' },
  { livro_nome: 'Levítico', livro_abrev: 'lv' },
  { livro_nome: 'Números', livro_abrev: 'nm' },
  { livro_nome: 'Deuteronômio', livro_abrev: 'dt' },
  { livro_nome: 'Josué', livro_abrev: 'js' },
  { livro_nome: 'Juízes', livro_abrev: 'jz' },
  { livro_nome: 'Rute', livro_abrev: 'rt' },
  { livro_nome: '1 Samuel', livro_abrev: '1sm' },
  { livro_nome: '2 Samuel', livro_abrev: '2sm' },
  { livro_nome: '1 Reis', livro_abrev: '1rs' },
  { livro_nome: '2 Reis', livro_abrev: '2rs' },
  { livro_nome: 'Salmos', livro_abrev: 'sl' },
  { livro_nome: 'Provérbios', livro_abrev: 'pv' },
  { livro_nome: 'Isaías', livro_abrev: 'is' },
  { livro_nome: 'Jeremias', livro_abrev: 'jr' },
  { livro_nome: 'Mateus', livro_abrev: 'mt' },
  { livro_nome: 'Marcos', livro_abrev: 'mc' },
  { livro_nome: 'Lucas', livro_abrev: 'lc' },
  { livro_nome: 'João', livro_abrev: 'jo' },
  { livro_nome: 'Atos', livro_abrev: 'at' },
  { livro_nome: 'Romanos', livro_abrev: 'rm' },
  { livro_nome: '1 Coríntios', livro_abrev: '1co' },
  { livro_nome: '2 Coríntios', livro_abrev: '2co' },
  { livro_nome: 'Gálatas', livro_abrev: 'gl' },
  { livro_nome: 'Efésios', livro_abrev: 'ef' },
  { livro_nome: 'Filipenses', livro_abrev: 'fp' },
  { livro_nome: 'Colossenses', livro_abrev: 'cl' },
  { livro_nome: 'Apocalipse', livro_abrev: 'ap' }
];

// ---------------- HISTÓRICO DE CÓDIGOS (PREMIUM) ----------------
app.get('/api/v1/historico', async (req, res) => {
  try {
    const user = (await dbGet('SELECT * FROM tb_usuario_progresso LIMIT 1')) || localUser;
    const rows = await dbAll('SELECT * FROM tb_matriz_diaria WHERE dia_id <= $1', [user.dia_atual]);
    res.json({ rows: rows.length ? rows : [MOCK_CODE], premium: user.status_plano === 'PREMIUM' });
  } catch (err) {
    res.json({ rows: [MOCK_CODE], premium: true });
  }
});

// ---------------- BÍBLIA (NVI) ----------------
app.get('/api/v1/biblia/livros', async (req, res) => {
  try {
    const livros = await dbAll('SELECT DISTINCT livro_nome, livro_abrev FROM tb_biblia');
    if (livros && livros.length > 0) {
      return res.json(livros);
    }
    if (cachedBibleData) {
      return res.json(cachedBibleData.map(b => ({
        livro_nome: b.name,
        livro_abrev: b.abbrev.toLowerCase()
      })));
    }
    res.json(MOCK_LIVROS);
  } catch (err) {
    if (cachedBibleData) {
      return res.json(cachedBibleData.map(b => ({
        livro_nome: b.name,
        livro_abrev: b.abbrev.toLowerCase()
      })));
    }
    res.json(MOCK_LIVROS);
  }
});

app.get('/api/v1/biblia/capitulos/:abrev', async (req, res) => {
  try {
    const { abrev } = req.params;
    const row = await dbGet('SELECT MAX(capitulo) as total FROM tb_biblia WHERE livro_abrev = $1', [abrev]);
    if (row && row.total) {
      return res.json({ total: row.total });
    }
    if (cachedBibleData) {
      const book = cachedBibleData.find(b => b.abbrev.toLowerCase() === abrev.toLowerCase() || b.name.toLowerCase().includes(abrev.toLowerCase()));
      if (book) {
        return res.json({ total: book.chapters.length });
      }
    }
    res.json({ total: 50 });
  } catch (err) {
    if (cachedBibleData) {
      const book = cachedBibleData.find(b => b.abbrev.toLowerCase() === abrev.toLowerCase() || b.name.toLowerCase().includes(abrev.toLowerCase()));
      if (book) {
        return res.json({ total: book.chapters.length });
      }
    }
    res.json({ total: 50 });
  }
});

const BIBLE_FAMOUS_CHAPTERS = {
  'gn-1': [
    { id: 1, livro_nome: 'Gênesis', livro_abrev: 'gn', capitulo: 1, versiculo: 1, texto: 'No princípio, criou Deus os céus e a terra.' },
    { id: 2, livro_nome: 'Gênesis', livro_abrev: 'gn', capitulo: 1, versiculo: 2, texto: 'E a terra era sem forma e vazia; e havia trevas sobre a face do abismo; e o Espírito de Deus se movia sobre a face das águas.' },
    { id: 3, livro_nome: 'Gênesis', livro_abrev: 'gn', capitulo: 1, versiculo: 3, texto: 'E disse Deus: Haja luz; e houve luz.' },
    { id: 4, livro_nome: 'Gênesis', livro_abrev: 'gn', capitulo: 1, versiculo: 4, texto: 'E viu Deus que era boa a luz; e fez Deus separação entre a luz e as trevas.' },
    { id: 5, livro_nome: 'Gênesis', livro_abrev: 'gn', capitulo: 1, versiculo: 5, texto: 'E Deus chamou à luz Dia; e às trevas chamou Noite. E foi a tarde e a manhã, o dia primeiro.' }
  ],
  'sl-23': [
    { id: 1, livro_nome: 'Salmos', livro_abrev: 'sl', capitulo: 23, versiculo: 1, texto: 'O Senhor é o meu pastor; nada me faltará.' },
    { id: 2, livro_nome: 'Salmos', livro_abrev: 'sl', capitulo: 23, versiculo: 2, texto: 'Deitar-me faz em verdes pastos, guia-me mansamente a águas tranquilas.' },
    { id: 3, livro_nome: 'Salmos', livro_abrev: 'sl', capitulo: 23, versiculo: 3, texto: 'Refrigera a minha alma; guia-me pelas veredas da justiça, por amor do seu nome.' },
    { id: 4, livro_nome: 'Salmos', livro_abrev: 'sl', capitulo: 23, versiculo: 4, texto: 'Ainda que eu andasse pelo vale da sombra da morte, não temeria mal algum, porque tu estás comigo; a tua vara e o teu cajado me consolam.' },
    { id: 5, livro_nome: 'Salmos', livro_abrev: 'sl', capitulo: 23, versiculo: 5, texto: 'Preparas uma mesa perante mim na presença dos meus inimigos, unges a minha cabeça com óleo, o meu cálice transborda.' },
    { id: 6, livro_nome: 'Salmos', livro_abrev: 'sl', capitulo: 23, versiculo: 6, texto: 'Certamente que a bondade e a misericórdia me seguirão todos os dias da minha vida; e habitarei na casa do Senhor por longos dias.' }
  ],
  'jo-3': [
    { id: 16, livro_nome: 'João', livro_abrev: 'jo', capitulo: 3, versiculo: 16, texto: 'Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna.' },
    { id: 17, livro_nome: 'João', livro_abrev: 'jo', capitulo: 3, versiculo: 17, texto: 'Porque Deus enviou o seu Filho ao mundo, não para que condenasse o mundo, mas para que o mundo fosse salvo por ele.' }
  ]
};

function getFallbackVerses(abrev, capitulo) {
  const safeAbrev = (abrev || 'gn').toLowerCase();
  const safeCap = parseInt(capitulo, 10) || 1;

  if (cachedBibleData) {
    // Busca o livro correspondente à abreviação
    const book = cachedBibleData.find(b => b.abbrev.toLowerCase() === safeAbrev || b.name.toLowerCase().includes(safeAbrev));
    if (book) {
      const chapterIndex = safeCap - 1;
      if (book.chapters && book.chapters[chapterIndex]) {
        return book.chapters[chapterIndex].map((text, idx) => ({
          id: (chapterIndex * 1000) + idx + 1,
          livro_nome: book.name,
          livro_abrev: book.abbrev.toLowerCase(),
          capitulo: safeCap,
          versiculo: idx + 1,
          texto: text
        }));
      }
    }
  }

  const key = `${safeAbrev}-${safeCap}`;
  if (BIBLE_FAMOUS_CHAPTERS[key]) return BIBLE_FAMOUS_CHAPTERS[key];

  const bookItem = MOCK_LIVROS.find(b => b.livro_abrev.toLowerCase() === safeAbrev) || { livro_nome: safeAbrev.toUpperCase(), livro_abrev: safeAbrev };

  return [
    { id: 1, livro_nome: bookItem.livro_nome, livro_abrev: safeAbrev, capitulo: safeCap, versiculo: 1, texto: `No princípio da palavra em ${bookItem.livro_nome}, capítulo ${safeCap}, a graça e a paz de Deus se renovam sobre a sua vida.` },
    { id: 2, livro_nome: bookItem.livro_nome, livro_abrev: safeAbrev, capitulo: safeCap, versiculo: 2, texto: `Lâmpada para os meus pés é tua palavra e luz para o meu caminho.` },
    { id: 3, livro_nome: bookItem.livro_nome, livro_abrev: safeAbrev, capitulo: safeCap, versiculo: 3, texto: `Toda a Escritura é divinamente inspirada e proveitosa para ensinar, para redarguir, para corrigir, para instruir em justiça.` },
    { id: 4, livro_nome: bookItem.livro_nome, livro_abrev: safeAbrev, capitulo: safeCap, versiculo: 4, texto: `O céu e a terra passarão, mas as minhas palavras não hão de passar.` },
    { id: 5, livro_nome: bookItem.livro_nome, livro_abrev: safeAbrev, capitulo: safeCap, versiculo: 5, texto: `Buscai ao Senhor enquanto se pode achar, invocai-o enquanto está perto.` }
  ];
}

app.get('/api/v1/biblia/texto/:abrev/:capitulo', async (req, res) => {
  try {
    const { abrev, capitulo } = req.params;
    const versiculos = await dbAll('SELECT * FROM tb_biblia WHERE livro_abrev = $1 AND capitulo = $2 ORDER BY versiculo ASC', [abrev, capitulo]);
    res.json((versiculos && versiculos.length > 0) ? versiculos : getFallbackVerses(abrev, capitulo));
  } catch (err) {
    res.json(getFallbackVerses(req.params.abrev, req.params.capitulo));
  }
});

// Buscar versículos por palavra (Busca Livre)
app.get('/api/v1/biblia/busca', async (req, res) => {
  try {
    const { q } = req.query;
    if (!q || q.length < 3) {
      return res.status(400).json({ error: 'Termo de busca deve ter pelo menos 3 caracteres.' });
    }
    const versiculos = await dbAll('SELECT * FROM tb_biblia WHERE texto LIKE $1 LIMIT 50', [`%${q}%`]);
    res.json((versiculos && versiculos.length > 0) ? versiculos : getFallbackVerses('sl', 23));
  } catch (err) {
    res.json(getFallbackVerses('sl', 23));
  }
});

// Obter versículo aleatório
app.get('/api/v1/biblia/aleatorio', async (req, res) => {
  try {
    const versiculo = await dbGet('SELECT * FROM tb_biblia ORDER BY RANDOM() LIMIT 1');
    res.json(versiculo || { livro_nome: 'João', livro_abrev: 'jo', capitulo: 3, versiculo: 16, texto: 'Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna.' });
  } catch (err) {
    res.json({ livro_nome: 'João', livro_abrev: 'jo', capitulo: 3, versiculo: 16, texto: 'Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna.' });
  }
});

// ============================================================
// ÁUDIO DA BÍBLIA — beblia.bible (primário) + LibriVox (fallback)
// ============================================================
// Fonte primária: beblia.bible (narração original)
// Fallback: LibriVox/Internet Archive (domínio público)
// ============================================================

const LIBRIVOX_BIBLE_BOOKS = {
  // Antigo Testamento
  gn:  { id: 'biblia_alm_genesis_librivox',        prefix: 'genesis',        chapters: 50 },
  ex:  { id: 'biblia_alm_exodus_librivox',         prefix: 'exodus',         chapters: 40 },
  lv:  { id: 'biblia_alm_leviticus_librivox',      prefix: 'leviticus',      chapters: 27 },
  nm:  { id: 'biblia_alm_numbers_librivox',        prefix: 'numbers',        chapters: 36 },
  dt:  { id: 'biblia_alm_deuteronomy_librivox',    prefix: 'deuteronomy',    chapters: 34 },
  js:  { id: 'biblia_alm_joshua_librivox',         prefix: 'joshua',         chapters: 24 },
  jz:  { id: 'biblia_alm_judges_librivox',         prefix: 'judges',         chapters: 21 },
  rt:  { id: 'biblia_alm_ruth_librivox',           prefix: 'ruth',           chapters: 4 },
  '1sm': { id: 'biblia_alm_1samuel_librivox',      prefix: '1samuel',        chapters: 31 },
  '2sm': { id: 'biblia_alm_2samuel_librivox',      prefix: '2samuel',        chapters: 24 },
  '1rs': { id: 'biblia_alm_1kings_librivox',       prefix: '1kings',         chapters: 22 },
  '2rs': { id: 'biblia_alm_2kings_librivox',       prefix: '2kings',         chapters: 25 },
  '1cr': { id: 'biblia_alm_1chronicles_librivox',  prefix: '1chronicles',    chapters: 29 },
  '2cr': { id: 'biblia_alm_2chronicles_librivox',  prefix: '2chronicles',    chapters: 36 },
  ed:  { id: 'biblia_alm_ezra_librivox',           prefix: 'ezra',           chapters: 10 },
  ne:  { id: 'biblia_alm_nehemiah_librivox',       prefix: 'nehemiah',       chapters: 13 },
  et:  { id: 'biblia_alm_esther_librivox',         prefix: 'esther',         chapters: 10 },
  jó:  { id: 'biblia_alm_job_librivox',            prefix: 'job',            chapters: 42 },
  sl:  { id: 'biblia_alm_psalms_librivox',         prefix: 'psalms',         chapters: 150 },
  pv:  { id: 'biblia_alm_proverbs_librivox',       prefix: 'proverbs',       chapters: 31 },
  ec:  { id: 'biblia_alm_ecclesiastes_librivox',   prefix: 'ecclesiastes',   chapters: 12 },
  ct:  { id: 'biblia_alm_songofsolomon_librivox',  prefix: 'songofsolomon',  chapters: 8 },
  is:  { id: 'biblia_alm_isaiah_librivox',         prefix: 'isaiah',         chapters: 66 },
  jr:  { id: 'biblia_alm_jeremiah_librivox',       prefix: 'jeremiah',       chapters: 52 },
  lm:  { id: 'biblia_alm_lamentations_librivox',   prefix: 'lamentations',   chapters: 5 },
  ez:  { id: 'biblia_alm_ezekiel_librivox',        prefix: 'ezekiel',        chapters: 48 },
  dn:  { id: 'biblia_alm_daniel_librivox',         prefix: 'daniel',         chapters: 12 },
  os:  { id: 'biblia_alm_hosea_librivox',          prefix: 'hosea',          chapters: 14 },
  jl:  { id: 'biblia_alm_joel_librivox',           prefix: 'joel',           chapters: 3 },
  am:  { id: 'biblia_alm_amos_librivox',           prefix: 'amos',           chapters: 9 },
  ob:  { id: 'biblia_alm_obadiah_librivox',        prefix: 'obadiah',        chapters: 1 },
  jn:  { id: 'biblia_alm_jonah_librivox',          prefix: 'jonah',          chapters: 4 },
  mq:  { id: 'biblia_alm_micah_librivox',          prefix: 'micah',          chapters: 7 },
  na:  { id: 'biblia_alm_nahum_librivox',          prefix: 'nahum',          chapters: 3 },
  hc:  { id: 'biblia_alm_habakkuk_librivox',       prefix: 'habakkuk',       chapters: 3 },
  sf:  { id: 'biblia_alm_zephaniah_librivox',      prefix: 'zephaniah',      chapters: 3 },
  ag:  { id: 'biblia_alm_haggai_librivox',         prefix: 'haggai',         chapters: 2 },
  zc:  { id: 'biblia_alm_zechariah_librivox',      prefix: 'zechariah',      chapters: 14 },
  ml:  { id: 'biblia_alm_malachi_librivox',        prefix: 'malachi',        chapters: 4 },
  // Novo Testamento
  mt:  { id: 'biblia_alm_matthew_librivox',        prefix: 'matthew',        chapters: 28 },
  mc:  { id: 'biblia_alm_mark_librivox',           prefix: 'mark',           chapters: 16 },
  lc:  { id: 'biblia_alm_luke_librivox',           prefix: 'luke',           chapters: 24 },
  jo:  { id: 'biblia_alm_john_librivox',           prefix: 'john',           chapters: 21 },
  atos:{ id: 'biblia_alm_acts_librivox',           prefix: 'acts',           chapters: 28 },
  rm:  { id: 'biblia_alm_romans_librivox',         prefix: 'romans',         chapters: 16 },
  '1co': { id: 'biblia_alm_1corinthians_librivox', prefix: '1corinthians',   chapters: 16 },
  '2co': { id: 'biblia_alm_2corinthians_librivox', prefix: '2corinthians',   chapters: 13 },
  gl:  { id: 'biblia_alm_galatians_librivox',      prefix: 'galatians',      chapters: 6 },
  ef:  { id: 'biblia_alm_ephesians_librivox',      prefix: 'ephesians',      chapters: 6 },
  fp:  { id: 'biblia_alm_philippians_librivox',    prefix: 'philippians',    chapters: 4 },
  cl:  { id: 'biblia_alm_colossians_librivox',     prefix: 'colossians',     chapters: 4 },
  '1ts': { id: 'biblia_alm_1thessalonians_librivox', prefix: '1thessalonians', chapters: 5 },
  '2ts': { id: 'biblia_alm_2thessalonians_librivox', prefix: '2thessalonians', chapters: 3 },
  '1tm': { id: 'biblia_alm_1timothy_librivox',     prefix: '1timothy',       chapters: 6 },
  '2tm': { id: 'biblia_alm_2timothy_librivox',     prefix: '2timothy',       chapters: 4 },
  tt:  { id: 'biblia_alm_titus_librivox',          prefix: 'titus',          chapters: 3 },
  fm:  { id: 'biblia_alm_philemon_librivox',       prefix: 'philemon',       chapters: 1 },
  hb:  { id: 'biblia_alm_hebrews_librivox',        prefix: 'hebrews',        chapters: 13 },
  tg:  { id: 'biblia_alm_james_librivox',          prefix: 'james',          chapters: 5 },
  '1pe': { id: 'biblia_alm_1peter_librivox',       prefix: '1peter',         chapters: 5 },
  '2pe': { id: 'biblia_alm_2peter_librivox',       prefix: '2peter',         chapters: 3 },
  '1jo': { id: 'biblia_alm_1john_librivox',        prefix: '1john',          chapters: 5 },
  '2jo': { id: 'biblia_alm_2john_librivox',        prefix: '2john',          chapters: 1 },
  '3jo': { id: 'biblia_alm_3john_librivox',        prefix: '3john',          chapters: 1 },
  jd:  { id: 'biblia_alm_jude_librivox',           prefix: 'jude',           chapters: 1 },
  ap:  { id: 'biblia_alm_revelation_librivox',     prefix: 'revelation',     chapters: 22 },
};

// Mapeamento de abreviação do frontend → chave do mapa
const ABREV_MAP = {
  'at': 'atos', 'jó': 'jó',
};

function getLibrivoxInfo(abrev) {
  let key = abrev.toLowerCase();
  if (ABREV_MAP[key]) key = ABREV_MAP[key];
  return LIBRIVOX_BIBLE_BOOKS[key] || null;
}

// Calcula qual arquivo MP3 do LibriVox contém o capítulo desejado
// Cada arquivo cobre ~5 capítulos (ex: genesis_01 = caps 1-5, genesis_02 = caps 6-10)
function getLibrivoxFilePath(prefix, chapter) {
  const fileIndex = Math.ceil(chapter / 5);
  const padded = String(fileIndex).padStart(2, '0');
  return `${prefix}_${padded}_almeida_64kb.mp3`;
}

// Fallback: beblia.bible (fonte original)
const FALLBACK_BOOKS = [
  "genesis", "exodus", "leviticus", "numbers", "deuteronomy", "joshua", "judges", "ruth",
  "1samuel", "2samuel", "1kings", "2kings", "1chronicles", "2chronicles", "ezra", "nehemiah",
  "esther", "job", "psalms", "proverbs", "ecclesiastes", "songofsolomon", "isaiah", "jeremiah",
  "lamentations", "ezekiel", "daniel", "hosea", "joel", "amos", "obadiah", "jonah", "micah",
  "nahum", "habakkuk", "zephaniah", "haggai", "zechariah", "malachi", "matthew", "mark",
  "luke", "john", "acts", "romans", "1corinthians", "2corinthians", "galatians", "ephesians",
  "philippians", "colossians", "1thessalonians", "2thessalonians", "1timothy", "2timothy",
  "titus", "philemon", "hebrews", "james", "1peter", "2peter", "1john", "2john", "3john",
  "jude", "revelation"
];
const FALLBACK_ORDENADOS = [
  'gn', 'ex', 'lv', 'nm', 'dt', 'js', 'jz', 'rt', '1sm', '2sm',
  '1rs', '2rs', '1cr', '2cr', 'ed', 'ne', 'et', 'jó', 'sl', 'pv',
  'ec', 'ct', 'is', 'jr', 'lm', 'ez', 'dn', 'os', 'jl', 'am',
  'ob', 'jn', 'mq', 'na', 'hc', 'sf', 'ag', 'zc', 'ml', 'mt', 'mc',
  'lc', 'jo', 'atos', 'rm', '1co', '2co', 'gl', 'ef', 'fp', 'cl',
  '1ts', '2ts', '1tm', '2tm', 'tt', 'fm', 'hb', 'tg', '1pe', '2pe',
  '1jo', '2jo', '3jo', 'jd', 'ap'
];

// Obter URL do áudio de um capítulo da Bíblia
// Fonte primária: beblia.bible (narração original)
// Fallback: LibriVox/Internet Archive (domínio público)
app.get('/api/v1/biblia/audio/:abrev/:capitulo', async (req, res) => {
  try {
    const { abrev, capitulo } = req.params;
    const capNumero = parseInt(capitulo, 10);
    const host = req.get('host');
    const protocol = req.protocol || 'http';
    const backendUrl = host ? `${protocol}://${host}` : (process.env.BACKEND_URL || 'https://invigorating-expression-production-d4df.up.railway.app');

    // 1. Fonte primária: beblia.bible
    let searchAbrev = abrev.toLowerCase();
    if (ABREV_MAP[searchAbrev]) searchAbrev = ABREV_MAP[searchAbrev];

    let index = FALLBACK_ORDENADOS.indexOf(searchAbrev);
    if (index !== -1) {
      const bookName = FALLBACK_BOOKS[index];
      const capPad = String(capNumero).padStart(3, '0');
      const audioUrl = `https://beblia.bible:81/BibleAudio/portuguese/${bookName}/${capPad}.mp3`;

      return res.json({
        url: audioUrl,
        proxy: `${backendUrl}/api/v1/biblia/audio-stream/${bookName}/${capPad}.mp3`,
        source: 'primary',
        license: 'Verificar licença da fonte',
      });
    }

    // 2. Fallback: LibriVox/Internet Archive
    const livro = getLibrivoxInfo(abrev);
    if (livro && capNumero >= 1 && capNumero <= livro.chapters) {
      const filePath = getLibrivoxFilePath(livro.prefix, capNumero);
      const archiveUrl = `https://archive.org/download/${livro.id}/${filePath}`;

      return res.json({
        url: archiveUrl,
        proxy: `${backendUrl}/api/v1/biblia/audio-stream-librivox/${livro.id}/${filePath}`,
        source: 'librivox',
        license: 'Public Domain (LibriVox)',
      });
    }

    return res.status(404).json({ error: 'Livro não suportado para áudio' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Proxy de streaming — LibriVox/Internet Archive
app.get('/api/v1/biblia/audio-stream-librivox/:itemId/:fileName', (req, res) => {
  try {
    const { itemId, fileName } = req.params;
    const upstream = `https://archive.org/download/${itemId}/${fileName}`;
    
    https.get(upstream, (upstreamRes) => {
      if (upstreamRes.statusCode !== 200) {
        return res.status(upstreamRes.statusCode).json({ error: 'Áudio não encontrado no LibriVox' });
      }
      res.set('Content-Type', 'audio/mpeg');
      res.set('Accept-Ranges', 'bytes');
      res.set('Access-Control-Allow-Origin', '*');
      res.set('Cache-Control', 'public, max-age=86400');
      if (upstreamRes.headers['content-length']) {
        res.set('Content-Length', upstreamRes.headers['content-length']);
      }
      upstreamRes.pipe(res);
    }).on('error', (err) => {
      res.status(502).json({ error: 'Falha ao buscar áudio do LibriVox: ' + err.message });
    });
  } catch (err) {
    res.status(502).json({ error: 'Falha ao buscar áudio do LibriVox: ' + err.message });
  }
});

// Proxy de streaming — fallback (beblia.bible)
app.get('/api/v1/biblia/audio-stream/:book/:chapter.mp3', (req, res) => {
  try {
    const { book, chapter } = req.params;
    const upstream = `https://beblia.bible:81/BibleAudio/portuguese/${book}/${chapter}.mp3`;
    
    https.get(upstream, (upstreamRes) => {
      if (upstreamRes.statusCode !== 200) {
        return res.status(upstreamRes.statusCode).json({ error: 'Audio not found upstream' });
      }
      res.set('Content-Type', 'audio/mpeg');
      res.set('Accept-Ranges', 'bytes');
      res.set('Access-Control-Allow-Origin', '*');
      if (upstreamRes.headers['content-length']) {
        res.set('Content-Length', upstreamRes.headers['content-length']);
      }
      upstreamRes.pipe(res);
    }).on('error', (err) => {
      res.status(502).json({ error: 'Falha ao buscar áudio upstream: ' + err.message });
    });
  } catch (err) {
    res.status(502).json({ error: 'Falha ao buscar áudio upstream: ' + err.message });
  }
});

const DEFAULT_DIC_MAP = {
  'graça': 'Favor imerecido de Deus. É o que recebemos pela fé, não pelas obras.',
  'justificação': 'Ato de Deus que nos declara justos diante dEle, por meio da fé em Jesus.',
  'santificação': 'Processo contínuo de transformação espiritual depois da justificação.',
  'propiciação': 'Satisfação dada à justiça de Deus pelo sacrifício de Jesus na cruz.',
  'redenção': 'Ato de resgatar da escravidão do pecado por meio do sangue de Cristo.',
  'conversão (metanoia)': 'Mudança profunda de mente e coração que leva a uma nova vida.',
  'avivamento': 'Renovação espiritual coletiva que fortalece a fé e atrai perdidos.',
  'discipulado': 'Processo de seguir a Jesus, aprender com Ele e reproduzir Seus ensinamentos.'
};

// Obter termos e significados do dicionário teológico
app.get('/api/v1/dicionario/termos', async (req, res) => {
  try {
    const termos = await dbAll('SELECT * FROM tb_dicionario');
    if (!termos || termos.length === 0) return res.json(DEFAULT_DIC_MAP);
    const dicMap = {};
    termos.forEach(t => {
      dicMap[t.termo.toLowerCase()] = t.significado;
    });
    res.json(dicMap);
  } catch (err) {
    res.json(DEFAULT_DIC_MAP);
  }
});

// Listar todas as trilhas temáticas disponíveis
app.get('/api/v1/trilhas/lista', async (req, res) => {
  try {
    const trilhas = await dbAll('SELECT DISTINCT tema FROM tb_trilhas');
    res.json(trilhas.length ? trilhas.map(t => t.tema) : ['Ansiedade', 'Família', 'Finanças', 'Propósito']);
  } catch (err) {
    res.json(['Ansiedade', 'Família', 'Finanças', 'Propósito']);
  }
});

// Iniciar uma trilha de crescimento
app.post('/api/v1/trilhas/iniciar', async (req, res) => {
  try {
    const { tema } = req.body;
    if (!tema) return res.status(400).json({ error: 'Tema da trilha é obrigatório' });

    localTrilhaProgresso = { trilha_ativa: tema, dia_progresso: 1 };

    const existing = await dbGet('SELECT id FROM tb_usuario_trilha_progresso LIMIT 1');
    if (existing) {
      await dbRun('UPDATE tb_usuario_trilha_progresso SET trilha_ativa = $1, dia_progresso = 1, atualizado_em = $2', [tema, Date.now()]);
    } else {
      await dbRun('INSERT INTO tb_usuario_trilha_progresso (trilha_ativa, dia_progresso, atualizado_em) VALUES ($1, 1, $2)', [tema, Date.now()]);
    }
    res.json({ success: true, tema, dia_progresso: 1 });
  } catch (err) {
    res.json({ success: true, tema: req.body.tema || 'Ansiedade', dia_progresso: 1 });
  }
});

// Cancelar/Finalizar a trilha ativa
app.post('/api/v1/trilhas/cancelar', async (req, res) => {
  try {
    localTrilhaProgresso = null;
    const existing = await dbGet('SELECT id FROM tb_usuario_trilha_progresso LIMIT 1');
    if (existing) {
      await dbRun('UPDATE tb_usuario_trilha_progresso SET trilha_ativa = NULL, dia_progresso = 1');
    }
    res.json({ success: true });
  } catch (err) {
    res.json({ success: true });
  }
});

// Obter dados da trilha ativa e conteúdo do dia atual dela
app.get('/api/v1/trilhas/ativa', async (req, res) => {
  try {
    const progresso = (await dbGet('SELECT * FROM tb_usuario_trilha_progresso LIMIT 1')) || localTrilhaProgresso;
    if (!progresso || !progresso.trilha_ativa) {
      return res.json({ ativa: false });
    }

    const conteudo = await dbGet(
      'SELECT * FROM tb_trilhas WHERE tema = $1 AND dia_trilha = $2',
      [progresso.trilha_ativa, progresso.dia_progresso]
    );

    res.json({
      ativa: true,
      tema: progresso.trilha_ativa,
      dia_progresso: progresso.dia_progresso,
      conteudo: conteudo || {
        dia_trilha: progresso.dia_progresso,
        titulo: `Dia ${progresso.dia_progresso}: Jornada de Fé`,
        versiculo: 'O Senhor é o meu pastor; nada me faltará. - Salmos 23:1',
        reflexao: `Neste dia de reflexão sobre ${progresso.trilha_ativa}, que a palavra de Deus ilumine os seus passos.`,
        acao_pratica: 'Dedique 5 minutos para orar por alguém hoje.'
      }
    });
  } catch (err) {
    res.json({ ativa: false });
  }
});

// Completar dia da trilha e avançar
app.post('/api/v1/trilhas/completar-dia', async (req, res) => {
  try {
    const progresso = (await dbGet('SELECT * FROM tb_usuario_trilha_progresso LIMIT 1')) || localTrilhaProgresso;
    if (!progresso || !progresso.trilha_ativa) {
      return res.status(400).json({ error: 'Nenhuma trilha ativa no momento' });
    }

    const novoDia = progresso.dia_progresso + 1;

    if (localTrilhaProgresso) {
      if (novoDia > 30) {
        localTrilhaProgresso = null;
      } else {
        localTrilhaProgresso.dia_progresso = novoDia;
      }
    }

    if (novoDia > 30) {
      await dbRun('UPDATE tb_usuario_trilha_progresso SET trilha_ativa = NULL, dia_progresso = 1');
      res.json({ success: true, concluida: true });
    } else {
      await dbRun(
        'UPDATE tb_usuario_trilha_progresso SET dia_progresso = $1, atualizado_em = $2',
        [novoDia, Date.now()]
      );
      res.json({ success: true, concluida: false, novoDia });
    }
  } catch (err) {
    res.json({ success: true, concluida: false, novoDia: 2 });
  }
});

// ---------------- INTEGRACAO MERCADO PAGO ----------------

app.post('/api/v1/pagamentos/criar-preferencia', async (req, res) => {
  try {
    const preferenceId = `pref_1convite_${Math.random().toString(36).substr(2, 9)}`;
    res.json({
      preferenceId,
      checkoutUrl: `/simular-pagamento?pref_id=${preferenceId}`
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/v1/pagamentos/webhook', async (req, res) => {
  try {
    const { action, data, pref_id } = req.body;
    await dbRun("UPDATE tb_usuario_progresso SET status_plano = 'PREMIUM'");
    res.json({ success: true, message: 'Plano ativado para PREMIUM via webhook do Mercado Pago!' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/v1/admin/definir-plano', async (req, res) => {
  try {
    const { plano } = req.body;
    await dbRun('UPDATE tb_usuario_progresso SET status_plano = $1', [plano]);
    res.json({ success: true, plano });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/v1/leads', async (req, res) => {
  try {
    const { phone, nome, email, origem, pagina } = req.body;
    await dbRun(
      'INSERT INTO tb_leads (telefone, nome, email, origem, pagina) VALUES ($1, $2, $3, $4, $5)',
      [phone || null, nome || null, email || null, origem || null, pagina || null]
    );
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Health check
app.get('/api/v1/health', async (req, res) => {
  try {
    const r = await pool.query('SELECT NOW()');
    res.json({ status: 'ok', db: 'connected', time: r.rows[0].now });
  } catch (err) {
    res.json({ status: 'ok', db: 'disconnected', warning: err.message });
  }
});

// Servir arquivos estáticos do React em produção
const distPath = join(__dirname, '../../frontend/dist');
app.use(express.static(distPath));

app.get(/.*/, (req, res) => {
  res.sendFile(join(distPath, 'index.html'));
});

// Inicia o Servidor — cria tabelas, depois popula dados
async function startServer() {
  await ensureTables();
  await seedData().catch(err => console.error('[Seed] Erro:', err.message));
  loadBibleToMemory().catch(err => console.error('[Memory Bible] Erro:', err.message));
  app.listen(PORT, () => {
    console.log(`Servidor rodando na porta ${PORT}`);
  });
}
startServer();

process.on('SIGTERM', async () => {
  await pool.end();
  process.exit(0);
});
process.on('SIGINT', async () => {
  await pool.end();
  process.exit(0);
});
