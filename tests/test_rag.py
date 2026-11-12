"""Tests de la Task 6: retriever RAG con TF-IDF."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.rag import RagRetriever, _trocear  # noqa: E402


def _retriever():
    return RagRetriever().cargar()


def test_indice_carga_fragmentos():
    r = _retriever()
    assert len(r.fragmentos) > 0
    # Debe haber fragmentos de varios archivos del corpus.
    fuentes = {f.fuente for f in r.fragmentos}
    assert len(fuentes) >= 3


def test_busqueda_recomendaciones_salud():
    r = _retriever()
    res = r.search("que debo hacer para protegerme del aire contaminado", k=3)
    assert res, "no devolvio resultados"
    fuentes = [x.fuente for x in res]
    # El doc de recomendaciones de salud debe estar en el top-k.
    assert any("recomendaciones" in f or "preguntas_frecuentes" in f for f in fuentes)


def test_busqueda_episodios_criticos():
    r = _retriever()
    res = r.search("protocolo de alerta y emergencia pico y placa episodios", k=3)
    assert res
    assert any("episodios_criticos" in x.fuente for x in res)


def test_busqueda_categorias_pm25():
    r = _retriever()
    res = r.search("rango de microgramos categoria buena moderada danina", k=3)
    assert res
    assert any("categorias_ica" in x.fuente for x in res)


def test_resultados_tienen_fuente_y_score():
    r = _retriever()
    res = r.search("PM2.5 salud", k=2)
    for item in res:
        assert item.fuente.endswith(".md")
        assert 0.0 < item.score <= 1.0
        assert item.texto


def test_query_vacia_devuelve_lista_vacia():
    r = _retriever()
    assert r.search("", k=3) == []
    assert r.search("   ", k=3) == []


def test_trocear_agrupa_cortos():
    texto = "# Titulo corto\n\nEste es un parrafo suficientemente largo como para superar el minimo de caracteres exigido por la funcion de troceo del indice."
    frags = _trocear(texto, min_chars=120)
    # El titulo corto debe quedar unido al parrafo largo, no suelto.
    assert len(frags) == 1
    assert "Titulo corto" in frags[0]
