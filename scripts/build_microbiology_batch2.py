import os
import re
import csv
import json
import random
from pathlib import Path
import pymupdf as fitz
from PIL import Image, ImageChops

# Set seed for reproducibility
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
COLLECTIONS_DIR = DATA_DIR / "mikrobiologiya_collections"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)

PDF_FILES = {
    5: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795204941833_a4f64d09.pdf",
    6: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795204941827_f2539e7e.pdf",
    7: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795204941831_b8ee4a02.pdf",
    8: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795204941830_ce70709a.pdf",
    9: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795204941830_377da57f.pdf",
    10: r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795204941831_1910a799.pdf",
}

# Domain pools for realistic medical microbiology distractors
DOMAIN_POOLS = {
    "culture_media": [
        "Endo muhiti", "Ploskirev muhiti", "Vismut-sulfit agar", "Saburo muhiti",
        "Kitta-Tarottsi muhiti", "Uilson-Bler muhiti", "Qonli agar", "Zardobli agar",
        "Levenshteyn-Yensen muhiti", "Kligler muhiti", "Go'sht-peptonli agar (GPA)",
        "Go'sht-peptonli bulyon (GPB)", "Rassel muhiti", "Tyuxi muhiti", "TSTA agari"
    ],
    "microorganisms": [
        "Escherichia coli", "Salmonella typhi", "Shigella dysenteriae",
        "Staphylococcus aureus", "Streptococcus pneumoniae", "Clostridium tetani",
        "Clostridium perfringens", "Pseudomonas aeruginosa", "Vibrio cholerae",
        "Mycobacterium tuberculosis", "Corynebacterium diphtheriae", "Lactobacillus",
        "Bifidobacterium", "Bordetella pertussis", "Proteus vulgaris"
    ],
    "viruses": [
        "Gripp virusi", "Adenovirus", "Gerpes virusi", "Marburg virusi",
        "Ebola virusi", "Quturish virusi (Rabies)", "Bakteriofag",
        "Tamaki mozaikasi virusi", "OIV (OITS virusi)", "Gepatit B virusi",
        "Koronavirus", "Qizamiq virusi", "Poliomiyelit virusi", "Rotavirus"
    ],
    "serology_tests": [
        "IFA (immunoferment tahlili)", "KBR (komplementni bog'lash reaksiyasi)",
        "Agglyutinatsiya reaksiyasi", "Pretsipitatsiya reaksiyasi",
        "Bilvosita gemagglyutinatsiya (RNGA)", "Kumbs reaksiyasi",
        "PZR (polimeraza zanjir reaksiyasi)", "Immunobloting (Western blot)"
    ],
    "sterilization_methods": [
        "Avtoklavlash (bosimli bug' bilan)", "Quruq issiq havo (Paster pechi)",
        "Tindalizatsiya usuli", "Pasterizatsiya usuli",
        "Ultrabinafsha (UB) nurlantirish", "Filtrlash (membrana orqali)",
        "Kimyoviy dezinfeksiya", "Gamma-nurlanish bilan sterilizatsiya"
    ],
    "immunoglobulins": [
        "IgG", "IgM", "IgA", "IgE", "IgD", "Sekretor IgA"
    ],
    "symmetry_types": [
        "Spiralsimon simmetriya", "Kubsimon (ikosaedrik) simmetriya",
        "Murakkab (kombinatsiyalashgan) simmetriya", "Asimmetrik tuzilish"
    ],
    "viral_structures": [
        "Kapsid", "Superkapsid (peplos)", "Nukleokapsid", "Kapsomerlar",
        "Genom (DNK yoki RNK)", "Teskari transkriptaza", "Glikoprotein spayklar"
    ],
    "colony_types": [
        "S-koloniyalar (smooth - silliq)", "R-koloniyalar (rough - g'adir-budur)",
        "M-koloniyalar (shilliq)", "D-koloniyalar (mitti)"
    ],
    "respiration_types": [
        "Obligat aeroblar", "Obligat anaeroblar", "Fakultativ anaeroblar",
        "Mikroaerofillar", "Aerotolerant bakteriyalar"
    ]
}

def trim_image(im: Image.Image) -> Image.Image:
    """Trim uniform white or near-white background from image."""
    bg = Image.new(im.mode, im.size, (255, 255, 255) if im.mode == 'RGB' else (255, 255, 255, 255))
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        # Add 3px padding
        w, h = im.size
        pad_bbox = (
            max(0, bbox[0] - 3),
            max(0, bbox[1] - 3),
            min(w, bbox[2] + 3),
            min(h, bbox[3] + 3)
        )
        return im.crop(pad_bbox)
    return im

def clean_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def clean_answer_text(ans: str) -> str:
    ans = ans.strip().rstrip('.')
    ans = re.sub(r'\s*\(\s*✓\s*\)', '', ans)
    ans = re.sub(r'\(qizil ruchkada[^\)]*\)', '', ans, flags=re.IGNORECASE)
    ans = re.sub(r'\(qo[‘\'`\"]lda[^\)]*\)', '', ans, flags=re.IGNORECASE)
    ans = re.sub(r'\(rasmda chizilgan javob[^\)]*\)', '', ans, flags=re.IGNORECASE)
    ans = re.sub(r'\(rasmda bosma javob[^\)]*\)', '', ans, flags=re.IGNORECASE)
    ans = ans.strip().rstrip('.')
    return ans

def generate_distractors(correct_ans: str, question_text: str, all_answers: list) -> list:
    norm_ans = clean_answer_text(correct_ans)
    low_ans = norm_ans.lower()

    # 1. True / False
    if low_ans in ["ha", "to'g'ri", "to‘g‘ri", "ha, to'g'ri", "ha (to'g'ri)"] or low_ans.startswith("ha ("):
        return ["Yo'q (Noto'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
    if low_ans in ["yo'q", "yo‘q", "noto'g'ri", "noto‘g‘ri", "yo'q (noto'g'ri)"] or low_ans.startswith("yo'q ("):
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

    # 3. Number sequences e.g. 1, 2, 3 or 1, 3, 5
    if re.match(r'^\d+(\s*,\s*\d+)+$', norm_ans):
        parts = [p.strip() for p in norm_ans.split(',')]
        if len(parts) == 4:
            cands = ["2, 3, 4, 6", "1, 2, 4, 5", "1, 3, 4, 7", "2, 4, 5, 6"]
        elif len(parts) == 3:
            cands = ["2, 4, 6", "1, 2, 4", "3, 4, 5", "1, 3, 5", "2, 3, 5"]
        elif len(parts) == 2:
            cands = ["2, 4", "1, 3", "1, 2", "3, 4", "2, 5"]
        else:
            cands = ["1, 2", "2, 3", "3, 4"]
        return [c for c in cands if c != norm_ans][:3]

    # 4. Temperature ranges e.g. 65-70°C, 37°C
    if "°c" in low_ans or "gradus" in low_ans or "c da" in low_ans:
        cands = ["37°C da", "56–60°C da", "100°C da", "20–25°C da", "120°C da"]
        return [c for c in cands if c.lower() != low_ans][:3]

    # 5. Domain pool matches
    for pool_name, pool in DOMAIN_POOLS.items():
        match_found = False
        for item in pool:
            if item.lower() == low_ans or (len(item) > 4 and item.lower() in low_ans):
                match_found = True
                break
        if match_found:
            candidates = [p for p in pool if p.lower() != low_ans and p.lower() not in low_ans]
            random.shuffle(candidates)
            if len(candidates) >= 3:
                return candidates[:3]

    # 6. Fallback: similar length answers from current topic
    target_len = len(norm_ans)
    clean_all = []
    seen = set()
    for a in all_answers:
        ca = clean_answer_text(a)
        ca_low = ca.lower()
        if (ca_low != low_ans and ca_low not in seen
            and not ca_low.startswith("ha") and not ca_low.startswith("yo'q")
            and not ca_low.startswith("to'g'ri") and not ca_low.startswith("noto'g'ri")
            and len(ca) <= 90 and len(ca) >= 3):
            seen.add(ca_low)
            clean_all.append(ca)

    clean_all.sort(key=lambda x: abs(len(x) - target_len))
    selected = clean_all[:3]

    # If still not enough, add medical microbiology fallbacks
    defaults = [
        "Gram usulida bo'yash",
        "Petri kosachasida o'stirish",
        "Serologik tahlil o'tkazish",
        "Biologik proba qo'yish"
    ]
    for d in defaults:
        if len(selected) >= 3:
            break
        if d.lower() != low_ans and d.lower() not in [s.lower() for s in selected]:
            selected.append(d)

    return selected[:3]

def parse_pdf(pdf_path: str):
    """Parse all Q and A pairs from PDF and identify image regions."""
    doc = fitz.open(pdf_path)
    pairs = []
    current_q = None

    for p_idx, page in enumerate(doc):
        blocks = page.get_text('blocks')
        for b in blocks:
            text = b[4].strip()
            if not text:
                continue
            m_q = re.match(r'^(\d+)[\.\s\b](.*)', text, re.DOTALL)
            if not m_q:
                m_q = re.match(r'^(\d+)([A-Z\u0400-\u04FF\u0100-\u017F\u02BB\u02BC\'\"“‘].*)', text, re.DOTALL)
            if m_q and not text.startswith('Javob:'):
                current_q = {
                    'num': int(m_q.group(1)),
                    'text': clean_text(m_q.group(2) if len(m_q.groups()) > 1 else text),
                    'page': p_idx,
                    'y0': b[1],
                    'y1': b[3]
                }
            elif text.startswith('Javob:'):
                if current_q:
                    raw_ans = text[len('Javob:'):].strip()
                    pairs.append({
                        'num': current_q['num'],
                        'question': current_q['text'],
                        'answer': raw_ans,
                        'q_page': current_q['page'],
                        'q_y0': current_q['y0'],
                        'q_y1': current_q['y1'],
                        'a_page': p_idx,
                        'a_y0': b[1],
                        'a_y1': b[3]
                    })
                    current_q = None

    return doc, pairs

def extract_and_build():
    print("=== Starting Microbiology Batch 2 (Topics 5 to 10) ===")
    total_questions = 0
    total_images = 0

    for m in range(5, 11):
        pdf_path = PDF_FILES[m]
        doc, pairs = parse_pdf(pdf_path)
        print(f"\nProcessing Topic {m}: {len(pairs)} questions found.")

        all_answers = [p['answer'] for p in pairs]
        rows = []
        topic_images = 0

        for item in pairs:
            q_num = item['num']
            raw_q = clean_text(item['question'])
            raw_a = clean_text(item['answer'])

            # Special case for Q104 and Q105 in Mavzu 8 where original PDF lacked answer
            if m == 8 and q_num == 104 and "mavjud emas" in raw_a.lower():
                raw_a = "Avtoklav (bosim ostida to'yingan bug' bilan sterillash apparati)"
            elif m == 8 and q_num == 105 and "mavjud emas" in raw_a.lower():
                raw_a = "Ultrabinafsha (UB) nurlantirish (bakteritsid kvars chirog'i)"

            # Image extraction logic
            img_rel_path = ""
            # Check if there is an image between Q and A
            has_image = False
            if item['q_page'] == item['a_page']:
                gap = item['a_y0'] - item['q_y1']
                if gap >= 35:
                    has_image = True
            
            if has_image:
                page = doc[item['q_page']]
                clip = fitz.Rect(60, item['q_y1'] + 1, page.rect.width - 60, item['a_y0'] - 1)
                pix = page.get_pixmap(clip=clip, dpi=180)
                im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                trimmed = trim_image(im)
                if trimmed.size[0] > 30 and trimmed.size[1] > 20:
                    filename = f"mikro_m{m}_q{q_num:03d}.png"
                    out_path = IMAGES_DIR / filename
                    trimmed.save(out_path, format="PNG", optimize=True)
                    img_rel_path = f"data/images/{filename}"
                    topic_images += 1
                    total_images += 1

            # Format correct answer and distractors
            clean_ans = clean_answer_text(raw_a)
            low_ans = clean_ans.lower()

            if low_ans in ["ha", "to'g'ri", "to‘g‘ri", "ha, to'g'ri", "ha (to'g'ri)"] or low_ans.startswith("ha ("):
                correct_text = "Ha (To'g'ri)"
                distractors = ["Yo'q (Noto'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
            elif low_ans in ["yo'q", "yo‘q", "noto'g'ri", "noto‘g‘ri", "yo'q (noto'g'ri)"] or low_ans.startswith("yo'q ("):
                correct_text = "Yo'q (Noto'g'ri)"
                distractors = ["Ha (To'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
            else:
                correct_text = clean_ans
                distractors = generate_distractors(correct_text, raw_q, all_answers)

            # Cap options to 95 chars max
            correct_text = correct_text[:95]
            distractors = [d[:95] for d in distractors[:3]]

            # Ensure 4 unique options
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

            # Telegram max question length: 295
            if len(raw_q) > 295:
                q_text = raw_q[:292] + "..."
            else:
                q_text = raw_q

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
                "image": img_rel_path
            })

        # Save to CSV
        csv_filename = f"mikrobiologiya_mavzu_{m:02d}.csv"
        csv_path = COLLECTIONS_DIR / csv_filename
        with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "question", "option_a", "option_b", "option_c", "option_d",
                "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
            ])
            writer.writeheader()
            writer.writerows(rows)

        total_questions += len(rows)
        print(f"Created {csv_filename}: {len(rows)} questions, {topic_images} images saved.")

    print(f"\n=== FINISHED! Total questions: {total_questions}, Total images: {total_images} ===")

if __name__ == "__main__":
    extract_and_build()
