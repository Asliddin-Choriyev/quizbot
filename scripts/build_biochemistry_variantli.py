import os
import re
import csv
import random
from pathlib import Path
import pymupdf as fitz

# Set seed for reproducibility
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
COLLECTIONS_DIR = DATA_DIR / "biokimyo_collections"
COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795258124602_c8353748.pdf"

# Standardize Turkish/accented Latin to clean Uzbek Latin
def to_clean_uzbek(text: str) -> str:
    text = text.replace('ş', 'sh').replace('Ş', 'Sh')
    text = text.replace('ç', 'ch').replace('Ç', 'Ch')
    text = text.replace('ö', "o'").replace('Ö', "O'")
    text = text.replace('ǧ', "g'").replace('Ǧ', "G'")
    text = text.replace('ğ', "g'").replace('Ğ', "G'")
    text = text.replace('’', "'").replace('`', "'").replace('‘', "'").replace('ʼ', "'")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Domain pools for realistic medical biochemistry distractors
DOMAIN_POOLS = {
    "enzymes": [
        "pepsin", "tripsin", "ximotripsin", "enteropeptidaza", "sitratsintaza",
        "piruvatdegidrogenaza", "piruvatdekarboksilaza", "digidrolipoiltransatsetilaza",
        "digidrolipoildegidrogenaza", "nukleoziddifosfatkinaza", "izotsitratdegidrogenaza",
        "suksinatdegidrogenaza", "lipoproteinlipaza", "fosfolipaza", "elastaza",
        "karboksipeptidaza A", "karboksipeptidaza B", "aminopeptidaza", "ATF-sintaza",
        "suksinat-KoQ-reduktaza", "NADH-degidrogenaza", "sitoxromoksidaza",
        "gamma-glutamiltransferaza", "laktatdegidrogenaza", "glyukokinaza"
    ],
    "metabolites": [
        "piruvat", "atsetil-KoA", "oksaloatsetat", "sitrat", "suksinat",
        "suksinil-KoA", "fumarat", "malat", "izotsitrat", "alfa-ketoglutarat",
        "laktat", "glyukoza", "glikogen", "mochevina", "kreatin", "ammiak"
    ],
    "energy_coenzymes": [
        "ATF", "ADF", "AMF", "GTF", "GDF", "NAD+", "NADH", "FAD", "FADH2",
        "Koenzim Q (ubixinon)", "sitoxrom c", "FMN", "KoA-SH"
    ],
    "amino_acids": [
        "lizin", "arginin", "gistidin", "leytsin", "izoleytsin", "valin",
        "metionin", "treonin", "fenilalanin", "triptofan", "tirozin",
        "glutamat", "aspartat", "glitsin", "alanin", "serin", "sistein"
    ],
    "toxic_products": [
        "indol va skatol", "putressin va kadaverin", "krezol", "fenol",
        "vodorod sulfid (H2S), merkaptanlar", "ammiak", "metan"
    ],
    "lipids": [
        "xolesterol", "xolestanol va koprastanol", "triatsilglitserollar",
        "fosfatidilxolin", "fosfatidilserin", "fosfatidiletanolamin",
        "sfingomielinlar", "serebrozidlar", "gangliozidlar", "lipoproteinlar (LP)"
    ],
    "fatty_acids": [
        "olein, linol, linolen", "miristin, palmitin, stearin",
        "linol, linolen", "araxidon kislotasi", "palmitin, stearin"
    ],
    "organelles": [
        "mitoxondriyalarning ichki membranasi", "mitoxondriyalarning tashqi membranasi",
        "lizosomalar membranasi", "endoplazmatik retikulum membranasi",
        "Golji apparati membranasi", "yadro membranasi", "plazmatik membrana",
        "peroksisomalar", "sitozol va mitoxondriyalarda"
    ],
    "hormones": [
        "gastrin, gistamin", "sekretin gormoni", "xolesistokinin (pankreozimin)",
        "insulin", "glyukagon", "adrenalin", "steroid gormonlar"
    ],
    "processes": [
        "katabolizm, anabolizm", "oksidlanishli fosforillanish",
        "substratli fosforillanish", "sitrat sikli (Krebs sikli)",
        "beta-oksidlanish", "passiv diffuziya, aktiv transport",
        "glyukoza anaerob oksidlanishi", "oqsil gidrolizi va chirishi",
        "oqsillarning denaturatsiyasi", "elektron transport zanjiri"
    ]
}

def generate_distractors(correct_ans: str, question_text: str, all_answers: list) -> list:
    norm_ans = correct_ans.strip().rstrip('.')
    low_ans = norm_ans.lower()

    # 1. Number of items e.g. "3 ta", "2 ta", "1 ta", "12 ta", "11 ta", "0 ta"
    m_ta = re.match(r'^(\d+)\s*ta\.?$', low_ans)
    if m_ta:
        n = int(m_ta.group(1))
        pool = [f"{n+1} ta", f"{max(0, n-1)} ta", f"{n+2} ta", f"{n+3} ta", f"{max(0, n-2)} ta"]
        cands = [x for x in pool if x.lower() != low_ans]
        random.shuffle(cands)
        return cands[:3]

    # 2. Number sequences / lists e.g. "2 va 3 ta", "8 ta kattalarda, 10 ta bolalarda"
    if "kattalarda" in low_ans and "bolalarda" in low_ans:
        return [
            "10 ta kattalarda, 12 ta bolalarda",
            "6 ta kattalarda, 8 ta bolalarda",
            "12 ta kattalarda, 14 ta bolalarda"
        ]
    if low_ans in ["2 va 3 ta", "2 ta va 3 ta"]:
        return ["3 va 2 ta", "1 va 2 ta", "3 va 4 ta"]

    # 3. Simple numbers / counts
    if low_ans.isdigit():
        n = int(low_ans)
        return [str(n + 1), str(max(1, n - 1)), str(n + 2)]

    # 4. Grams / weights
    if low_ans == "35 g":
        return ["70 g", "15 g", "100 g"]
    if low_ans == "400 g":
        return ["200 g", "600 g", "100 g"]
    if "35–65 g/l" in low_ans or "35-65 g/l" in low_ans:
        return ["65–85 g/l", "20–40 g/l", "10–25 g/l"]
    if "%" in low_ans:
        if "1%" in low_ans:
            return ["taxminan 10% issiqlik sifatida", "taxminan 5% issiqlik sifatida", "taxminan 25% issiqlik sifatida"]
        if "13%" in low_ans:
            return ["25% i ATFda to'planadi", "50% i ATFda to'planadi", "5% i ATFda to'planadi"]

    # 5. pH values
    if "1,5 – 2,0" in low_ans or "1.5 - 2.0" in low_ans:
        return ["3,5 – 4,5", "6,8 – 7,2", "7,5 – 8,0"]
    if low_ans in ["3,5", "3.5"]:
        return ["1,5 – 2,0", "6,8 – 7,0", "7,8 – 8,2"]
    if "1 – 2,5" in low_ans or "1 - 2.5" in low_ans:
        return ["3,0 – 4,0", "5,5 – 6,5", "7,2 – 7,8"]

    # 6. Check domain pools
    for pool_name, pool in DOMAIN_POOLS.items():
        matched = False
        for item in pool:
            if item.lower() == low_ans or (len(item) > 4 and item.lower() in low_ans):
                matched = True
                break
        if matched:
            cands = [p for p in pool if p.lower() != low_ans and p.lower() not in low_ans and low_ans not in p.lower()]
            random.shuffle(cands)
            if len(cands) >= 3:
                return cands[:3]

    # 7. Fallback: similar length answers from all parsed answers
    target_len = len(norm_ans)
    clean_all = []
    seen = {low_ans}
    for a in all_answers:
        ca = to_clean_uzbek(a).strip().rstrip('.')
        ca_low = ca.lower()
        if ca_low not in seen and len(ca) <= 90 and len(ca) >= 3:
            seen.add(ca_low)
            clean_all.append(ca)

    clean_all.sort(key=lambda x: abs(len(x) - target_len))
    selected = clean_all[:3]

    # Safe biochemistry defaults if needed
    defaults = [
        "oksidlanish-fosforillanish jarayoni",
        "fermentativ faollikning oshishi",
        "glikoliz va Krebs sikli",
        "hujayra ichi transporti"
    ]
    for d in defaults:
        if len(selected) >= 3:
            break
        if d.lower() not in [s.lower() for s in selected] and d.lower() != low_ans:
            selected.append(d)

    return selected[:3]

def parse_pdf():
    doc = fitz.open(PDF_PATH)
    full_text = ''
    for page in doc:
        full_text += page.get_text() + '\n'

    pattern = re.compile(r'(\d+)\.\s*(.*?)\s*\n\s*Javob:\s*(.*?)(?=\n\s*\d+\.|\Z)', re.DOTALL | re.IGNORECASE)
    matches = pattern.findall(full_text)
    
    questions = []
    for num_str, q_body, ans_str in matches:
        num = int(num_str)
        q_clean = to_clean_uzbek(q_body)
        a_clean = to_clean_uzbek(ans_str)
        
        # Specific overrides for answers > 95 characters
        if num == 45:
            a_clean = "H+ - ATFaza (protonlarni o'tkazib elektrokimyoviy potensial hosil qiluvchi nasos)"
        elif num == 67:
            a_clean = "Elektronlar to'g'ridan-to'g'ri kislorodga o'tib H2O2 hosil bo'ladi (ATF sintezlanmaydi)"
            
        questions.append({
            "num": num,
            "question": q_clean,
            "answer": a_clean
        })
        
    return questions

def build_collection():
    raw_questions = parse_pdf()
    print(f"Parsed {len(raw_questions)} questions from PDF.")
    
    all_answers = [q["answer"] for q in raw_questions]
    rows = []
    
    for item in raw_questions:
        num = item["num"]
        q_text = item["question"]
        correct_ans = item["answer"].strip().rstrip('.')
        
        # Generate 3 distractors
        distractors = generate_distractors(correct_ans, q_text, all_answers)
        
        # Ensure lengths <= 95
        correct_opt = correct_ans[:95]
        clean_distractors = [d[:95] for d in distractors[:3]]
        
        # Ensure 4 unique options
        seen_opts = {correct_opt.lower()}
        final_distractors = []
        for d in clean_distractors:
            if d.lower() not in seen_opts:
                seen_opts.add(d.lower())
                final_distractors.append(d)
                
        while len(final_distractors) < 3:
            filler = f"Variant {chr(66 + len(final_distractors))}"
            final_distractors.append(filler)
            
        all_opts = [correct_opt] + final_distractors
        random.shuffle(all_opts)
        correct_letter = chr(65 + all_opts.index(correct_opt))
        
        # Truncate question if needed (Telegram limit: 295)
        if len(q_text) > 295:
            q_text = q_text[:292] + "..."
            
        explanation = f"To'g'ri javob: {correct_opt}"
        if len(explanation) > 200:
            explanation = explanation[:197] + "..."
            
        rows.append({
            "question": q_text,
            "option_a": all_opts[0],
            "option_b": all_opts[1],
            "option_c": all_opts[2],
            "option_d": all_opts[3],
            "correct_answer": correct_letter,
            "explanation": explanation,
            "topic": "Biokimyo variantli",
            "difficulty": "Medium",
            "timer": 25,
            "image": ""
        })
        
    csv_filename = "biokimyo_variantli_209.csv"
    csv_path = COLLECTIONS_DIR / csv_filename
    with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "question", "option_a", "option_b", "option_c", "option_d",
            "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
        ])
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Successfully generated {csv_path} with {len(rows)} questions!")
    return rows

if __name__ == "__main__":
    build_collection()
