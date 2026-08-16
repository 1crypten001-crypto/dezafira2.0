"""Regressão: a página embutida do Chat do Hermes (/chat) precisa servir JS válido.

Bug histórico: o HTML é uma string Python e escapes como `\n` viravam newline
real no JS servido — quebrava o regex /\n/g com "Invalid regular expression:
missing /", matando o script inteiro (send nunca era definido).
O fix foi tornar o template uma raw string. Estes testes travam isso.
"""
from server import _HERMES_CHAT_HTML


def test_chat_html_regexes_nao_tem_newline_real():
    """O regex de quebra de linha deve chegar ao browser como \\n literal,
    nunca como um caractere newline de verdade (o que quebra o literal /.../)."""
    # Não deve existir um regex literal quebrado por newline real.
    assert "/\n/g" not in _HERMES_CHAT_HTML.replace("\\n", "\x00NL\x00")


def test_chat_html_regex_newline_literal():
    """`s.replace(/\n/g,"<br/>")` deve aparecer com backslash-n literal."""
    needle = 's.replace(/\\n/g,"<br/>")'
    assert needle in _HERMES_CHAT_HTML, "regex de \\n deve estar literal no HTML servido"


def test_chat_html_sem_nul_literal():
    """Nenhum byte NUL real deve estar no template (Python \u0000 processado)."""
    assert "\x00" not in _HERMES_CHAT_HTML


def test_chat_html_escapes_restantes_literais():
    """Os demais escapes de regex precisam chegar literais ao browser."""
    for literal in ["[\\s\\S]", "\\u0000PRE", "(\\d+)"]:
        assert literal in _HERMES_CHAT_HTML, f"escape {literal!r} deve estar literal"


def test_chat_html_funcao_send_definida():
    """A função send() deve existir no script servido."""
    assert "function send(" in _HERMES_CHAT_HTML
    assert 'onclick="send(' in _HERMES_CHAT_HTML
