import pytest
from synonyms import Compressor


@pytest.fixture
def c():
    return Compressor(domain="legal-pt", model="gpt-4o", safe_only=False)


def test_requerente_vira_autor_com_artigo(c):
    # requerente (2 tok) → autor (1 tok): saving = 1
    result = c.compress("A requerente apresentou o recurso.")
    assert "autor" in result.text.lower()


def test_magistrado_com_artigo_masculino(c):
    result = c.compress("O magistrado falou.")
    assert result.text.startswith("O juiz")


def test_reclamante_vira_autor(c):
    # reclamante (2 tok) → autor (1 tok)
    result = c.compress("O reclamante recorreu.")
    assert "autor" in result.text.lower()


def test_controvérsia_3_tokens_saving(c):
    result = c.compress("A controvérsia principal é jurídica.")
    assert "disputa" in result.text
    assert result.tokens_saved >= 3


def test_inadimplemento_saving(c):
    result = c.compress("O inadimplemento foi comprovado.")
    assert "mora" in result.text.lower()


def test_uppercase_magistrado(c):
    result = c.compress("O MAGISTRADO do caso.")
    assert "JUIZ" in result.text


def test_sem_match_nao_muda(c):
    result = c.compress("comarca decidiu.")
    assert result.text == "comarca decidiu."
    assert result.tokens_saved == 0
