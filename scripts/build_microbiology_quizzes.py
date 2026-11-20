import os
import re
import csv
import json
import random
from pathlib import Path
import pymupdf
from PIL import Image
import io

# Set random seed for reproducibility
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
COLLECTIONS_DIR = DATA_DIR / "mikrobiologiya_collections"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)

PDF_FILES = {
    1: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795193336460_45827dcc.pdf",
    2: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795193336460_235029dc.pdf",
    3: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795193336459_ec7a02ba.pdf",
    4: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795193336461_e65a5368.pdf",
}

# Domain pools for realistic distractors
DOMAIN_POOLS = {
    "microscope_parts": [
        "Obyektiv", "Okulyar", "Revolver", "Kondensator", "Tubus", 
        "Makrovint", "Mikrovint", "Buyum stolchasi", "Yorituvchi ko'zgu", "Diafragma"
    ],
    "morphology": [
        "stafilokokk", "streptokokk", "diplokokk", "sartsina", "monokokk", 
        "batsilla", "klostridiya", "vibrion", "spiroxeta", "spirilla", 
        "korinobakteriya", "aktinomitseta", "mikoplazma", "pnevmokokk", 
        "meningokokk", "gonokokk", "salmonella", "sil tayoqchasi", "ichak tayoqchasi"
    ],
    "flagella": [
        "monotrix", "lofotrix", "amfitrix", "peritrix", "politrix"
    ],
    "spores": [
        "markaziy", "terminal", "subterminal", "lateral", "ekssentrik"
    ],
    "staining_methods": [
        "Gram usuli", "Sil-Nilsen usuli", "Romanovskiy - Gimza usuli", "Neysser usuli", 
        "Burri-Gins usuli", "Ojeshko usuli", "Zdrodovskiy usuli", "Lyoffler usuli", "Peshkov usuli"
    ],
    "lab_tools": [
        "bakteriologik halqa", "buyum oynasi", "qoplagich oyna", "qoplovchi oyna", 
        "Paster pipetkasi", "drigalskiy (shpatel) shpateli", "stomatologik lotok", 
        "lotok", "shtativ", "spirt idish, spirtovka", "petri", "laminar boks", "termokonteyner"
    ],
    "scientists": [
        "Antoni Van Levenguk", "Robert Kox", "Lui Paster", "Ilya Mechnikov", 
        "A. Neisser", "T. Escherix", "F. Lyoffler", "A. Vekselbaum", "Berdji", "Rikkets", "A. Sinev"
    ],
    "dyes": [
        "gensian binafsha", "Lyugol eritmasi", "etil", "karbol fuksin", "anilin", 
        "eozin", "metilen ko'ki", "Neyser bo'yog'i", "xrizoidin", "vezuvin", "atsetat sinkasi"
    ],
    "colors": [
        "binafsha", "qizil", "ko'kimtir-binafsha", "rangsiz", "oq rangli", "pushti", "sariq"
    ],
    "spirochetes": [
        "treponema", "borrelia", "leptospira", "kristospira", "spiroxeta"
    ],
    "cell_structures": [
        "peptidoglikan", "murein", "hujayra devori", "kapsula", "xivchin", 
        "kiprikchalar", "nukleoid", "sitoplazma", "ribosoma", "blefaroplast"
    ]
}

def extract_images():
    """Extract and map images from all 4 PDFs directly to question numbers."""
    print("Extracting images from PDFs...")
    saved_count = 0
    q_img_map = {} # (m_idx, q_num) -> rel_path

    for m in range(1, 5):
        doc = pymupdf.open(PDF_FILES[m])
        elements = []
        for p_idx, page in enumerate(doc):
            for b in page.get_text('blocks'):
                text = b[4].strip()
                m_q = re.match(r'^(\d+)\.\s', text)
                if m_q:
                    elements.append((p_idx, 'Q', int(m_q.group(1)), b[1], b[3]))
                elif text.startswith('Javob:'):
                    elements.append((p_idx, 'A', None, b[1], b[3]))
            for img in page.get_images():
                rects = page.get_image_rects(img[0])
                if rects:
                    iy0 = min(r.y0 for r in rects)
                    iy1 = max(r.y1 for r in rects)
                    elements.append((p_idx, 'IMG', img[0], iy0, iy1))
        
        elements.sort(key=lambda x: (x[0], x[3]))
        current_q = None
        for el in elements:
            if el[1] == 'Q':
                current_q = el[2]
            elif el[1] == 'IMG':
                if current_q is not None:
                    xref = el[2]
                    img_data = doc.extract_image(xref)
                    im = Image.open(io.BytesIO(img_data['image']))
                    filename = f"mikro_m{m}_q{current_q:03d}.png"
                    out_path = IMAGES_DIR / filename
                    im.save(out_path, format="PNG", optimize=True)
                    rel_path = f"data/images/{filename}"
                    q_img_map[(m, current_q)] = rel_path
                    saved_count += 1
                    current_q = None
    print(f"Extracted {saved_count} images successfully!")
    return q_img_map

def clean_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def generate_distractors(correct_ans: str, question_text: str, all_answers: list) -> list:
    norm_ans = correct_ans.strip().rstrip('.')
    low_ans = norm_ans.lower()
    
    # 1. True / False
    if low_ans in ["ha", "ha, to'g'ri", "to'g'ri", "ha."]:
        return ["Yo'q (Noto'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
    if low_ans in ["yo'q", "yo'q.", "noto'g'ri"]:
        return ["Ha (To'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
    
    # 2. Matching pairs e.g. A-2, B-1, C-3
    if re.search(r'[A-Z]-\d', norm_ans):
        distractors = [
            "A-1, B-2, C-3",
            "A-3, B-1, C-2",
            "A-2, B-3, C-1",
            "A-3, B-2, C-1"
        ]
        return [d for d in distractors if d.lower() != low_ans][:3]
    
    # 3. Number sequences e.g. 1, 2, 3, 4
    if re.match(r'^\d+(\s*,\s*\d+)+$', norm_ans):
        parts = [p.strip() for p in norm_ans.split(',')]
        if len(parts) == 4:
            return ["2, 1, 4, 3", "1, 3, 2, 4", "4, 2, 1, 3"]
        elif len(parts) == 3:
            return ["2, 4, 6", "1, 2, 4", "3, 5, 6"]
        elif len(parts) == 2:
            return ["2, 4", "1, 2", "3, 4"]
        elif len(parts) == 1:
            n = parts[0]
            return [str(int(n)+1), str(max(1, int(n)-1)), str(int(n)+2)]

    # 4. Dimension / measurement
    if "mkm" in low_ans:
        return ["0,5 mkm", "1,0 mkm", "0,1 mkm"]
    if "tomchi" in low_ans:
        return ["5 tomchi", "2 tomchi", "15 tomchi"]
    if "daqiqa" in low_ans:
        return ["3-5 daqiqa", "10 daqiqa", "30 soniya"]
    if "soniya" in low_ans:
        return ["10-15 soniya", "1-2 daqiqa", "60 soniya"]
    if re.match(r'^\d+\s*ta\.?$', low_ans):
        n = int(re.findall(r'\d+', low_ans)[0])
        return [f"{n+2} ta", f"{max(1, n-1)} ta", f"{n+1} ta"]
    if low_ans.isdigit():
        n = int(low_ans)
        return [str(n + 10), str(max(10, n - 20)), str(n + 30)]

    # 5. Domain pool matches
    for pool_name, pool in DOMAIN_POOLS.items():
        # Check if correct answer matches any item in pool
        match_idx = None
        for idx, item in enumerate(pool):
            if item.lower() == low_ans or (len(item) > 4 and item.lower() in low_ans):
                match_idx = idx
                break
        if match_idx is not None:
            # Pick from this pool
            candidates = [p for p in pool if p.lower() != low_ans and p.lower() not in low_ans]
            random.shuffle(candidates)
            if len(candidates) >= 3:
                return candidates[:3]

    # 6. Fallback from all topic answers with similar length
    target_len = len(norm_ans)
    same_answers = [
        a.strip().rstrip('.') for a in all_answers 
        if a.strip().rstrip('.').lower() != low_ans 
        and a.strip().rstrip('.').lower() not in ["ha", "yo'q", "to'g'ri", "noto'g'ri"]
        and len(a.strip()) <= 90
    ]
    # Sort by length proximity
    same_answers.sort(key=lambda x: abs(len(x) - target_len))
    selected = []
    seen = set()
    for cand in same_answers:
        cand_low = cand.lower()
        if cand_low not in seen and cand_low != low_ans:
            seen.add(cand_low)
            selected.append(cand)
            if len(selected) == 3:
                break
    
    # If still not enough, add safe defaults
    defaults = ["Mikroskopik tahlil", "Bakterial kultura", "Serologik usul", "Biologik sinov"]
    for d in defaults:
        if len(selected) >= 3:
            break
        if d.lower() != low_ans and d.lower() not in seen:
            selected.append(d)
            seen.add(d.lower())
            
    return selected[:3]

def build_quizzes():
    q_img_map = extract_images()
    
    for m in range(1, 5):
        raw_file = f"scratch_m{m}_raw.json"
        with open(raw_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        all_answers = [x["answer"] for x in raw_data]
        rows = []
        
        for item in raw_data:
            q_num = item["num"]
            raw_q = clean_text(item["question"])
            raw_a = clean_text(item["answer"])
            
            # Format True/False clean representation
            if raw_a.lower() in ["ha", "ha.", "to'g'ri", "ha, to'g'ri"]:
                correct_text = "Ha (To'g'ri)"
                distractors = ["Yo'q (Noto'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
            elif raw_a.lower() in ["yo'q", "yo'q.", "noto'g'ri"]:
                correct_text = "Yo'q (Noto'g'ri)"
                distractors = ["Ha (To'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
            else:
                correct_text = raw_a.rstrip('.')
                distractors = generate_distractors(correct_text, raw_q, all_answers)
            
            # Cap options to 95 chars max
            correct_text = correct_text[:95]
            distractors = [d[:95] for d in distractors[:3]]
            
            # Ensure 4 unique options
            options = [correct_text] + distractors
            # De-duplicate while preserving correct_text
            seen = {correct_text.lower()}
            final_distractors = []
            for d in distractors:
                if d.lower() not in seen:
                    seen.add(d.lower())
                    final_distractors.append(d)
            while len(final_distractors) < 3:
                filler = f"Variant {chr(66 + len(final_distractors))}"
                final_distractors.append(filler)
                
            all_opts = [correct_text] + final_distractors
            random.shuffle(all_opts)
            
            correct_letter = chr(65 + all_opts.index(correct_text))
            
            # Cap question length for Telegram (max 295 chars)
            if len(raw_q) > 295:
                q_text = raw_q[:292] + "..."
            else:
                q_text = raw_q
                
            img_path = q_img_map.get((m, q_num), "")
            explanation = f"To'g'ri javob: {correct_text}"
            
            rows.append({
                "question": q_text,
                "option_a": all_opts[0],
                "option_b": all_opts[1],
                "option_c": all_opts[2],
                "option_d": all_opts[3],
                "correct_answer": correct_letter,
                "explanation": explanation[:200],
                "topic": f"Mikrobiologiya: {m}-mavzu",
                "difficulty": "Medium",
                "timer": 25,
                "image": img_path
            })
            
        csv_filename = f"mikrobiologiya_mavzu_{m:02d}.csv"
        csv_path = COLLECTIONS_DIR / csv_filename
        with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "question", "option_a", "option_b", "option_c", "option_d",
                "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
            ])
            writer.writeheader()
            writer.writerows(rows)
            
        print(f"Created {csv_filename} with {len(rows)} questions ({sum(1 for r in rows if r['image'])} with images)")

if __name__ == "__main__":
    build_quizzes()
