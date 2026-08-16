// ═══════════════════════════════════════════════════════════════════
// DADOS DOS JOGOS - Arcade Bíblico 1Convite
// ═══════════════════════════════════════════════════════════════════

// ═══════ QUIZ BÍBLICO ═══════
// Formato: { question, options: string[4], answer: number(índice da correta), difficulty: 'facil'|'medio'|'avancado' }
export const ARCADE_QUIZ_QUESTIONS = [
  // ── FÁCIL ──
  {
    question: 'Quem construiu a Arca de Noé?',
    options: ['Abraão', 'Noé', 'Moisés', 'Davi'],
    answer: 1,
    difficulty: 'facil'
  },
  {
    question: 'Qual o primeiro livro da Bíblia?',
    options: ['Êxodo', 'Gênesis', 'Levítico', 'Números'],
    answer: 1,
    difficulty: 'facil'
  },
  {
    question: 'Quantos mandamentos Deus deu a Moisés?',
    options: ['5', '7', '10', '12'],
    answer: 2,
    difficulty: 'facil'
  },
  {
    question: 'Quem foi engolido por um grande peixe?',
    options: ['Pedro', 'Paulo', 'Jonas', 'Jeremias'],
    answer: 2,
    difficulty: 'facil'
  },
  {
    question: 'Qual fruta Eva comeu no Éden?',
    options: ['Banana', 'Maçã', 'Laranja', 'Uva'],
    answer: 1,
    difficulty: 'facil'
  },
  {
    question: 'Quem matou Golias?',
    options: ['Saul', 'Davi', 'Salomão', 'Josué'],
    answer: 1,
    difficulty: 'facil'
  },
  {
    question: 'Quantos discíbulos Jesus tinha?',
    options: ['10', '11', '12', '14'],
    answer: 2,
    difficulty: 'facil'
  },
  {
    question: 'Qual o nome da mãe de Jesus?',
    options: ['Marta', 'Maria', 'Sara', 'Rebeca'],
    answer: 1,
    difficulty: 'facil'
  },
  {
    question: 'Em que cidade Jesus nasceu?',
    options: ['Nazareth', 'Jerusalém', 'Belém', 'Egito'],
    answer: 2,
    difficulty: 'facil'
  },
  {
    question: 'Qual rio Jesus foi batizado?',
    options: ['Nilo', 'Eufrates', ' Jordão', 'Tigre'],
    answer: 2,
    difficulty: 'facil'
  },

  // ── MÉDIO ──
  {
    question: 'Quantos livros tem a Bíblia?',
    options: ['64', '66', '68', '72'],
    answer: 1,
    difficulty: 'medio'
  },
  {
    question: 'Qual o significado do nome "Emmanuel"?',
    options: ['Deus é forte', 'Deos conosco', 'Deus é fiel', 'Deus é amor'],
    answer: 1,
    difficulty: 'medio'
  },
  {
    question: 'Quem foi o primeiro rei de Israel?',
    options: ['Davi', 'Salomão', 'Saul', 'Roboão'],
    answer: 2,
    difficulty: 'medio'
  },
  {
    question: 'Em quantos dias Deus criou o mundo?',
    options: ['5', '6', '7', '8'],
    answer: 1,
    difficulty: 'medio'
  },
  {
    question: 'Qual apóstolo traiu Jesus?',
    options: ['Pedro', 'Paulo', 'Judas', 'Tomé'],
    answer: 2,
    difficulty: 'medio'
  },
  {
    question: 'Quantos livros tem o Novo Testamento?',
    options: ['25', '27', '29', '31'],
    answer: 1,
    difficulty: 'medio'
  },
  {
    question: 'Qual o maior versículo da Bíblia?',
    options: ['João 3:16', 'Efésios 6:10', 'João 15:13', 'Efésios 2:8-9'],
    answer: 3,
    difficulty: 'medio'
  },
  {
    question: 'Quem escreveu a maioria das cartas do Novo Testamento?',
    options: ['Pedro', 'João', 'Paulo', 'Tiago'],
    answer: 2,
    difficulty: 'medio'
  },
  {
    question: 'Qual o nome do jardim onde Jesus orou antes de ser preso?',
    options: ['Jardim do Éden', 'Getsêmani', 'Getsemane', 'Betânia'],
    answer: 1,
    difficulty: 'medio'
  },
  {
    question: 'De onde Deus chamou Abraão?',
    options: ['Egito', 'Mesopotâmia', 'Canaã', 'Ur'],
    answer: 1,
    difficulty: 'medio'
  },

  // ── AVANÇADO ──
  {
    question: 'Qual o nome hebraico do Antigo Testamento?',
    options: ['Torá', 'Tanakh', 'Septuaginta', 'Pentateuco'],
    answer: 1,
    difficulty: 'avancado'
  },
  {
    question: 'Em que ano aproximadamente Jesus nasceu?',
    options: ['6 a.C.', '4 a.C.', '1 d.C.', '10 d.C.'],
    answer: 1,
    difficulty: 'avancado'
  },
  {
    question: 'Quantos profetas menores existem na Bíblia?',
    options: ['9', '10', '12', '14'],
    answer: 2,
    difficulty: 'avancado'
  },
  {
    question: 'Qual o tema central da Carta aos Romanos?',
    options: [' amor', 'Graça', 'Fé', 'Justiça'],
    answer: 1,
    difficulty: 'avancado'
  },
  {
    question: 'Quem foi o pai de Salomão?',
    options: ['Saul', 'Davi', 'Ezequias', 'Roboão'],
    answer: 1,
    difficulty: 'avancado'
  },
  {
    question: 'Qual a última palavra de Jesus na cruz segundo João?',
    options: ['Está consumado', 'Pai, perdoa-lhes', 'Em tuas mãos', 'Ela! Ela!'],
    answer: 0,
    difficulty: 'avancado'
  },
  {
    question: 'Onde Stephen foi apedrejado?',
    options: ['Jerusalém', 'Antioquia', 'Roma', 'Alexandria'],
    answer: 0,
    difficulty: 'avancado'
  },
  {
    question: 'Quantos capítulos tem Salmos?',
    options: ['148', '150', '152', '155'],
    answer: 1,
    difficulty: 'avancado'
  },
  {
    question: 'Qual o primeiro milagre de Jesus?',
    options: ['Curar um coxo', 'Água em vinho', 'Multiplicar pães', 'Calmar a tempestade'],
    answer: 1,
    difficulty: 'avancado'
  },
  {
    question: 'Quem foi o escriba que auxiliou Esdras?',
    options: ['Neemias', 'Baruque', 'Zorobabel', 'Ageu'],
    answer: 1,
    difficulty: 'avancado'
  }
];

// ═══════ CHARADAS - QUEM SOU EU ═══════
// Formato: { clues: string[], options: string[4], answer: number, difficulty: 'facil'|'medio'|'avancado' }
export const ARCADE_CHARADAS_QUESTIONS = [
  // ── FÁCIL ──
  {
    clues: [
      'Fui rei de Israel e era jovem quando ungido.',
      'Matei um gigante com uma pedra.',
      'Tocava harpa e escrevi muitos Salmos.',
      'Cometi um grande pecado com Bate-Seba.'
    ],
    options: ['Salomão', 'Davi', 'Saul', 'Josué'],
    answer: 1,
    difficulty: 'facil'
  },
  {
    clues: [
      'Sou profeta que fugiu de Deus.',
      'Fui engolido por um grande peixe.',
      'Preguei em Nínive contra a vontade.',
      'Meu livro tem apenas 4 capítulos.'
    ],
    options: ['Jeremias', 'Isaías', 'Jonas', 'Elias'],
    answer: 2,
    difficulty: 'facil'
  },
  {
    clues: [
      'Fui a primeira mulher criada.',
      'Lata da costa de Adão.',
      'Fui tentada pela serpente no Éden.',
      'Sou a mãe de toda a humanidade.'
    ],
    options: ['Sara', 'Eva', 'Lilith', 'Rebeca'],
    answer: 1,
    difficulty: 'facil'
  },
  {
    clues: [
      'Liderei o povo de Israel para fora do Egito.',
      'Recebi os Dez Mandamentos no Sinai.',
      'Atravessei o Mar Vermelho.',
      'Meu nome significa "tirado das águas".'
    ],
    options: ['Josué', 'Aarão', 'Moisés', 'Caleb'],
    answer: 2,
    difficulty: 'facil'
  },
  {
    clues: [
      'Fui o primeiro homem criado.',
      'Nome significa "barro" em hebraico.',
      'Fui colocado no Jardim do Éden.',
      'Deus me deu a tarefa de dar nomes aos animais.'
    ],
    options: ['Sete', 'Caim', 'Adão', 'Noé'],
    answer: 2,
    difficulty: 'facil'
  },

  // ── MÉDIO ──
  {
    clues: [
      'Fui rainha de Ester e judeia.',
      'Arrisquei minha vida para salvar meu povo.',
      'Meu nome pode significar "estrela".',
      'O livro bíblico com meu nome não menciona a Deus.'
    ],
    options: ['Dalila', 'Ester', 'Rute', 'Jael'],
    answer: 1,
    difficulty: 'medio'
  },
  {
    clues: [
      'Sou apóstolo e neguei Jesus três vezes.',
      'Jesus me chamou de "Pedra".',
      'Fui o primeiro a pregar no dia de Pentecostes.',
      'Minha epístola fala da esperança viva.'
    ],
    options: ['Paulo', 'João', 'Tiago', 'Pedro'],
    answer: 3,
    difficulty: 'medio'
  },
  {
    clues: [
      'Sou o filho mais novo de Jacó.',
      'Meus irmãos me venderam como escravo.',
      'Interpretei sonhos no Egito.',
      'Virei governador do Egito.'
    ],
    options: ['Ruben', 'Josué', 'José', 'Benjamim'],
    answer: 2,
    difficulty: 'medio'
  },
  {
    clues: [
      'Fui juíza de Israel.',
      'Liderei um exército contra Sísara.',
      'Julgava o povo sob uma palmeira.',
      'Cantéi um cântico de vitória.'
    ],
    options: ['Ester', 'Rute', 'Débora', 'Sara'],
    answer: 2,
    difficulty: 'medio'
  },
  {
    clues: [
      'Fui rei sábio de Israel.',
      'Pedi sabedoria a Deus em um sonho.',
      'Escrevi Provérbios e Eclesiastes.',
      'Construí o Templo em Jerusalém.'
    ],
    options: ['Davi', 'Salomão', 'Ezequias', 'Manassés'],
    answer: 1,
    difficulty: 'medio'
  },

  // ── AVANÇADO ──
  {
    clues: [
      'Sou o profeta do deserto.',
      'Minha voz clama no ermo.',
      'Batizei Jesus no Jordão.',
      'Fui decapitado a pedido de Herodias.'
    ],
    options: ['Isaías', 'Jeremias', 'João Batista', 'Elias'],
    answer: 2,
    difficulty: 'avancado'
  },
  {
    clues: [
      'Fui parente de Maria, mãe de Jesus.',
      'Cantei o Magnificat.',
      'Meu marido era Zacarias.',
      'Fui profeta no Templo.'
    ],
    options: ['Elisabete', 'Ana', 'Marta', 'Mara'],
    answer: 0,
    difficulty: 'avancado'
  },
  {
    clues: [
      'Fui escriba e levita.',
      'Liderei a reforma da Lei em Jerusalém.',
      'Jejuamos por confessar pecados.',
      'Lia a Lei de manhã até o meio-dia.'
    ],
    options: ['Esdras', 'Neemias', 'Ageu', 'Malaquias'],
    answer: 0,
    difficulty: 'avancado'
  },
  {
    clues: [
      'Fui o primeiro mártir cristão.',
      'Meu nome significa "coroa".',
      'Fui apedrejado enquanto via os céus abertos.',
      'Guardavam as roupas dos que me apedrejavam.'
    ],
    options: ['Estêvão', 'Filipe', 'Barnabé', 'Timóteo'],
    answer: 0,
    difficulty: 'avancado'
  },
  {
    clues: [
      'Fui centurião romano.',
      'Minha servo ficou doente e Jesus o curou.',
      'Disse: "Senhor, não sou digno".',
      'Tinha soldados sob meu comando.'
    ],
    options: ['Cornélio', 'Bartimeu', 'Lázaro', 'Simeão'],
    answer: 0,
    difficulty: 'avancado'
  }
];

// ═══════ FORCA BÍBLICA ═══════
// Formato: { word: string, tip: string, difficulty: 'facil'|'medio'|'avancado' }
export const ARCADE_FORCA_WORDS = [
  // ── FÁCIL ──
  { word: 'ARCA', tip: 'Barco que Noé construiu para o dilúvio', difficulty: 'facil' },
  { word: 'MOISES', tip: 'Líder que libertou Israel do Egito', difficulty: 'facil' },
  { word: 'DAVI', tip: 'Rei pastor que matou um gigante', difficulty: 'facil' },
  { word: 'JESUS', tip: 'O Filho de Deus, Salvador da humanidade', difficulty: 'facil' },
  { word: 'PEDRO', tip: 'Apóstolo que caminhou sobre as águas', difficulty: 'facil' },
  { word: 'ADAO', tip: 'Primeiro homem criado por Deus', difficulty: 'facil' },
  { word: 'EVA', tip: 'Primeira mulher criada por Deus', difficulty: 'facil' },
  { word: 'NOE', tip: 'Homem justo que sobreviveu ao dilúvio', difficulty: 'facil' },
  { word: 'ESTRELA', tip: 'Guia que os Magos seguiram até Jesus', difficulty: 'facil' },
  { word: 'CRESCEREI', tip: 'Jesus disse: "É preciso que eu ___, e que ele diminua"', difficulty: 'facil' },

  // ── MÉDIO ──
  { word: 'CANAA', tip: 'Cidade onde Jesus fez seu primeiro milagre', difficulty: 'medio' },
  { word: 'GETSEMANI', tip: 'Jardim onde Jesus orou antes de ser preso', difficulty: 'medio' },
  { word: 'PENTECOSTES', tip: 'Festa em que o Espírito Santo desceu', difficulty: 'medio' },
  { word: 'SAMARIA', tip: 'Região onde Jesus conversou com a mulher no poço', difficulty: 'medio' },
  { word: 'CALVARIO', tip: 'Local onde Jesus foi crucificado', difficulty: 'medio' },
  { word: 'FARISEU', tip: 'Grupo religioso que frequentemente contestava Jesus', difficulty: 'medio' },
  { word: 'BARTIMEU', tip: 'Cego que Jesus curou perto de Jericó', difficulty: 'medio' },
  { word: 'BETANIA', tip: 'Cidade onde Jesus ressuscitou Lázaro', difficulty: 'medio' },
  { word: 'CORINTO', tip: 'Cidade grega onde Paulo escreveu duas cartas', difficulty: 'medio' },
  { word: 'EFESO', tip: 'Cidade asiática da carta de Paulo', difficulty: 'medio' },

  // ── AVANÇADO ──
  { word: 'BETHLEHEM', tip: 'Cidade onde o Rei Davi nasceu e onde Jesus veio ao mundo', difficulty: 'avancado' },
  { word: 'ZACARIAS', tip: 'Pai de João Batista, ficou mudo por não acreditar', difficulty: 'avancado' },
  { word: 'LIVRO', tip: 'João viu um selado com sete ___ no Apocalipse', difficulty: 'avancado' },
  { word: 'MANA', tip: 'Alimento que caía do céu para Israel no deserto', difficulty: 'avancado' },
  { word: 'SERAFIM', tip: 'Anjos de seis asas que cantavam "Santo, Santo, Santo"', difficulty: 'avancado' },
  { word: 'CEDRO', tip: 'Árvore nobre usada na construção do Templo de Salomão', difficulty: 'avancado' },
  { word: 'TENTACULOS', tip: 'Morada portátil que Israel usava no deserto', difficulty: 'avancado' },
  { word: 'QUIRUBIM', tip: 'Anjos que guardavam a Árvore da Vida após a queda', difficulty: 'avancado' },
  { word: 'MURMURACAO', tip: 'Reclamação frequente de Israel contra Moisés no deserto', difficulty: 'avancado' },
  { word: 'UNGUENTO', tip: 'Maria ungiu os pés de Jesus com isso', difficulty: 'avancado' }
];

// ═══════ CAÇA-PALAVRAS BÍBLICO ═══════
// Formato: { word: string, difficulty: 'facil'|'medio'|'avancado' }
export const ARCADE_CACA_PALAVRAS_LIST = [
  // ── FÁCIL ──
  { word: 'DEUS', difficulty: 'facil' },
  { word: 'FE', difficulty: 'facil' },
  { word: 'AMOR', difficulty: 'facil' },
  { word: 'PAZ', difficulty: 'facil' },
  { word: 'VIDA', difficulty: 'facil' },
  { word: 'LUZ', difficulty: 'facil' },
  { word: 'REI', difficulty: 'facil' },
  { word: 'LEI', difficulty: 'facil' },
  { word: 'BOI', difficulty: 'facil' },
  { word: 'ARCA', difficulty: 'facil' },
  { word: 'LUA', difficulty: 'facil' },
  { word: 'MAR', difficulty: 'facil' },
  { word: 'SOL', difficulty: 'facil' },
  { word: 'Ceu', difficulty: 'facil' },
  { word: 'TERA', difficulty: 'facil' },

  // ── MÉDIO ──
  { word: 'CRUZ', difficulty: 'medio' },
  { word: 'GRAÇA', difficulty: 'medio' },
  { word: 'PERDAO', difficulty: 'medio' },
  { word: 'ORACAO', difficulty: 'medio' },
  { word: 'IGREJA', difficulty: 'medio' },
  { word: 'BIBLIA', difficulty: 'medio' },
  { word: 'ANGEL', difficulty: 'medio' },
  { word: 'PAULO', difficulty: 'medio' },
  { word: 'PEDRO', difficulty: 'medio' },
  { word: 'MARIA', difficulty: 'medio' },
  { word: 'TOMÉ', difficulty: 'medio' },
  { word: 'JOAO', difficulty: 'medio' },

  // ── AVANÇADO ──
  { word: 'PENTECOSTES', difficulty: 'avancado' },
  { word: 'EVANGELHO', difficulty: 'avancado' },
  { word: 'MISERICORDIA', difficulty: 'avancado' },
  { word: 'COMUNHAO', difficulty: 'avancado' },
  { word: 'BAPTISMO', difficulty: 'avancado' },
  { word: 'PROFECIA', difficulty: 'avancado' },
  { word: 'APOSTOLO', difficulty: 'avancado' },
  { word: 'CORDEIRO', difficulty: 'avancado' },
  { word: 'SACRIFICIO', difficulty: 'avancado' },
  { word: 'RESSURREICAO', difficulty: 'avancado' }
];

// ═══════ GERADOR DE GRADE CAÇA-PALAVRAS ═══════
// Gera uma grade NxN com palavras colocadas aleatoriamente
export function generateCacaPalavrasGrid(wordList, gridSize = 10, maxWords = 6) {
  const grid = [];
  const placedWords = [];
  const directions = [
    { dr: 0, dc: 1 },   // horizontal →
    { dr: 1, dc: 0 },   // vertical ↓
    { dr: 1, dc: 1 },   // diagonal ↘
    { dr: 0, dc: -1 },  // horizontal ←
    { dr: -1, dc: 0 },  // vertical ↑
    { dr: -1, dc: -1 }, // diagonal ↖
    { dr: -1, dc: 1 },  // diagonal ↗
    { dr: 1, dc: -1 }   // diagonal ↙
  ];

  // Inicializa a grade com vazios
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      grid.push({ id: `caca-${r}-${c}`, r, c, char: '', wordIds: [] });
    }
  }

  const getCell = (r, c) => grid.find(cell => cell.r === r && cell.c === c);

  // Embaralha e seleciona palavras
  const shuffled = [...wordList].sort(() => Math.random() - 0.5);
  const wordsToPlace = shuffled.slice(0, Math.min(maxWords, shuffled.length));

  let wordIdCounter = 0;

  for (const wordObj of wordsToPlace) {
    const word = wordObj.word.toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    if (word.length > gridSize) continue;

    let placed = false;
    const attempts = [];

    // Tenta posicionar a palavra
    for (let attempt = 0; attempt < 500 && !placed; attempt++) {
      const dir = directions[Math.floor(Math.random() * directions.length)];
      const startR = Math.floor(Math.random() * gridSize);
      const startC = Math.floor(Math.random() * gridSize);

      // Verifica se cabe na direção
      const endR = startR + dir.dr * (word.length - 1);
      const endC = startC + dir.dc * (word.length - 1);

      if (endR < 0 || endR >= gridSize || endC < 0 || endC >= gridSize) continue;

      // Verifica se pode colocar (sem conflito)
      let canPlace = true;
      for (let i = 0; i < word.length; i++) {
        const r = startR + dir.dr * i;
        const c = startC + dir.dc * i;
        const cell = getCell(r, c);
        if (cell && cell.char && cell.char !== word[i]) {
          canPlace = false;
          break;
        }
      }

      if (canPlace) {
        const wordId = `word-${wordIdCounter++}`;
        for (let i = 0; i < word.length; i++) {
          const r = startR + dir.dr * i;
          const c = startC + dir.dc * i;
          const cell = getCell(r, c);
          if (cell) {
            cell.char = word[i];
            cell.wordIds.push(wordId);
          }
        }
        placedWords.push({
          id: wordId,
          word: wordObj.word.toUpperCase(),
          found: false
        });
        placed = true;
      }
    }
  }

  // Preenche espaços vazios com letras aleatórias
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  for (const cell of grid) {
    if (!cell.char) {
      cell.char = alphabet[Math.floor(Math.random() * alphabet.length)];
    }
  }

  return { grid, words: placedWords };
}
