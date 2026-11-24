import os
import re
import csv
import random
from pathlib import Path
from distractor_dicts import DOMAIN_DISTRACTORS, SHORTEN_ANSWERS

TOPICS = [
    (1, "fiziologiya_mavzu_01", "Normal fiziologiya: 1-mavzu", "Fiziologiya faniga kirish"),
    (2, "fiziologiya_mavzu_02", "Normal fiziologiya: 2-mavzu", "Membrana potensiali va qo'zg'aluvchan to'qimalar"),
    (3, "fiziologiya_mavzu_03", "Normal fiziologiya: 3-mavzu", "Muskul fiziologiyasi"),
    (4, "fiziologiya_mavzu_04", "Normal fiziologiya: 4-mavzu", "Nerv tolalari va sinapslar"),
    (5, "fiziologiya_mavzu_05", "Normal fiziologiya: 5-mavzu", "Qon plazmasi va eritrotsitlar"),
    (6, "fiziologiya_mavzu_06", "Normal fiziologiya: 6-mavzu", "Leykotsitlar va qon guruhlari"),
    (7, "fiziologiya_mavzu_07", "Normal fiziologiya: 7-mavzu", "Gemostaz va trombotsitlar"),
    (8, "fiziologiya_mavzu_08", "Normal fiziologiya: 8-mavzu", "Yurak mushaklari"),
    (9, "fiziologiya_mavzu_09", "Normal fiziologiya: 9-mavzu", "Yurak boshqarilishi"),
    (10, "fiziologiya_mavzu_10", "Normal fiziologiya: 10-mavzu", "Mikrosirkulyatsiya"),
    (11, "fiziologiya_mavzu_11", "Normal fiziologiya: 11-mavzu", "Nafas fiziologiyasi"),
    (12, "fiziologiya_mavzu_12", "Normal fiziologiya: 12-mavzu", "Nafas boshqarilishi")
]

def normalize_text(t):
    return re.sub(r"\s+", " ", t).strip()

def clean_ans(a):
    a = normalize_text(a)
    return a.rstrip(".")

def parse_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
        
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    qa_pairs = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("Fiziologiya fanidan") or line.startswith("Savol va faqat") or line.startswith("Ha / Yo") or line.startswith("1–60.") or line.startswith("61–90.") or line.startswith("91–100.") or line in ["Gemostaz", "Yurak mushaklari", "Yurak boshqarilishi", "Mikrosirkulyatsiya", "Nafas fiziologiyasi", "Nafas boshqarilishi"]:
            i += 1
            continue
            
        q_match = re.match(r"^(\d+)(?:-test)?\.\s*(.*)", line)
        if q_match:
            q_num = int(q_match.group(1))
            q_text = q_match.group(2).strip()
            i += 1
            while i < len(lines):
                next_line = lines[i]
                ans_match = re.match(r"^(?:To[‘'`]g[‘'`]ri javob:|Javob:|\+)\s*(.*)", next_line, re.IGNORECASE)
                if ans_match:
                    qa_pairs.append((q_num, normalize_text(q_text), clean_ans(ans_match.group(1))))
                    i += 1
                    break
                elif re.match(r"^(\d+)(?:-test)?\.\s*", next_line):
                    break
                else:
                    q_text += " " + next_line
                    i += 1
            continue
        i += 1
    return qa_pairs

def get_normalized_answer(a):
    a_lower = a.lower().rstrip(".")
    if a_lower in SHORTEN_ANSWERS:
        return SHORTEN_ANSWERS[a_lower]
    # Check if any key is a substring or close match
    for k, v in SHORTEN_ANSWERS.items():
        if k in a_lower or a_lower in k:
            return v
    if len(a) > 88:
        # shorten at last space before 85
        cut = a[:85]
        last_space = cut.rfind(" ")
        if last_space > 50:
            return cut[:last_space]
        return cut
    return a

def select_distractors(q_num, q, correct, open_answers, topic_num):
    c_lower = correct.lower()
    
    # 1. Check DOMAIN_DISTRACTORS
    if c_lower in DOMAIN_DISTRACTORS:
        return list(DOMAIN_DISTRACTORS[c_lower])
        
    for k, v in DOMAIN_DISTRACTORS.items():
        if k == c_lower or k in c_lower or c_lower in k:
            # check if distractors don't conflict with correct
            d_list = [d for d in v if d.lower() != c_lower]
            if len(d_list) >= 3:
                return d_list[:3]
                
    # 2. Pick from open_answers
    rng = random.Random(topic_num * 1000 + q_num * 17)
    candidates = []
    
    for ans in open_answers:
        ans_norm = get_normalized_answer(ans)
        ans_lower = ans_norm.lower()
        if ans_lower == c_lower:
            continue
        if ans_lower in c_lower or c_lower in ans_lower:
            continue
        if len(ans_norm) > 90:
            continue
            
        len_diff = abs(len(ans_norm) - len(correct))
        candidates.append((len_diff, ans_norm))
        
    candidates.sort(key=lambda x: x[0])
    
    # Select from top 20 candidates
    pool = [c for diff, c in candidates[:20]]
    rng.shuffle(pool)
    
    selected = []
    for c in pool:
        if c not in selected and c.lower() != c_lower:
            selected.append(c)
        if len(selected) == 3:
            break
            
    # Fallback if pool was small
    fallback_pool = [
        "Metabolik faollikning susayishi",
        "Regulyator mexanizmlar nomutanosibligi",
        "Kompleks fiziologik moslashuv buzilishi",
        "Nerv va gumoral boshqaruv yetishmovchiligi"
    ]
    fb_idx = 0
    while len(selected) < 3:
        cand = fallback_pool[fb_idx % len(fallback_pool)]
        if cand not in selected and cand.lower() != c_lower:
            selected.append(cand)
        fb_idx += 1
        
    return selected

def build_topic_csv(col_num, slug, clean_title, subtitle):
    raw_path = f"scripts/raw_txt/{slug}.txt"
    qa_pairs = parse_file(raw_path)
    print(f"[{col_num}] {slug}: {len(qa_pairs)} questions parsed")
    
    # Collect open answers for distractor pool
    open_answers = [a for num, q, a in qa_pairs if a.lower().rstrip(".") not in ["ha", "yo'q", "yo‘q", "yo`q", "yoq"]]
    
    rows = []
    for num, q, a in qa_pairs:
        a_clean = a.lower().rstrip(".").strip()
        is_yes = a_clean in ["ha"]
        is_no = a_clean in ["yo'q", "yo‘q", "yo`q", "yoq"]
        
        orig_answer_for_expl = a
        
        if is_yes:
            correct_opt = "Ha (To'g'ri)"
            distractors = ["Yo'q (Noto'g'ri)", "Qisman to'g'ri", "Bunday bog'liqlik yo'q"]
            explanation = f"To'g'ri javob: Ha (To'g'ri)."
        elif is_no:
            correct_opt = "Yo'q (Noto'g'ri)"
            distractors = ["Ha (To'g'ri)", "Qisman to'g'ri", "Har doim to'g'ri"]
            explanation = f"To'g'ri javob: Yo'q (Noto'g'ri)."
        else:
            correct_opt = get_normalized_answer(a)
            distractors = select_distractors(num, q, correct_opt, open_answers, col_num)
            explanation = f"To'g'ri javob: {correct_opt}."
            
        # Capitalize first letter of correct_opt if needed
        if correct_opt and correct_opt[0].islower():
            correct_opt = correct_opt[0].upper() + correct_opt[1:]
        distractors = [d[0].upper() + d[1:] if d and d[0].islower() else d for d in distractors]
        
        # Verify length
        assert len(correct_opt) <= 95, f"Option too long in {slug} #{num}: '{correct_opt}' ({len(correct_opt)})"
        for d in distractors:
            assert len(d) <= 95, f"Distractor too long in {slug} #{num}: '{d}' ({len(d)})"
            
        # Shuffle options
        options = [correct_opt] + distractors
        # Ensure 4 unique options
        unique_opts = []
        for o in options:
            if o not in unique_opts:
                unique_opts.append(o)
        while len(unique_opts) < 4:
            unique_opts.append(f"Qo'shimcha variant {len(unique_opts)+1}")
            
        rng = random.Random(col_num * 5000 + num * 31)
        rng.shuffle(unique_opts)
        
        letters = ["A", "B", "C", "D"]
        correct_idx = unique_opts.index(correct_opt)
        correct_letter = letters[correct_idx]
        
        if len(explanation) > 195:
            explanation = explanation[:192] + "..."
            
        row = {
            "question": q,
            "option_a": unique_opts[0],
            "option_b": unique_opts[1],
            "option_c": unique_opts[2],
            "option_d": unique_opts[3],
            "correct_answer": correct_letter,
            "explanation": explanation,
            "topic": clean_title,
            "difficulty": "Medium",
            "timer": 25,
            "image": ""
        }
        rows.append(row)
        
    out_dir = Path("data/fiziologiya_collections")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.csv"
    
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "question", "option_a", "option_b", "option_c", "option_d",
            "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Generated {out_path} with {len(rows)} questions.")
    return len(rows)

def main():
    total_q = 0
    for col_num, slug, title, subtitle in TOPICS:
        count = build_topic_csv(col_num, slug, title, subtitle)
        total_q += count
    print(f"\nALL 12 COLLECTIONS SUCCESSFULLY BUILT! Total questions: {total_q}")

if __name__ == "__main__":
    main()
