import sys
import pathlib

# Ensure project root is on sys.path so `from src.matcher import ...` works
# when running this file as a script (python src\main.py) and when running
# tests from the project root.
project_root = pathlib.Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.matcher import DiseaseMatcher


def main():
    csv_path = "data/diseases.csv"
    matcher = DiseaseMatcher()
    matcher.fit_from_csv(csv_path)
    print("AI-based Disease Matcher (prototype)")
    print("Type symptoms separated by commas or natural language. Type 'quit' to exit.")
    while True:
        try:
            user = input("\nEnter symptoms: ")
        except (KeyboardInterrupt, EOFError):
            print('\nGoodbye')
            break
        if not user:
            continue
        if user.strip().lower() in ("quit", "exit"):
            print("Goodbye")
            break
        text = user.strip()
        low = text.lower()
        # Allow checking status of the loaded data and reloading the CSV at runtime
        if low == 'status':
            path = getattr(matcher, 'csv_path', None)
            n = len(matcher.df) if getattr(matcher, 'df', None) is not None else 0
            print(f"Loaded CSV: {path if path else 'None'}")
            print(f"Entries loaded: {n}")
            continue
        if low.startswith('reload'):
            # support: 'reload' or 'reload <path>'
            parts = text.split(None, 1)
            if len(parts) == 2 and parts[1].strip():
                new_path = parts[1].strip()
            else:
                new_path = matcher.csv_path or csv_path
            try:
                matcher.fit_from_csv(new_path)
                print(f"Reloaded CSV from: {new_path}")
            except Exception as e:
                print(f"Failed to reload CSV: {e}")
            continue
        # Support disease lookup commands:
        #  - "find <disease name>"
        #  - "disease: <disease name>"
        if low.startswith('find ') or low.startswith('disease:'):
            # extract name
            if low.startswith('find '):
                name = text[5:].strip()
            else:
                # disease: prefix
                name = text.split(':', 1)[1].strip()
            if not name:
                print("Please provide a disease name after 'find' or 'disease:'")
                continue
            matches = matcher.find_by_name(name, exact=False, limit=10)
            if not matches:
                print("No disease found with that name. Try a different name or check spelling.")
                continue
            print(f"Found {len(matches)} disease(s):")
            for disease, symptoms, tips in matches:
                print(f" - {disease}")
                print(f"   Symptoms: {symptoms}")
                if tips:
                    print(f"   Tips: {tips}")
            continue

        results = matcher.match(user, top_k=3, threshold=0.15)
        if not results:
            print("No confident match found. Try adding more symptoms or check spelling.")
            continue
        print("Matches:")
        for item in results:
            # results are (disease, score, tips, matched_keywords)
            if len(item) == 4:
                disease, score, tips, matched = item
            else:
                # backward compatibility
                disease, score, tips = item
                matched = []
            print(f" - {disease} (score: {score:.2f})")
            if tips:
                print(f"   Tips: {tips}")
            if matched:
                print(f"   Matched keywords: {', '.join(matched)}")


if __name__ == '__main__':
    main()
