from typing import List, Tuple, Dict
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pathlib import Path
import csv
import re
import difflib


def load_synonyms(path: str) -> Dict[str, List[str]]:
    p = Path(path)
    if not p.exists():
        return {}
    mapping: Dict[str, List[str]] = {}
    with p.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            canon = row.get('canonical', '').strip().lower()
            syns = row.get('synonyms', '')
            if not canon:
                continue
            parts = [s.strip().lower() for s in syns.split(';') if s.strip()]
            mapping[canon] = parts
    return mapping


class DiseaseMatcher:
    """Load diseases from a CSV and match free-text symptom input to diseases.

    CSV format (header): disease,symptoms,tips
    - symptoms should be a short text (semicolon or comma separated symptoms is fine)
    """

    def __init__(self):
        self.df = None
        self.vectorizer = None
        self.tfidf_matrix = None
        self.synonyms = {}
        self.vocab = set()
        self.csv_path = None
        self.csv_mtime = None

    def _normalize_text(self, text: str) -> str:
        if text is None:
            return ""
        # basic normalization: lowercase and replace separators with spaces
        return text.lower().replace(";", " ").replace(",", " ")

    def _expand_with_synonyms(self, text: str) -> str:
        # expand text by replacing canonical synonyms with their variants
        s = text
        for canon, syns in self.synonyms.items():
            # replace canonical with itself and synonyms
            for syn in syns:
                if syn and syn in s:
                    s = s.replace(syn, canon)
        return s

    def _tokenize(self, text: str) -> List[str]:
        # extract word-like tokens; keep simple alphanum tokens
        if not text:
            return []
        tokens = re.findall(r"\w+", text.lower())
        return tokens

    def _correct_and_dedup_tokens(self, tokens: List[str]) -> List[str]:
        """Correct tokens by fuzzy-matching against vocabulary and remove duplicates (preserve order)."""
        seen = set()
        out: List[str] = []
        vocab = list(self.vocab)
        for t in tokens:
            if not t:
                continue
            corrected = t
            if t not in self.vocab and vocab:
                # try fuzzy match
                best = difflib.get_close_matches(t, vocab, n=1, cutoff=0.7)
                if best:
                    corrected = best[0]
            if corrected not in seen:
                seen.add(corrected)
                out.append(corrected)
        return out

    def fit_from_csv(self, csv_path: str) -> None:
        self.df = pd.read_csv(csv_path)
        # remember path and mtime for auto-reload
        self.csv_path = str(csv_path)
        try:
            self.csv_mtime = Path(csv_path).stat().st_mtime
        except Exception:
            self.csv_mtime = None
        if 'symptoms' not in self.df.columns:
            raise ValueError("CSV must contain a 'symptoms' column")
        # load synonyms if present (data/symptoms_synonyms.csv)
        self.synonyms = load_synonyms('data/symptoms_synonyms.csv')

        # normalize and expand symptom text
        symptom_texts = (
            self.df['symptoms'].fillna("")
            .apply(self._normalize_text)
            .apply(self._expand_with_synonyms)
            .tolist()
        )
        # build vocabulary from symptom texts and synonyms for fuzzy correction
        vocab = set()
        for txt in symptom_texts:
            for tok in self._tokenize(txt):
                vocab.add(tok)
        # include synonyms and canonicals
        for canon, syns in self.synonyms.items():
            for tok in self._tokenize(canon):
                vocab.add(tok)
            for syn in syns:
                for tok in self._tokenize(syn):
                    vocab.add(tok)
        self.vocab = vocab
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(symptom_texts)

    def _maybe_reload(self):
        """If the CSV file changed on disk since last load, reload it automatically."""
        if not self.csv_path:
            return
        try:
            m = Path(self.csv_path).stat().st_mtime
        except Exception:
            return
        if self.csv_mtime is None or m != self.csv_mtime:
            # reload
            try:
                self.fit_from_csv(self.csv_path)
            except Exception:
                # ignore reload errors for now
                pass

    def match(self, user_symptoms: str, top_k: int = 3, threshold: float = 0.2) -> List[Tuple[str, float, str, List[str]]]:
        """Return up to top_k matches as (disease, score, tips, matched_keywords).

        - score is cosine similarity in [0,1]
        - threshold: minimum score to include a match
        - matched_keywords: a list of symptom keywords from the disease entry that contributed to the match
        """
        # auto-reload if file changed
        self._maybe_reload()

        if self.df is None or self.vectorizer is None:
            raise RuntimeError("Matcher not trained. Call fit_from_csv(csv_path) first.")
        query = self._normalize_text(user_symptoms)
        query = self._expand_with_synonyms(query)
        # tokenize, correct misspellings and remove duplicates
        tokens = self._tokenize(query)
        tokens = self._correct_and_dedup_tokens(tokens)
        query = " ".join(tokens)
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        # get indices sorted by descending similarity
        idx_sorted = np.argsort(-sims)
        results = []
        for idx in idx_sorted[:top_k]:
            score = float(sims[idx])
            if score < threshold:
                continue
            disease = str(self.df.iloc[idx]['disease'])
            tips = str(self.df.iloc[idx]['tips']) if 'tips' in self.df.columns else ""
            # extract matched keywords by intersecting token sets
            disease_sym_text = self._expand_with_synonyms(self._normalize_text(str(self.df.iloc[idx]['symptoms'])))
            query_tokens = set(query.split())
            disease_tokens = set(disease_sym_text.split())
            matched = sorted(list(query_tokens & disease_tokens))
            results.append((disease, score, tips, matched))
        return results

    def find_by_name(self, name: str, exact: bool = False, limit: int = 10) -> List[Tuple[str, str, str]]:
        """Find disease entries by name.

        Returns a list of (disease, symptoms, tips). If exact is True, matches exact disease name
        (case-insensitive). Otherwise performs a case-insensitive substring search and returns up to `limit` results.
        """
        # auto-reload if file changed
        self._maybe_reload()

        if self.df is None:
            raise RuntimeError("Matcher not trained. Call fit_from_csv(csv_path) first.")
        q = name.strip().lower()
        if exact:
            mask = self.df['disease'].fillna("").str.lower() == q
            matches = self.df[mask]
        else:
            mask = self.df['disease'].fillna("").str.lower().str.contains(q)
            matches = self.df[mask].drop_duplicates(subset='disease')
        results = []
        for _, row in matches.head(limit).iterrows():
            results.append((str(row['disease']), str(row.get('symptoms', '')), str(row.get('tips', ''))))
        return results


if __name__ == "__main__":
    # quick smoke when run directly
    m = DiseaseMatcher()
    m.fit_from_csv("data/diseases.csv")
    examples = [
        "I have sneezing and a runny nose",
        "Severe headache with nausea and sensitivity to light",
        "Vomiting and diarrhea after eating"
    ]
    for ex in examples:
        print('Input:', ex)
        print(m.match(ex))
        print()
