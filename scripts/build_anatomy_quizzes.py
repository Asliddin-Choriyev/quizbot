import os
import csv
import random
from pathlib import Path

# Seed random so results are consistent and reproducible
random.seed(42)

DIAGRAMS = [
    {
        "id": 1,
        "topic": "Umurtqa suyagi",
        "image": "data/images/anatomiya_img_01.png",
        "items": [
            (1, "Processus spinosus"),
            (2, "Foramen vertebrale"),
            (3, "Processus articularis inferior"),
            (4, "Processus articularis superior"),
            (5, "Corpus vertebrae"),
            (6, "Processus transversus"),
            (7, "Foramen transversarium"),
            (8, "Processus costarius"),
        ]
    },
    {
        "id": 2,
        "topic": "Dumg'aza suyagi",
        "image": "data/images/anatomiya_img_02.png",
        "items": [
            (1, "Basis ossis sacri"),
            (2, "Processus articularis superior"),
            (3, "Foramina sacralia pelvina"),
            (4, "Linea transversae"),
            (5, "Apex ossis sacri"),
        ]
    },
    {
        "id": 3,
        "topic": "Umurtqa pog'onasi",
        "image": "data/images/anatomiya_img_03.png",
        "items": [
            (1, "Vertebra cervicalis"),
            (2, "Vertebra thoracica"),
            (3, "Vertebra lumbalis"),
            (4, "Vertebra sacralia"),
            (5, "Vertebra coccygea"),
            (6, "Atlas"),
            (7, "Processus transversus"),
        ]
    },
    {
        "id": 4,
        "topic": "Qo'l suyaklari",
        "image": "data/images/anatomiya_img_04.png",
        "items": [
            (1, "Clavicula"),
            (2, "Scapula"),
            (3, "Humerus"),
            (4, "Radius"),
            (5, "Ulna"),
            (6, "Ossa carpi"),
            (7, "Ossa metacarpi"),
            (8, "Ossa digitorum manus"),
        ]
    },
    {
        "id": 5,
        "topic": "Oyoq suyaklari",
        "image": "data/images/anatomiya_img_05.png",
        "items": [
            (1, "Os sacrum"),
            (2, "Os coxae"),
            (3, "Femur"),
            (4, "Patella"),
            (5, "Fibula"),
            (6, "Tibia"),
            (7, "Ossa pedis"),
        ]
    },
    {
        "id": 6,
        "topic": "Yelka suyagi (Humerus)",
        "image": "data/images/anatomiya_img_06.png",
        "items": [
            (1, "Tuberculum majus"),
            (2, "Sulcus intertubercularis"),
            (3, "Tuberositas deltoidea"),
            (4, "Fossa radialis"),
            (5, "Capitulum humeri"),
            (6, "Trochlea humeri"),
            (7, "Fossa coronoidea"),
            (8, "Tuberculum minus"),
            (9, "Caput humeri"),
        ]
    },
    {
        "id": 7,
        "topic": "Son suyagi (Femur)",
        "image": "data/images/anatomiya_img_07.png",
        "items": [
            (1, "Fovea capitis"),
            (2, "Caput femoris"),
            (3, "Trochanter major"),
            (4, "Collum femoris"),
            (5, "Linea intertrochanterica"),
            (6, "Trochanter minor"),
            (7, "Corpus femoris"),
            (8, "Epicondylus lateralis"),
            (9, "Epicondylus medialis"),
        ]
    },
    {
        "id": 8,
        "topic": "Boldir suyaklari (Tibia et fibula)",
        "image": "data/images/anatomiya_img_08.png",
        "items": [
            (1, "Condylus lateralis"),
            (2, "Caput fibulae"),
            (3, "Margo interosseus fibulae"),
            (4, "Malleolus lateralis"),
            (5, "Malleolus medialis"),
            (6, "Corpus tibiae"),
            (7, "Tuberositas tibiae"),
            (8, "Condylus medialis"),
        ]
    },
    {
        "id": 9,
        "topic": "Chanoq suyagi (Os coxae)",
        "image": "data/images/anatomiya_img_09.png",
        "items": [
            (1, "Crista iliaca"),
            (2, "Spina iliaca posterior inferior"),
            (3, "Incisura ischiadica major"),
            (4, "Spina ischiadica"),
            (5, "Tuber ischiadicum"),
            (6, "Spina iliaca anterior superior"),
            (7, "Fossa acetabuli"),
            (8, "Foramen obturatum"),
        ]
    },
    {
        "id": 10,
        "topic": "To'sh-o'mrov bo'g'imi",
        "image": "data/images/anatomiya_img_10.png",
        "items": [
            (1, "Lig. interclaviculare"),
            (2, "Discus articularis"),
            (3, "Os claviculare"),
            (4, "Lig. costoclaviculare"),
            (5, "Costa"),
            (6, "Lig. sternoclaviculare anterius"),
            (7, "Sternum"),
        ]
    },
    {
        "id": 11,
        "topic": "Umurtqalararo boylamlar",
        "image": "data/images/anatomiya_img_11.png",
        "items": [
            (1, "Corpus vertebrae"),
            (2, "Discus intervertebralis"),
            (3, "Lig. longitudinale posterius"),
            (4, "Lig. longitudinale anterius"),
            (5, "Art. zygapophysialis"),
            (6, "Lig. interspinale"),
            (7, "Lig. flavum"),
            (8, "Lig. supraspinale"),
            (9, "Foramen intervertebrale"),
        ]
    },
    {
        "id": 12,
        "topic": "Yelka bo'g'imi (Art. humeri)",
        "image": "data/images/anatomiya_img_12.png",
        "items": [
            (1, "Lig. coracohumerale"),
            (2, "Lig. coracoacromiale"),
            (3, "Processus coracoideus"),
            (4, "Scapula"),
            (5, "Capsula articularis"),
            (6, "Humerus"),
            (7, "Caput longum m. bicipitis brachii"),
            (8, "M. subscapularis"),
            (9, "Acromion"),
        ]
    },
    {
        "id": 13,
        "topic": "Chanoq-son bo'g'imi (Art. coxae)",
        "image": "data/images/anatomiya_img_13.png",
        "items": [
            (1, "Spina iliaca anterior inferior"),
            (2, "Lig. iliofemorale"),
            (3, "Capsula articularis"),
            (4, "Lig. pubofemorale"),
            (5, "Canalis obturatorius"),
            (6, "Membrana obturatoria"),
            (7, "Trochanter minor"),
            (8, "Femur"),
            (9, "Trochanter major"),
        ]
    },
    {
        "id": 14,
        "topic": "Tizza bo'g'imi (Art. genus)",
        "image": "data/images/anatomiya_img_14.png",
        "items": [
            (1, "Femur"),
            (2, "Lig. cruciatum posterius"),
            (3, "Lig. cruciatum anterius"),
            (4, "Meniscus medialis"),
            (5, "Meniscus lateralis"),
            (6, "Lig. collaterale tibiale"),
            (7, "Lig. patellae (suprapatellare)"),
            (8, "Patella"),
            (9, "Caput fibulae"),
            (10, "Membrana interossea"),
        ]
    },
    {
        "id": 15,
        "topic": "Ko'krak va qorin mushaklari",
        "image": "data/images/anatomiya_img_15.png",
        "items": [
            (1, "M. pectoralis major"),
            (2, "M. pectoralis minor"),
            (3, "M. trapezius"),
            (4, "M. sternocleidomastoideus"),
            (5, "Fascia thoracica"),
            (7, "M. deltoideus"),
            (8, "M. obliquus internus abdominis"),
            (9, "M. serratus anterior"),
            (10, "M. rectus abdominis"),
            (11, "M. transversus abdominis"),
        ]
    },
    {
        "id": 16,
        "topic": "Orqa mushaklari",
        "image": "data/images/anatomiya_img_16.png",
        "items": [
            (1, "M. trapezius"),
            (2, "Spina scapulae"),
            (3, "M. deltoideus"),
            (4, "M. infraspinatus"),
            (5, "M. teres minor"),
            (6, "M. teres major"),
            (7, "M. rhomboideus major"),
            (8, "M. latissimus dorsi"),
            (9, "Trigonum lumbale"),
        ]
    },
    {
        "id": 17,
        "topic": "Sonning orqa mushaklari",
        "image": "data/images/anatomiya_img_17.png",
        "items": [
            (1, "M. gluteus maximus"),
            (2, "M. adductor magnus"),
            (3, "Tractus iliotibialis"),
            (4, "Tendo m. semitendinosi"),
            (5, "M. semitendinosus"),
            (6, "M. biceps femoris"),
            (7, "M. gracilis"),
            (8, "M. semimembranosus"),
            (9, "M. sartorius"),
            (10, "M. popliteus"),
        ]
    },
    {
        "id": 18,
        "topic": "Boldirning old mushaklari",
        "image": "data/images/anatomiya_img_18.png",
        "items": [
            (1, "M. sartorius"),
            (2, "M. iliopsoas"),
            (3, "M. pectineus"),
            (4, "M. adductor longus"),
            (5, "M. gracilis"),
            (6, "M. gastrocnemius"),
            (7, "M. soleus"),
            (8, "M. extensor hallucis longus"),
        ]
    },
    {
        "id": 19,
        "topic": "Qorin a'zolari va qorin pardasi",
        "image": "data/images/anatomiya_img_19.png",
        "items": [
            (1, "Hepar"),
            (2, "Oesophagus"),
            (3, "Vesica fellea"),
            (4, "Lien (Splen)"),
            (5, "Peritoneum"),
            (6, "Flexura coli sinistra (lienalis)"),
            (7, "Flexura coli dextra (hepatica)"),
            (8, "Intestinum jejunum"),
            (9, "Duodenum"),
        ]
    },
    {
        "id": 20,
        "topic": "Qo'l mushaklari",
        "image": "data/images/anatomiya_img_20.png",
        "items": [
            (1, "M. levator scapulae"),
            (2, "M. deltoideus"),
            (3, "M. biceps brachii"),
            (4, "M. coracobrachialis"),
            (5, "M. subscapularis"),
            (6, "M. rhomboideus major"),
            (7, "M. brachioradialis"),
            (8, "M. triceps brachii"),
        ]
    },
    {
        "id": 21,
        "topic": "Hazm qilish tizimi",
        "image": "data/images/anatomiya_img_21.png",
        "items": [
            (1, "Cavum oris"),
            (2, "Pharynx"),
            (3, "Oesophagus"),
            (4, "Gaster"),
            (5, "Hepar"),
            (6, "Pancreas"),
            (7, "Jejunum"),
            (8, "Colon descendens"),
            (9, "Rectum"),
        ]
    },
    {
        "id": 22,
        "topic": "Jigar darvoza venasi tizimi",
        "image": "data/images/anatomiya_img_22.png",
        "items": [
            (1, "Oesophagus"),
            (2, "Ventriculus (Gaster)"),
            (3, "Duodenum"),
            (4, "Vesica fellea"),
            (5, "Hepar"),
            (6, "Pancreas"),
            (7, "Jejunum"),
            (8, "Caecum"),
            (9, "Appendix vermiformis"),
            (10, "Colon descendens"),
            (11, "Rectum"),
            (12, "Sphincter ani"),
        ]
    },
    {
        "id": 23,
        "topic": "Jigar anatomiyasi (Hepar)",
        "image": "data/images/anatomiya_img_23.png",
        "items": [
            (1, "Lig. coronarium hepatis"),
            (2, "M. phrenicus (Diaphragma)"),
            (3, "Lig. triangulare"),
            (4, "Lig. falciforme hepatis"),
            (5, "Lobus dexter"),
            (6, "Lobus sinister"),
            (7, "Lig. teres hepatis"),
            (8, "Margo inferior"),
            (9, "Vesica fellea"),
        ]
    },
    {
        "id": 24,
        "topic": "Oshqozon anatomiyasi (Gaster)",
        "image": "data/images/anatomiya_img_24.png",
        "items": [
            (1, "Pars cardiaca"),
            (2, "Fundus ventriculi"),
            (3, "Corpus ventriculi"),
            (4, "Curvatura ventriculi major"),
            (5, "Pars pylorica"),
            (6, "Pars descendens duodeni"),
            (7, "Pars superior duodeni"),
            (8, "Curvatura ventriculi minor"),
            (9, "Oesophagus"),
        ]
    },
    {
        "id": 25,
        "topic": "Oshqozon boylamlari",
        "image": "data/images/anatomiya_img_25.png",
        "items": [
            (1, "Lig. gastropancreaticum"),
            (2, "Lig. pyloropancreaticum"),
            (3, "Lig. gastrophrenicum"),
            (4, "Lig. gastrolienale"),
            (5, "Lig. gastrocolicum"),
            (6, "Lig. gastroduodenale"),
            (7, "Lig. hepatogastricum"),
        ]
    },
    {
        "id": 26,
        "topic": "Kalla suyagi (Cranium)",
        "image": "data/images/anatomiya_img_26.png",
        "items": [
            (1, "Os parietale"),
            (2, "Os frontale"),
            (3, "Os sphenoidale"),
            (4, "Os temporale"),
            (5, "Os lacrimale"),
            (6, "Os nasale"),
            (7, "Os zygomaticum"),
            (8, "Maxilla"),
            (9, "Mandibula"),
        ]
    },
    {
        "id": 27,
        "topic": "Peshona suyagi (Os frontale)",
        "image": "data/images/anatomiya_img_27.png",
        "items": [
            (1, "Squama frontalis"),
            (2, "Linea temporalis"),
            (3, "Foramen supraorbitale"),
            (4, "Incisura frontalis"),
            (5, "Tuber frontale"),
            (6, "Glabella"),
            (7, "Processus zygomaticus"),
            (8, "Pars nasalis"),
        ]
    },
    {
        "id": 28,
        "topic": "Ensa suyagi (Os occipitale)",
        "image": "data/images/anatomiya_img_28.png",
        "items": [
            (1, "Squama occipitalis"),
            (2, "Sulcus sinus sagittalis superioris"),
            (3, "Protuberantia occipitalis interna"),
            (4, "Sulcus sinus transversi"),
            (5, "Crista occipitalis interna"),
            (6, "Foramen magnum"),
            (7, "Sulcus sinus sigmoidei"),
            (8, "Canalis condylaris"),
            (9, "Pars basilaris"),
            (10, "Sulcus sinus petrosi inferioris"),
        ]
    },
    {
        "id": 29,
        "topic": "Miya arterial doirasi",
        "image": "data/images/anatomiya_img_29.png",
        "items": [
            (1, "A. communicans anterior"),
            (2, "A. cerebri anterior"),
            (3, "A. carotis interna"),
            (4, "A. cerebri media"),
            (5, "A. communicans posterior"),
            (6, "A. cerebri posterior"),
            (7, "A. cerebelli superior"),
            (8, "A. basilaris"),
            (9, "A. cerebelli inferior anterior"),
            (10, "A. vertebralis"),
            (11, "A. cerebelli inferior posterior"),
        ]
    },
    {
        "id": 30,
        "topic": "Bosh miya bo'ylama kesimi",
        "image": "data/images/anatomiya_img_30.png",
        "items": [
            (1, "Medulla oblongata"),
            (2, "Pons"),
            (3, "Pedunculus cerebri"),
            (4, "Thalamus"),
            (5, "Hypophysis"),
            (6, "Hypothalamus"),
            (7, "Corpus callosum"),
            (8, "Epiphysis"),
            (9, "Lamina tecti"),
            (10, "Cerebellum"),
        ]
    },
    {
        "id": 31,
        "topic": "Uzunchoq miya (Medulla oblongata)",
        "image": "data/images/anatomiya_img_31.png",
        "items": [
            (1, "Nucleus olivae"),
            (2, "Oliva"),
            (3, "Nervus hypoglossus"),
            (4, "Sulcus lateralis anterior"),
            (5, "Tractus pyramidalis"),
            (6, "Pyramis"),
            (7, "Nervus accessorius"),
            (8, "Decussatio pyramidum"),
        ]
    },
    {
        "id": 32,
        "topic": "Bosh miya bo'laklari",
        "image": "data/images/anatomiya_img_32.png",
        "items": [
            (1, "Lobus frontalis"),
            (2, "Lobus parietalis"),
            (3, "Lobus occipitalis"),
            (4, "Cerebellum"),
            (5, "Medulla oblongata"),
            (6, "Pons"),
            (7, "Mesencephalon"),
            (8, "Lobus temporalis"),
        ]
    },
    {
        "id": 33,
        "topic": "Bosh miya yadrolari",
        "image": "data/images/anatomiya_img_33.png",
        "items": [
            (1, "Insula"),
            (2, "Putamen"),
            (3, "Claustrum"),
            (4, "Capsula externa"),
            (5, "Globus pallidus"),
            (6, "Ventriculus tertius"),
            (7, "Nucleus ruber"),
            (8, "Thalamus opticus"),
            (9, "Cerebellum"),
        ]
    },
    {
        "id": 34,
        "topic": "Bosh miya qorinchalari",
        "image": "data/images/anatomiya_img_34.png",
        "items": [
            (1, "Foramen interventriculare"),
            (2, "Ventriculus lateralis"),
            (3, "Ventriculus tertius"),
            (4, "Aqueductus cerebri"),
            (5, "Ventriculus quartus"),
        ]
    },
    {
        "id": 35,
        "topic": "Miyacha va miya ustuni",
        "image": "data/images/anatomiya_img_35.png",
        "items": [
            (1, "Pedunculi cerebri"),
            (2, "Cortex cerebelli superior"),
            (3, "Hypophysis"),
            (4, "Arbor vitae cerebelli"),
            (5, "Pons"),
            (6, "Nucleus dentatus"),
            (7, "Substantia alba cerebelli"),
            (8, "Medulla oblongata"),
            (9, "Oliva"),
            (10, "Cortex cerebelli inferior"),
            (11, "Medulla spinalis"),
        ]
    },
    {
        "id": 36,
        "topic": "Eshitish a'zolari (Auris)",
        "image": "data/images/anatomiya_img_36.png",
        "items": [
            (1, "Malleus"),
            (2, "Incus"),
            (3, "Canales semicirculares"),
            (4, "Vestibulum"),
            (5, "Nervus vestibulocochlearis"),
            (6, "Cochlea"),
            (7, "Fenestra cochleae"),
            (8, "Stapes"),
            (9, "Membrana tympanica"),
        ]
    },
]

# Pair every 2 diagrams into 18 collections:
COLLECTION_METADATA = [
    (1, 2, "1-rasm, 2-rasm"),
    (3, 4, "3-rasm, 4-rasm"),
    (5, 6, "5-rasm, 6-rasm"),
    (7, 8, "7-rasm, 8-rasm"),
    (9, 10, "9-rasm, 10-rasm"),
    (11, 12, "11-rasm, 12-rasm"),
    (13, 14, "13-rasm, 14-rasm"),
    (15, 16, "15-rasm, 16-rasm"),
    (17, 18, "17-rasm, 18-rasm"),
    (19, 20, "19-rasm, 20-rasm"),
    (21, 22, "21-rasm, 22-rasm"),
    (23, 24, "23-rasm, 24-rasm"),
    (25, 26, "25-rasm, 26-rasm"),
    (27, 28, "27-rasm, 28-rasm"),
    (29, 30, "29-rasm, 30-rasm"),
    (31, 32, "31-rasm, 32-rasm"),
    (33, 34, "33-rasm, 34-rasm"),
    (35, 36, "35-rasm, 36-rasm"),
]

# Fix collection 12 tuple (23, 24)
COLLECTION_METADATA[11] = (23, 24, "Anatomiya 12: Jigar va Oshqozon anatomiyasi")

def generate_questions():
    out_dir = Path("data/anatomiya_collections")
    out_dir.mkdir(parents=True, exist_ok=True)

    headers = [
        "question", "option_a", "option_b", "option_c", "option_d",
        "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
    ]

    collection_summary = []

    for c_idx, (d1_id, d2_id, title) in enumerate(COLLECTION_METADATA, 1):
        d1 = DIAGRAMS[d1_id - 1]
        d2 = DIAGRAMS[d2_id - 1]

        # Combine terms from both diagrams to serve as distractor pool
        pool1 = [name for num, name in d1["items"]]
        pool2 = [name for num, name in d2["items"]]
        combined_pool = pool1 + pool2

        rows = []
        for diag, pool in [(d1, pool1), (d2, pool2)]:
            for num, correct_name in diag["items"]:
                # Select 3 distinct distractors from the diagram pool or combined pool
                distractor_candidates = [item for item in combined_pool if item.lower() != correct_name.lower()]
                # Prefer distractors from same diagram if at least 3
                same_diag_distractors = [item for item in pool if item.lower() != correct_name.lower()]
                if len(same_diag_distractors) >= 3:
                    distractors = random.sample(same_diag_distractors, 3)
                else:
                    distractors = random.sample(distractor_candidates, 3)

                # Assign random position (A, B, C, or D) for correct answer
                choices = [correct_name] + distractors
                random.shuffle(choices)
                correct_letter = chr(ord('A') + choices.index(correct_name))

                q_text = f"Rasmda {num}-raqam bilan qaysi anatomik tuzilma ko'rsatilgan?"
                explanation = f"{num} — {correct_name}"

                rows.append({
                    "question": q_text,
                    "option_a": choices[0],
                    "option_b": choices[1],
                    "option_c": choices[2],
                    "option_d": choices[3],
                    "correct_answer": correct_letter,
                    "explanation": explanation,
                    "topic": diag["topic"],
                    "difficulty": "Medium",
                    "timer": 25,
                    "image": diag["image"]
                })

        filename = f"anatomiya_collection_{c_idx:02d}.csv"
        filepath = out_dir / filename
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        full_title = f"{title} ({len(rows)} ta savol)"
        collection_summary.append({
            "col_num": c_idx,
            "title": full_title,
            "filename": filename,
            "questions_count": len(rows),
            "d1": d1["topic"],
            "d2": d2["topic"],
        })
        print(f"[{c_idx:02d}/18] Generated '{full_title}' -> {len(rows)} questions")

    return collection_summary

if __name__ == "__main__":
    summary = generate_questions()
    total_q = sum(s["questions_count"] for s in summary)
    print(f"\nSuccessfully generated 18 collections with {total_q} total questions!")
