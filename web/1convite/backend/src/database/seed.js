import pool from './pool.js';

async function seed() {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // Seed dictionary
    const dicCount = await client.query('SELECT COUNT(*) as count FROM tb_dicionario');
    if (dicCount.rows[0].count === '0') {
      console.log('Populando dicionário teológico...');
      const termos = [
        ['Graça', 'Favor imerecido de Deus. É o que recebemos pela fé, não pelas obras.'],
        ['Justificação', 'Ato de Deus que nos declara justos diante dEle, por meio da fé em Jesus.'],
        ['Santificação', 'Processo contínuo de transformação espiritual depois da justificação.'],
        ['Propiação', 'Satisfação dada à justiça de Deus pelo sacrifício de Jesus na cruz.'],
        ['Redenção', 'Ato de resgatar da escravidão do pecado por meio do sangue de Cristo.'],
        ['Conversão (Metanoia)', 'Mudança profunda de mente e coração que leva a uma nova vida.'],
        ['Avivamento', 'Renovação espiritual coletiva que fortalece a fé e atrai perdidos.'],
        ['Discipulado', 'Processo de seguir a Jesus, aprender com Ele e reproduzir Seus ensinamentos.']
      ];
      for (const [termo, significado] of termos) {
        await client.query(
          'INSERT INTO tb_dicionario (termo, significado) VALUES ($1, $2) ON CONFLICT (termo) DO NOTHING',
          [termo, significado]
        );
      }
    }

    // Seed track progress
    const trProg = await client.query('SELECT * FROM tb_usuario_trilha_progresso LIMIT 1');
    if (trProg.rows.length === 0) {
      await client.query(
        'INSERT INTO tb_usuario_trilha_progresso (trilha_ativa, dia_progresso, atualizado_em) VALUES (NULL, 1, 0)'
      );
    }

    // Seed growth tracks
    const trilhaCount = await client.query('SELECT COUNT(*) as count FROM tb_trilhas');
    if (trilhaCount.rows[0].count === '0') {
      console.log('Populando Trilhas de Crescimento (30 dias para cada tema)...');
      const temas = ['Ansiedade', 'Família', 'Finanças', 'Propósito'];
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
          await client.query(
            'INSERT INTO tb_trilhas (tema, dia_trilha, titulo, versiculo, reflexao, acao_pratica) VALUES ($1, $2, $3, $4, $5, $6)',
            [tema, dia, titulo, versiculo, reflexao, acao_pratica]
          );
        }
      }
    }

    await client.query('COMMIT');
    console.log('✅ Seed concluído com sucesso!');
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('Erro no seed:', err);
  } finally {
    client.release();
    await pool.end();
  }
}

seed();
