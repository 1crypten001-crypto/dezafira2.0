"""
Config de testes — ISOLA os testes do banco real (dezafira.db).

O módulo modules/database.py lê DATABASE_URL e roda migrations/create_all
NO IMPORT. Este conftest define DATABASE_URL para um SQLite temporário
ANTES de qualquer import dos módulos da aplicação, garantindo que nenhum
teste toque ou polua o banco de desenvolvimento/produção.

⚠️ Requer que server.py use load_dotenv(override=False) — com override=True
o .env sobrescreveria o DATABASE_URL de teste (verificado em server.py).
"""

import os

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_STATE_DIR = os.path.join(_TESTS_DIR, ".pytest_state")
os.makedirs(_STATE_DIR, exist_ok=True)
_TEST_DB = os.path.join(_STATE_DIR, "test_dezafira.db")
_TEST_DB_URL = "sqlite:///" + _TEST_DB.replace("\\", "/")

# Antes de QUALQUER import da aplicação (pytest importa este módulo primeiro)
os.environ["DATABASE_URL"] = _TEST_DB_URL

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _isolated_db():
    """Remove o banco de teste ao fim da sessão (melhor esforço)."""
    yield
    try:
        from modules.database import engine
        engine.dispose()  # libera o lock do SQLite antes de apagar
    except Exception:
        pass
    try:
        os.remove(_TEST_DB)
    except Exception:
        pass
