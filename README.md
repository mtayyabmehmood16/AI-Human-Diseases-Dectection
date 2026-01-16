AI-based Human Disease Detection (prototype)

Overview

This simple Python prototype lets a user type symptoms and matches them against a CSV database of diseases using a TF-IDF + cosine-similarity model. It returns the best-matching disease(s), a similarity score, and healthy tips. The matcher now supports a simple synonyms mapping and can be expanded to larger synthetic datasets for prototyping.

Files

- data/diseases.csv - CSV datastore (disease,symptoms,tips)
- data/symptoms_synonyms.csv - optional canonical->synonyms mapping used to normalize text
- scripts/generate_diseases.py - generator to synthesize an expanded CSV (default 500 entries)
- src/matcher.py - core matching logic (DiseaseMatcher) with synonym expansion and explanations
- src/main.py - small CLI to enter symptoms and get results
- tests/test_matcher.py - a small pytest to check matching

Quick start (PowerShell)

Create and activate virtual env (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the CLI app:

```powershell
python src\main.py
```

Run tests:

```powershell
python -m pytest -q
```

Generate a larger dataset (optional)

Run the generator to create `data/diseases_expanded.csv` with 500 entries (default):

```powershell
python scripts\generate_diseases.py --out data\diseases_expanded.csv --count 500
```

Then run the matcher against the expanded file by changing the CSV path in `src/main.py` or calling `DiseaseMatcher().fit_from_csv('data/diseases_expanded.csv')`.

Notes

- This is a prototype for education and experimentation only. Do NOT use for real medical advice. For production, obtain high-quality annotated datasets, integrate medical ontologies, add validation and security, and consult clinical experts.
