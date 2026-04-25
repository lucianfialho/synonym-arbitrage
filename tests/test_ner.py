import pytest
from synonyms import Compressor


@pytest.fixture
def c():
    return Compressor(domain="legal-pt", model="gpt-4o", safe_only=False)


def test_magistrado_nome_proprio_nao_substituido(c):
    # "magistrado de Campinas" → nome próprio, não substitui
    result = c.compress("O magistrado de Campinas proferiu a decisão.")
    assert "magistrado" in result.text


def test_magistrado_generico_substituido(c):
    result = c.compress("O magistrado analisou o pedido.")
    assert "juiz" in result.text


def test_requerente_nome_proprio_protegido(c):
    # "requerente de São Paulo" = nome próprio
    result = c.compress("O requerente de São Paulo recorreu.")
    assert "requerente" in result.text


def test_requerente_generico_substituido(c):
    result = c.compress("O requerente apresentou a petição.")
    assert "autor" in result.text.lower()


def test_multiplos_magistrados_com_e_sem_nome(c):
    text = "O magistrado de Brasília e o magistrado decidiram em conjunto."
    result = c.compress(text)
    assert "magistrado de Brasília" in result.text  # protegido
    assert "juiz decidiram" in result.text or result.substitution_count >= 1


def test_ner_nao_quebra_sem_artigo(c):
    result = c.compress("magistrado decidiu.")
    assert result is not None
