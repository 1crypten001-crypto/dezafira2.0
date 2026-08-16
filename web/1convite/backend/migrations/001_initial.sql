-- 1Convite - Schema PostgreSQL
-- Migrado de SQLite (2026-07-27)

-- ═══════ TABELA: Matriz Diária (365 dias) ═══════
CREATE TABLE IF NOT EXISTS tb_matriz_diaria (
  dia_id INTEGER PRIMARY KEY,
  pilar_origem TEXT CHECK(pilar_origem IN ('PROPÓSITO_M2414', 'RECOMPENSA_AP321')) NOT NULL,
  codigo_verbal TEXT NOT NULL,
  versiculo_chave TEXT NOT NULL,
  texto_reflexao TEXT NOT NULL,
  texto_meditacao TEXT,
  url_audio_meditacao TEXT NOT NULL
);

-- ═══════ TABELA: Progresso do Usuário ═══════
CREATE TABLE IF NOT EXISTS tb_usuario_progresso (
  id SERIAL PRIMARY KEY,
  dia_atual INTEGER DEFAULT 1,
  checkpoint_completado BOOLEAN DEFAULT FALSE,
  checkpoint_started_at BIGINT DEFAULT 0,
  status_plano TEXT DEFAULT 'FREE',
  nome TEXT,
  email TEXT,
  avatar TEXT
);

-- ═══════ TABELA: Contatos ═══════
CREATE TABLE IF NOT EXISTS tb_contatos (
  id SERIAL PRIMARY KEY,
  nome TEXT NOT NULL,
  relacao TEXT NOT NULL,
  prioritario BOOLEAN DEFAULT FALSE,
  ultimo_convite_timestamp BIGINT DEFAULT 0,
  historico_acoes JSONB DEFAULT '[]'::jsonb
);

-- ═══════ TABELA: Dicionário Teológico ═══════
CREATE TABLE IF NOT EXISTS tb_dicionario (
  termo TEXT PRIMARY KEY,
  significado TEXT NOT NULL
);

-- ═══════ TABELA: Trilhas de Crescimento ═══════
CREATE TABLE IF NOT EXISTS tb_trilhas (
  id SERIAL PRIMARY KEY,
  tema TEXT NOT NULL,
  dia_trilha INTEGER NOT NULL,
  titulo TEXT NOT NULL,
  versiculo TEXT NOT NULL,
  reflexao TEXT NOT NULL,
  acao_pratica TEXT NOT NULL
);

-- ═══════ TABELA: Progresso de Trilhas ═══════
CREATE TABLE IF NOT EXISTS tb_usuario_trilha_progresso (
  id SERIAL PRIMARY KEY,
  trilha_ativa TEXT DEFAULT NULL,
  dia_progresso INTEGER DEFAULT 1,
  atualizado_em BIGINT DEFAULT 0
);

-- ═══════ TABELA: Bíblia ═══════
CREATE TABLE IF NOT EXISTS tb_biblia (
  id SERIAL PRIMARY KEY,
  livro_nome TEXT NOT NULL,
  livro_abrev TEXT NOT NULL,
  capitulo INTEGER NOT NULL,
  versiculo INTEGER NOT NULL,
  texto TEXT NOT NULL
);

-- ═══════ TABELA: Leads (Landing Page) ═══════
CREATE TABLE IF NOT EXISTS tb_leads (
  id SERIAL PRIMARY KEY,
  telefone TEXT,
  nome TEXT,
  email TEXT,
  origem TEXT,
  pagina TEXT,
  criado_em TIMESTAMP DEFAULT NOW()
);

-- ═══════ ÍNDICES ═══════
CREATE INDEX IF NOT EXISTS idx_biblia_abrev_cap ON tb_biblia (livro_abrev, capitulo);
CREATE INDEX IF NOT EXISTS idx_biblia_texto_gin ON tb_biblia USING gin(to_tsvector('portuguese', texto));
CREATE INDEX IF NOT EXISTS idx_trilhas_tema_dia ON tb_trilhas (tema, dia_trilha);
CREATE INDEX IF NOT EXISTS idx_contatos_nome ON tb_contatos (nome);
