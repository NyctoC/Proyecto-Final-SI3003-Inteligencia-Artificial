"""
Retriever RAG basado en TF-IDF (sin descargas de modelos de embeddings).

Diseno
------
- Carga los documentos de `corpus/` (archivos .md / .txt).
- Trocea cada documento en fragmentos (por parrafos, agrupando los muy cortos).
- Vectoriza los fragmentos con TF-IDF (scikit-learn) y responde consultas por
  similitud coseno, devolviendo los top-k fragmentos con su fuente para citar.

Es deterministico, ligero y 100% offline: ideal para reproducibilidad.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RAIZ = Path(__file__).resolve().parents[1]
DIR_CORPUS = RAIZ / "corpus"

# Stopwords en espanol (lista corta y suficiente para TF-IDF de dominio).
STOPWORDS_ES = [
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con",
    "contra", "cual", "cuando", "de", "del", "desde", "donde", "durante", "e",
    "el", "ella", "ellas", "ellos", "en", "entre", "era", "es", "esa", "ese",
    "eso", "esta", "estan", "este", "esto", "estos", "ha", "hay", "la", "las",
    "le", "les", "lo", "los", "mas", "me", "mi", "mucho", "muy", "no", "o",
    "para", "pero", "poco", "por", "porque", "que", "se", "sea", "ser", "si",
    "sin", "sobre", "solo", "son", "su", "sus", "tan", "te", "tiene", "un",
    "una", "uno", "unos", "y", "ya",
]


@dataclass
class Fragmento:
    texto: str
    fuente: str      # nombre de archivo
    indice: int      # posicion del fragmento dentro de su documento


@dataclass
class ResultadoBusqueda:
    texto: str
    fuente: str
    score: float


def _trocear(texto: str, min_chars: int = 120) -> list[str]:
    """Divide por parrafos (lineas en blanco) y agrupa los muy cortos."""
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    fragmentos: list[str] = []
    buffer = ""
    for p in parrafos:
        # Ignora encabezados sueltos muy cortos juntandolos con lo siguiente.
        candidato = (buffer + "\n" + p).strip() if buffer else p
        if len(candidato) < min_chars:
            buffer = candidato
        else:
            fragmentos.append(candidato)
            buffer = ""
    if buffer:
        fragmentos.append(buffer)
    return fragmentos


class RagRetriever:
    """Indice TF-IDF sobre el corpus con busqueda por similitud coseno."""

    def __init__(self, dir_corpus: str | Path = DIR_CORPUS) -> None:
        self.dir_corpus = Path(dir_corpus)
        self.fragmentos: list[Fragmento] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matriz = None

    def cargar(self) -> "RagRetriever":
        archivos = sorted(self.dir_corpus.glob("*.md")) + sorted(
            self.dir_corpus.glob("*.txt")
        )
        if not archivos:
            raise FileNotFoundError(
                f"No se encontraron documentos en {self.dir_corpus}"
            )
        self.fragmentos = []
        for archivo in archivos:
            texto = archivo.read_text(encoding="utf-8")
            for i, frag in enumerate(_trocear(texto)):
                self.fragmentos.append(Fragmento(texto=frag, fuente=archivo.name, indice=i))

        corpus_textos = [f.texto for f in self.fragmentos]
        self.vectorizer = TfidfVectorizer(
            stop_words=STOPWORDS_ES,
            ngram_range=(1, 2),
            lowercase=True,
            strip_accents="unicode",
        )
        self.matriz = self.vectorizer.fit_transform(corpus_textos)
        return self

    def search(self, query: str, k: int = 3) -> list[ResultadoBusqueda]:
        if self.vectorizer is None or self.matriz is None:
            raise RuntimeError("El indice no esta cargado. Llama a cargar() primero.")
        if not query or not query.strip():
            return []
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matriz)[0]
        orden = sims.argsort()[::-1][:k]
        resultados = []
        for idx in orden:
            score = float(sims[idx])
            if score <= 0:
                continue
            frag = self.fragmentos[idx]
            resultados.append(
                ResultadoBusqueda(texto=frag.texto, fuente=frag.fuente, score=round(score, 4))
            )
        return resultados


# Singleton perezoso para reutilizar el indice (util en el dashboard/agente).
_INDICE: RagRetriever | None = None


def get_retriever() -> RagRetriever:
    global _INDICE
    if _INDICE is None:
        _INDICE = RagRetriever().cargar()
    return _INDICE
