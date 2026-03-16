"""
RAG (Retrieval-Augmented Generation) para reglas de golf.

Indexa el archivo de reglas en chunks y busca los mas relevantes
para una pregunta dada, usando TF-IDF + cosine similarity.
"""

import os
import re
import math
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RULES_FILE = os.path.join(DATA_DIR, "reglas_golf_2023.txt")

# Cache global
_chunks: list[dict] = []
_idf: dict[str, float] = {}
_tfidf_vectors: list[dict[str, float]] = []


def _tokenize(text: str) -> list[str]:
    """Tokeniza texto en palabras lowercase, removiendo puntuacion."""
    text = text.lower()
    text = re.sub(r'[^\w\sáéíóúñü]', ' ', text)
    return [w for w in text.split() if len(w) > 1]


def _build_chunks(text: str, chunk_size: int = 800, overlap: int = 200) -> list[dict]:
    """Divide el texto en chunks por secciones de reglas."""
    chunks = []

    # Dividir por reglas principales (========)
    sections = re.split(r'={10,}\n(REGLA \d+[^=]*)\n={10,}', text)

    current_rule = "GENERAL"
    for i, section in enumerate(sections):
        if section.strip().startswith("REGLA "):
            current_rule = section.strip()
            continue

        if not section.strip():
            continue

        # Dividir secciones largas en sub-chunks por sub-reglas
        sub_sections = re.split(r'\n(?=\d+\.\d+[a-z]?\s)', section)

        buffer = ""
        for sub in sub_sections:
            if len(buffer) + len(sub) > chunk_size and buffer:
                chunks.append({
                    "rule": current_rule,
                    "text": f"{current_rule}\n{buffer.strip()}",
                })
                # Overlap: mantener las ultimas lineas
                lines = buffer.strip().split('\n')
                overlap_text = '\n'.join(lines[-3:]) if len(lines) > 3 else ""
                buffer = overlap_text + "\n" + sub
            else:
                buffer += "\n" + sub

        if buffer.strip():
            chunks.append({
                "rule": current_rule,
                "text": f"{current_rule}\n{buffer.strip()}",
            })

    # Agregar seccion de definiciones y penalidades como chunks separados
    for header in ["DEFINICIONES IMPORTANTES", "PENALIDADES RESUMEN", "SECCION "]:
        pattern = rf'={10,}\n({header}[^=]*)\n={10,}\n(.*?)(?=\n={10,}|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)
        for title, content in matches:
            if len(content.strip()) > 50:
                chunks.append({
                    "rule": title.strip(),
                    "text": f"{title.strip()}\n{content.strip()}",
                })

    return chunks


def _tf(tokens: list[str]) -> dict[str, float]:
    """Calcula term frequency normalizada."""
    counts = Counter(tokens)
    total = len(tokens)
    if total == 0:
        return {}
    return {word: count / total for word, count in counts.items()}


def _compute_idf(all_token_sets: list[set[str]]) -> dict[str, float]:
    """Calcula IDF sobre todos los chunks."""
    n = len(all_token_sets)
    idf = {}
    all_words = set()
    for token_set in all_token_sets:
        all_words.update(token_set)

    for word in all_words:
        doc_count = sum(1 for ts in all_token_sets if word in ts)
        idf[word] = math.log((n + 1) / (doc_count + 1)) + 1

    return idf


def _tfidf(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    """Calcula vector TF-IDF."""
    tf_vals = _tf(tokens)
    return {word: tf_val * idf.get(word, 1.0) for word, tf_val in tf_vals.items()}


def _cosine_similarity(v1: dict[str, float], v2: dict[str, float]) -> float:
    """Calcula similitud coseno entre dos vectores sparse."""
    common = set(v1.keys()) & set(v2.keys())
    if not common:
        return 0.0

    dot = sum(v1[w] * v2[w] for w in common)
    norm1 = math.sqrt(sum(v * v for v in v1.values()))
    norm2 = math.sqrt(sum(v * v for v in v2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (norm1 * norm2)


def _ensure_index():
    """Construye el indice si no existe."""
    global _chunks, _idf, _tfidf_vectors

    if _chunks:
        return

    if not os.path.exists(RULES_FILE):
        return

    with open(RULES_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    _chunks = _build_chunks(text)

    # Tokenizar todos los chunks
    all_tokens = [_tokenize(c["text"]) for c in _chunks]
    all_token_sets = [set(t) for t in all_tokens]

    # Calcular IDF
    _idf = _compute_idf(all_token_sets)

    # Calcular TF-IDF para cada chunk
    _tfidf_vectors = [_tfidf(tokens, _idf) for tokens in all_tokens]


def search(query: str, top_k: int = 4) -> str:
    """
    Busca los chunks mas relevantes para una pregunta.
    Retorna el texto concatenado de los top_k chunks.
    """
    _ensure_index()

    if not _chunks:
        return ""

    # Expandir query con sinonimos comunes de golf
    synonyms = {
        "drop": "dropear alivio dropeada",
        "dropear": "drop alivio dropeada",
        "agua": "penalidad agua temporal charco lateral",
        "bunker": "arena bunker trampa",
        "green": "green putting putt bandera hoyo",
        "perdida": "perdida fuera limites provisional",
        "fuera": "fuera limites perdida provisional",
        "injugable": "injugable alivio lateral distancia",
        "obstruccion": "obstruccion camino aspersor inamovible movible",
        "impedimento": "impedimento suelto piedra hoja rama",
        "penalidad": "penalidad golpe golpes descalificacion",
        "penalty": "penalidad golpe golpes",
        "hoyo": "hoyo embocar embocada",
        "tarjeta": "tarjeta score puntuacion marcador",
        "handicap": "handicap discapacidad modificacion",
        "provisional": "provisional perdida fuera limites",
        "empotrada": "empotrada pique enterrada plugged",
        "rough": "rough area general cesped alto",
        "fairway": "fairway area general cesped corto",
        "asiento": "asiento mejorado preferential lies tee up",
    }

    expanded = query
    for key, expansion in synonyms.items():
        if key in query.lower():
            expanded += " " + expansion

    query_tokens = _tokenize(expanded)
    query_vector = _tfidf(query_tokens, _idf)

    # Calcular similitudes
    scores = []
    for i, chunk_vector in enumerate(_tfidf_vectors):
        sim = _cosine_similarity(query_vector, chunk_vector)
        scores.append((sim, i))

    # Ordenar por similitud descendente
    scores.sort(reverse=True)

    # Tomar top_k unicos (evitar chunks duplicados de la misma regla)
    seen_rules = set()
    results = []
    for sim, idx in scores:
        if sim <= 0:
            break
        rule = _chunks[idx]["rule"]
        if rule not in seen_rules or len(results) < top_k:
            results.append(_chunks[idx]["text"])
            seen_rules.add(rule)
        if len(results) >= top_k:
            break

    return "\n\n---\n\n".join(results)
