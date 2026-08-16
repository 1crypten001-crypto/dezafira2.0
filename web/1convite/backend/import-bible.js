import pool from './src/database/pool.js';
import https from 'https';

const BIBLE_URL = 'https://raw.githubusercontent.com/thiagobodruk/bible/master/json/pt_acf.json';

const downloadBible = () => {
  return new Promise((resolve, reject) => {
    console.log('Baixando JSON da Bíblia (Almeida Corrigida Fiel - ACF)...');
    https.get(BIBLE_URL, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          if (data.charCodeAt(0) === 0xFEFF) {
            data = data.slice(1);
          }
          resolve(JSON.parse(data));
        } catch (e) {
          reject('Erro ao fazer parse do JSON: ' + e.message);
        }
      });
    }).on('error', err => reject(err));
  });
};

const importBible = async () => {
  const client = await pool.connect();
  try {
    const bibleData = await downloadBible();
    console.log(`Bíblia baixada com sucesso. Total de livros: ${bibleData.length}`);

    await client.query('DELETE FROM tb_biblia');

    console.log('Inserindo versículos...');
    await client.query('BEGIN');

    let count = 0;
    const batchSize = 1000;

    for (const book of bibleData) {
      const bookName = book.name;
      const bookAbbrev = book.abbrev;

      for (let ci = 0; ci < book.chapters.length; ci++) {
        const capituloNum = ci + 1;
        const chapter = book.chapters[ci];

        for (let vi = 0; vi < chapter.length; vi++) {
          const versiculoNum = vi + 1;
          const texto = chapter[vi];

          await client.query(
            'INSERT INTO tb_biblia (livro_nome, livro_abrev, capitulo, versiculo, texto) VALUES ($1, $2, $3, $4, $5)',
            [bookName, bookAbbrev, capituloNum, versiculoNum, texto]
          );
          count++;

          if (count % batchSize === 0) {
            console.log(`  ... ${count} versículos inseridos`);
          }
        }
      }
    }

    await client.query('COMMIT');
    console.log(`✅ Importação concluída com sucesso! ${count} versículos inseridos.`);
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('Erro na importação:', err);
  } finally {
    client.release();
    await pool.end();
  }
};

importBible();
