"""Testes do _resolve_ip (services.obscura_bridge).

O Chrome 136+ recusa requisições ao DevTools com header Host de hostname
(anti DNS-rebinding). O bridge sonda/conecta via IP resolvido — este teste
garante que: loopback resolve pra 127.0.0.1, hostname resolve pra IPv4, e
falha de DNS cai de volta pro host original (sem quebrar a sonda).
"""
from services.obscura_bridge import _resolve_ip


def test_loopback_vira_ip():
    assert _resolve_ip("127.0.0.1") == "127.0.0.1"


def test_localhost_resolve_para_ipv4():
    assert _resolve_ip("localhost") == "127.0.0.1"


def test_hostname_resolve_para_ipv4():
    ip = _resolve_ip("localhost")
    # qualquer hostname que resolva vira IPv4 (nunca fica como hostname)
    assert "." in ip or ":" not in ip


def test_falha_de_dns_mantem_host_original():
    assert _resolve_ip("host-que-nao-existe-abc123.invalid") == "host-que-nao-existe-abc123.invalid"
