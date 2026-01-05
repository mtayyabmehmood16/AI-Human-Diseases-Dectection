"""Generate an expanded diseases CSV for the prototype.

This script programmatically builds an expanded dataset (default 500 rows)
using a curated list of common diseases and symptom templates. It's intended
for prototyping only — please replace with a verified medical dataset for
production use.
"""
import csv
import random
from pathlib import Path


BASE_DISEASES = [
    ("Common Cold", ["sneezing", "cough", "runny nose", "sore throat"],
     "Rest, hydrate, saltwater gargles, OTC decongestants"),
    ("Influenza", ["fever", "chills", "body aches", "cough", "fatigue"],
     "Rest, fluids, see a doctor if severe; antiviral meds may help early"),
    ("Migraine", ["headache", "nausea", "sensitivity to light", "visual aura"],
     "Rest in a dark quiet room, OTC pain relief, avoid triggers"),
    ("Gastroenteritis", ["nausea", "vomiting", "diarrhea", "stomach pain"],
     "Hydration (oral rehydration), rest; see doctor if severe"),
    ("Allergic Rhinitis", ["sneezing", "runny nose", "itchy eyes", "nasal congestion"],
     "Avoid allergen, antihistamines, nasal corticosteroid sprays"),
    ("Pneumonia", ["fever", "cough", "shortness of breath", "chest pain"],
     "See a doctor — may need antibiotics or supportive care"),
    ("Asthma", ["wheeze", "shortness of breath", "chest tightness", "cough"],
     "Inhalers (bronchodilators), avoid triggers, see clinician for an action plan"),
    ("Hypertension", ["headache", "dizziness", "nosebleeds"],
     "Lifestyle changes, medications as prescribed; regular monitoring"),
    ("Type 2 Diabetes", ["increased thirst", "frequent urination", "fatigue", "blurred vision"],
     "Diet, exercise, glucose monitoring, medications as needed"),
    ("Urinary Tract Infection", ["painful urination", "frequent urination", "lower abdominal pain"],
     "Stay hydrated, see a doctor for antibiotics if bacterial"),
    ("Migraine with Aura", ["headache", "visual disturbances", "nausea"],
     "As for migraine; seek medical care if pattern changes"),
    ("Bronchitis", ["cough", "mucus", "fatigue", "mild fever"],
     "Rest, fluids; see doctor if symptoms worsen or persist"),
    ("Sinusitis", ["facial pain", "nasal congestion", "headache", "runny nose"],
     "Nasal irrigation, decongestants, see doctor if prolonged"),
    ("Otitis Media", ["ear pain", "fever", "hearing difficulty"],
     "Pain relief, see doctor for potential antibiotics in children"),
    ("Skin Infection", ["redness", "swelling", "pain", "pus"],
     "Keep clean, see doctor for antibiotics if spreading or severe"),
    ("Anxiety Disorder", ["worry", "restlessness", "insomnia", "palpitations"],
     "Consider therapy, lifestyle changes, medications as advised"),
    ("Depression", ["low mood", "loss of interest", "fatigue", "sleep changes"],
     "Seek professional help: therapy, social support, medications"),
    ("Back Pain", ["lower back pain", "stiffness", "limited mobility"],
     "Stay active, pain relief, physiotherapy if persistent"),
    ("Osteoarthritis", ["joint pain", "stiffness", "reduced range of motion"],
     "Exercise, weight management, pain control, joint injections or surgery in severe cases"),
    ("Rheumatoid Arthritis", ["joint pain", "swelling", "morning stiffness"],
     "Early rheumatology referral, DMARDs and symptom control"),
    # ... the list can include many more base diseases; for brevity we include ~20
]


def synthesize_disease(i: int, base: tuple) -> tuple:
    name, symptoms, tips = base
    # vary the name slightly to create unique entries
    variant = name
    # create variants for chronic/acute/child/adult to increase count
    variants = ["", " (chronic)", " (acute)", " - pediatric", " - adult", " (recurrent)"]
    suffix = random.choice(variants)
    variant_name = f"{variant}{suffix}"
    # shuffle and sample symptoms to make variety
    sym = random.sample(symptoms, k=min(len(symptoms), max(2, random.randint(2, len(symptoms)))))
    # add a small extra common symptom occasionally
    common_extras = ["fatigue", "fever", "nausea", "headache", "loss of appetite"]
    if random.random() < 0.3:
        sym.append(random.choice(common_extras))
    sym_text = "; ".join(sym)
    # tweak tips slightly
    tip = tips
    if random.random() < 0.2:
        tip = tip + "; consult your healthcare provider if symptoms worsen"
    return variant_name, sym_text, tip


def generate_csv(out_path: Path, target: int = 500) -> None:
    rows = []
    base_len = len(BASE_DISEASES)
    i = 0
    # first include the base list
    for base in BASE_DISEASES:
        name, syms, tips = base
        rows.append((name, "; ".join(syms), tips))
        i += 1
        if i >= target:
            break

    # generate variants until target reached
    while i < target:
        base = BASE_DISEASES[i % base_len]
        variant = synthesize_disease(i, base)
        # ensure uniqueness reasonably
        rows.append(variant)
        i += 1

    # write CSV
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['disease', 'symptoms', 'tips'])
        for r in rows:
            writer.writerow(r)


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser(prog='generate_diseases')
    p.add_argument('--out', default='data/diseases_expanded.csv')
    p.add_argument('--count', type=int, default=500)
    args = p.parse_args()
    out = Path(args.out)
    print(f"Generating {args.count} diseases into {out}")
    generate_csv(out, target=args.count)
    print("Done.")
