import re
from pathlib import Path
from typing import List, Dict, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class CorpusRetriever:
    def __init__(self, corpus_dir: str):
        self.corpus_dir = Path(corpus_dir)
        self.docs: List[Dict] = []
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=70000,
            min_df=1,
        )
        self.matrix = None

    def load(self) -> None:
        if not self.corpus_dir.exists():
            raise FileNotFoundError(f"Corpus directory not found: {self.corpus_dir}")

        for path in self.corpus_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".txt", ".md", ".html", ".htm", ".json", ".csv"}:
                text = self._read(path)
                text = self._clean(text)
                if len(text) < 40:
                    continue
                domain = self._infer_domain(path, text)
                for idx, chunk in enumerate(self._chunk(text)):
                    self.docs.append({
                        "id": f"{path.name}#{idx}",
                        "title": path.stem,
                        "path": str(path),
                        "domain": domain,
                        "text": chunk,
                    })

        if not self.docs:
            raise RuntimeError("No usable corpus files found. Check the --corpus path.")

        self.matrix = self.vectorizer.fit_transform([d["text"] for d in self.docs])

    def search(self, query: str, domain: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        if self.matrix is None:
            raise RuntimeError("Call load() before search().")

        qv = self.vectorizer.transform([query])
        scores = cosine_similarity(qv, self.matrix)[0]
        results = []

        for i, score in enumerate(scores):
            doc = self.docs[i]
            if domain and doc["domain"] != domain:
                continue
            results.append({**doc, "score": float(score)})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")

    def _clean(self, text: str) -> str:
        text = re.sub(r"<script.*?</script>", " ", text, flags=re.I | re.S)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _chunk(self, text: str, size: int = 1300, overlap: int = 200) -> List[str]:
        words = text.split()
        if len(words) <= size:
            return [text]

        chunks = []
        step = max(1, size - overlap)
        for start in range(0, len(words), step):
            chunk = " ".join(words[start:start + size])
            if len(chunk) > 120:
                chunks.append(chunk)
        return chunks

    def _infer_domain(self, path: Path, text: str) -> str:
        p = str(path).lower()
        t = text[:1000].lower()
        joined = p + " " + t
        if "hackerrank" in joined:
            return "hackerrank"
        if "claude" in joined or "anthropic" in joined:
            return "claude"
        if "visa" in joined:
            return "visa"
        return "unknown"
