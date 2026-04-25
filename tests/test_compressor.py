import pytest
from synonyms import Compressor


@pytest.fixture
def c():
    return Compressor(domain="legal-pt", model="gpt-4o")


def test_basic_substitution(c):
    # magistrado (2 tok in-context) → juiz (1 tok): saving = 1
    result = c.compress("O magistrado decidiu.")
    assert "juiz" in result.text
    assert result.tokens_saved > 0


def test_controvérsia_maior_saving(c):
    # controvérsia (4 tok in-context) → disputa (1 tok): saving = 3
    result = c.compress("A controvérsia foi resolvida.")
    assert "disputa" in result.text
    assert result.tokens_saved >= 3


def test_case_preserved(c):
    result = c.compress("O Magistrado decidiu.")
    assert "Juiz" in result.text


def test_uppercase_preserved(c):
    result = c.compress("MAGISTRADO")
    assert "JUIZ" in result.text


def test_no_match_returns_original(c):
    text = "O contrato foi assinado."
    result = c.compress(text)
    assert result.text == text
    assert result.tokens_saved == 0


def test_multiple_substitutions(c):
    # requerente (+1) e magistrado (+1) = 2 subs com saving real
    text = "O requerente comparecem perante o magistrado da vara."
    result = c.compress(text)
    assert result.substitution_count >= 2


def test_stats(c):
    s = c.stats("O magistrado decidiu sobre a controvérsia.")
    assert s["tokens_saved"] > 0
    assert s["savings_pct"] > 0
    assert s["original_tokens"] > s["compressed_tokens"]


def test_safe_only_skips_unsafe():
    c_safe = Compressor(domain="legal-pt", model="gpt-4o", safe_only=True)
    # acusação e dilação são unsafe
    result = c_safe.compress("A acusação definiu a dilação.")
    # acusação: unsafe → não substitui
    assert "acusação" in result.text


def test_comarca_sem_saving_em_contexto(c):
    # comarca em contexto = 1 tok (igual a foro) → não deve substituir
    result = c.compress("A comarca decidiu o caso.")
    assert "comarca" in result.text  # não substituído: saving = 0
