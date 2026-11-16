import asyncio
import pandas as pd
from pathlib import Path
import config
from bot.database.db import Database
from bot.database import queries

# Define all 85 questions
QUESTIONS_PART_1 = [
    {
        "question": "Valin qanday aminokislotalar guruhiga kiradi?",
        "option_a": "Almashinadigan aminokislota",
        "option_b": "Almashinmaydigan (muhim) aminokislota",
        "option_c": "Qisman almashinadigan aminokislota",
        "option_d": "Faqat o'simliklarda uchraydigan aminokislota",
        "correct_answer": "B",
        "explanation": "Valin inson tanasida sintezlanmaydi, faqat oziq-ovqat bilan tushishi shart bo'lgan almashtirib bo'lmaydigan (muhim) aminokislotadir.",
        "topic": "Aminokislotalar tasnifi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Battler − Olbrayt sindromi qanday metabolik buzilish bilan bog'liq?",
        "option_a": "Ammoniy tuzlari (ammoniy ajralishi) buzilishi bilan (buyrak tubulyar atsidozi)",
        "option_b": "Mochevina sintezining to'xtashi bilan",
        "option_c": "Xolesterin so'rilishining buzilishi bilan",
        "option_d": "Glikogen parchalanishining ortishi bilan",
        "correct_answer": "A",
        "explanation": "Battler-Olbrayt sindromi buyrak kanalchalari atsidozi va ammiak/ammoniy tuzlari ekskretsiyasining buzilishi bilan bog'liq.",
        "topic": "Patologik biokimyo",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Alkaptonuriya kasalligi qaysi aminokislota almashinuvining buzilishi bilan bog'liq?",
        "option_a": "Triptofan almashinuvi",
        "option_b": "Tirozin almashinuvining buzilishi bilan bog'liq irsiy kasallik",
        "option_c": "Valin va leysin sintezi",
        "option_d": "Sistein transporti",
        "correct_answer": "B",
        "explanation": "Alkaptonuriya — tirozin va fenilalanin almashinuvidagi gomogentizat-1,2-dioksigenaza fermenti yetishmovchiligi tufayli kelib chiquvchi irsiy kasallik.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 20
    },
    {
        "question": "Digidropteridinreduktaza fermentining irsiy nuqsoni qaysi kasallikka sabab bo'ladi?",
        "option_a": "Fenilketonuriya (variantli / atipik shakli)",
        "option_b": "Albinizm",
        "option_c": "Alkaptonuriya",
        "option_d": "Gistidinemiya",
        "correct_answer": "A",
        "explanation": "Digidropteridinreduktaza BH4 (tetragidrobiopterin) kofaktorini qaytarish uchun kerak bo'lib, uning yetishmovchiligi atipik fenilketonuriyani keltirib chiqaradi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Metilmalonil-KoA-mutaza fermentining irsiy nuqsoni qanday oqibatga olib keladi?",
        "option_a": "Metilmalonik atsiduriya kasalligiga sabab bo'ladi",
        "option_b": "Fenilketonuriyaga sabab bo'ladi",
        "option_c": "Alkaptonuriyaga sabab bo'ladi",
        "option_d": "Izovalerian atsiduriyasiga sabab bo'ladi",
        "correct_answer": "A",
        "explanation": "Metilmalonil-KoA-mutaza (B12 vitaminiga bog'liq) nuqsonida organizmda metilmalon kislotasi to'planib, og'ir atsiduriyaga sabab bo'ladi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Tripsinogen tripsinga qaysi ferment ta'sirida aylanadi?",
        "option_a": "Pepsin ta'sirida",
        "option_b": "Gastriksin ta'sirida",
        "option_c": "Enterokinaza (enteropeptidaza) ta'sirida",
        "option_d": "Ximotripsin ta'sirida",
        "correct_answer": "C",
        "explanation": "O'n ikki barmoqli ichak shilliq qavati ishlab chiqaradigan enterokinaza (enteropeptidaza) tripsinogenni aktiv tripsinga aylantiradi.",
        "topic": "Hazm fermentlari",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Xartnup kasalligi qaysi aminokislota almashinuvi buzilganda rivojlanadi?",
        "option_a": "Triptofan almashinuvi buzilganda",
        "option_b": "Glitsin almashinuvi buzilganda",
        "option_c": "Fenilalanin almashinuvi buzilganda",
        "option_d": "Metionin almashinuvi buzilganda",
        "correct_answer": "A",
        "explanation": "Xartnup kasalligi triptofanning ichakda so'rilishi va buyraklarda reabsorbsiyasining irsiy buzilishi oqibatida rivojlanadi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 20
    },
    {
        "question": "GAMK (γ-aminomoy kislota) qaysi aminokislotaning dekarboksillanishi natijasida hosil bo'ladi?",
        "option_a": "Asparagin kislotasidan",
        "option_b": "Glutamin (glutamat) kislotasidan",
        "option_c": "Tirozindan",
        "option_d": "Gistidindan",
        "correct_answer": "B",
        "explanation": "Glutamat kislotasi glutamatdekarboksilaza fermenti ta'sirida dekarboksillanib GAMK hosil qiladi.",
        "topic": "Biogen aminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Qon tomirlarni toraytiruvchi ta'sirga ega bo'lgan biogen amin qaysi?",
        "option_a": "Gistamin",
        "option_b": "Alanin",
        "option_c": "Serotonin",
        "option_d": "Glitsin",
        "correct_answer": "C",
        "explanation": "Serotonin qon tomirlarni toraytiruvchi (vazokonstriktor) ta'sirga ega kuchli biogen amindir.",
        "topic": "Biogen aminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Glikogen aminokislotalar katabolizmida nima orqali glyukozaga aylanishi mumkin?",
        "option_a": "Katabolizmda piruvatga (yoki Krebs sikli metabolitlariga) aylanadi",
        "option_b": "Asetoatsetatga aylanadi",
        "option_c": "Xolesteringa aylanadi",
        "option_d": "Yog' kislotalariga aylanadi",
        "correct_answer": "A",
        "explanation": "Glikogen aminokislotalar piruvat yoki Krebs sikli oraliq moddalariga aylanib, glyukoneogenezda glyukoza hosil qiladi.",
        "topic": "Aminokislotalar katabolizmi",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Miyaning qora moddasida dofamin yetishmovchiligi qaysi kasallikka olib keladi?",
        "option_a": "Parkinson kasalligiga olib keladi",
        "option_b": "Altsgeymer kasalligiga",
        "option_c": "Epilepsiyaga",
        "option_d": "Xoreyaga",
        "correct_answer": "A",
        "explanation": "Substantia nigra neyronlarining nobud bo'lishi va dofamin yetishmovchiligi Parkinson kasalligiga sabab bo'ladi.",
        "topic": "Biogen aminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Fosfatidilxolin va sfingomiyelin sintezida umumiy o'tmishdosh modda qaysi?",
        "option_a": "ATF",
        "option_b": "TsDF-xolin",
        "option_c": "S-adenozilmetionin",
        "option_d": "Asetil-KoA",
        "correct_answer": "B",
        "explanation": "TsDF-xolin (sitidindifosfat xolin) ham fosfatidilxolin, ham sfingomiyelin sintezida faollashgan xolin donori hisoblanadi.",
        "topic": "Lipidlar va aminokislotalar",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Inson organizmida xolesterin sintezi eng faol ravishda qayerda amalga oshiriladi?",
        "option_a": "Buyraklarda va taloqda",
        "option_b": "Skelet mushaklarida",
        "option_c": "Ichakda (jigar bilan birga)",
        "option_d": "Faqat miyada",
        "correct_answer": "C",
        "explanation": "Endogen xolesterinning asosiy qismi jigar va ingichka ichak shilliq qavatida sintezlanadi.",
        "topic": "Lipidlar metabolizmi",
        "difficulty": "Medium",
        "timer": 20
    },
    {
        "question": "Quyidagi moddalardan qaysi birining kashshofida xolesterin yo'q?",
        "option_a": "Prostaglandinlar (kashshofi — arakidon kislota)",
        "option_b": "D3 vitamini (kashshofi — 7-degidroxolesterol)",
        "option_c": "O't kislotalari",
        "option_d": "Kortizol gormoni",
        "correct_answer": "A",
        "explanation": "Prostaglandinlar arakidon kislotasidan hosil bo'ladi. D vitamini, o't kislotalari va steroidlar esa xolesterindan hosil bo'ladi.",
        "topic": "Biomolekulalar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Xolesterin sintezining asosiy tartibga soluvchi (tezlikni belgilovchi) fermenti qaysi?",
        "option_a": "Xolesterinesteraza",
        "option_b": "Gidroksimetilglutaril-KoA-reduktaza (GMG-KoA-reduktaza)",
        "option_c": "Lesitin-xolesterol-atsiltransferaza",
        "option_d": "Squalen-sintaza",
        "correct_answer": "B",
        "explanation": "Gidroksimetilglutaril-KoA-reduktaza xolesterin biosintezidagi asosiy tezlikni cheklovchi tartibga soluvchi fermentdir.",
        "topic": "Fermentlar",
        "difficulty": "Medium",
        "timer": 25
    }
]

QUESTIONS_PART_2 = [
    {
        "question": "Yo'g'on ichak mikroflorasi ta'sirida triptofandan qanday zaharli mahsulot hosil bo'ladi?",
        "option_a": "Krezol va fenol",
        "option_b": "Indol va skatol",
        "option_c": "Kadaverin va putresin",
        "option_d": "Mochevina va siydik kislotasi",
        "correct_answer": "B",
        "explanation": "Triptofanning ichakda chirishi natijasida indol va skatol, tirozindan esa fenol va krezol hosil bo'ladi.",
        "topic": "Ichakda oqsillarning chirishi",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Tanada ammiakning to'qimalardan jigarga toksik bo'lmagan asosiy transport shakli nima?",
        "option_a": "Erkin ammiak gazi",
        "option_b": "Mochevina",
        "option_c": "Glutamin (shuningdek, mushaklardan jigarga alanin)",
        "option_d": "Kreatinin",
        "correct_answer": "C",
        "explanation": "Ammiak to'qimalarda glutamat bilan birikib zararsiz glutamin hosil qiladi va qon orqali jigarga tashiladi.",
        "topic": "Ammiak metabolizmi",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Karbamid (mochevina) molekulasidagi ikkita azot atomining manbalari nimalar?",
        "option_a": "Biri ammiak (karbamoilfosfat tarkibida), ikkinchisi asparagin kislotasi aminoguruhi",
        "option_b": "Ikkala azot atomi ham erkin ammiakdan",
        "option_c": "Biri glutamindan, ikkinchisi glitsindan",
        "option_d": "Biri arginindan, ikkinchisi ornitindan",
        "correct_answer": "A",
        "explanation": "Mochevinadagi bitta azot karbamoilfosfatdan (ammiak), ikkinchi azot esa aspartat aminoguruhidan olinadi.",
        "topic": "Ornitin sikli",
        "difficulty": "Hard",
        "timer": 30
    },
    {
        "question": "Serin va glitsinning o'zaro konversiyasi qaysi vitaminlarning ichakdagi normal so'rilishiga bog'liq?",
        "option_a": "Vitamin C va vitamin D",
        "option_b": "Foliy kislotasi (B9 — tetragidrofolat) va piridoksin (B6)",
        "option_c": "Vitamin A va vitamin E",
        "option_d": "Vitamin B1 va vitamin B12",
        "correct_answer": "B",
        "explanation": "Serin-gidroksimetiltransferaza fermenti B6 (piridoksalfosfat) va B9 (tetragidrofolat) ishtirokida ishlaydi.",
        "topic": "Vitaminlar va aminokislotalar",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Tripsin qaysi aminokislotalar hosil qilgan peptid bog'larini gidrolizlaydi?",
        "option_a": "Lizin va arginin aminokislotalarining karboksil guruhlari hosil qilgan bog'larni",
        "option_b": "Tirozin va fenilalanin hosil qilgan bog'larni",
        "option_c": "Glitsin va alanin hosil qilgan bog'larni",
        "option_d": "Aspartat va glutamat hosil qilgan bog'larni",
        "correct_answer": "A",
        "explanation": "Tripsin asosli aminokislotalar — lizin va argininning karboksil guruhi ishtirok etgan peptid bog'larini uzadi.",
        "topic": "Hazm fermentlari",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Ximotripsin qaysi aminokislotalar hosil qilgan peptid bog'larini gidrolizlaydi?",
        "option_a": "Lizin va arginin hosil qilgan bog'larni",
        "option_b": "Tirozin, fenilalanin va triptofanning karboksil guruhlari hosil qilgan bog'larni",
        "option_c": "Prolin va gidroksiprolin bog'larini",
        "option_d": "Metionin va sistein bog'larini",
        "correct_answer": "B",
        "explanation": "Ximotripsin aromatik aminokislotalar (tirozin, fenilalanin, triptofan) ning karboksil guruhi hosil qilgan bog'larni uzadi.",
        "topic": "Hazm fermentlari",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Karboksipeptidaza A qaysi aminokislotalar hosil qilgan peptid bog'larini gidrolizlaydi?",
        "option_a": "Polipeptid zanjirning C-uchidagi aromatik va alifatik aminokislotalar hosil qilgan bog'larni",
        "option_b": "Polipeptid zanjirning N-uchidagi aminokislotalarni",
        "option_c": "Zanjir o'rtasidagi asosli aminokislotalarni",
        "option_d": "Faqat lizin va arginin bog'larini",
        "correct_answer": "A",
        "explanation": "Karboksipeptidaza A polipeptid zanjirining C-uchidan aromatik va alifatik aminokislotalarni ajratadi.",
        "topic": "Hazm fermentlari",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Transaminlanish reaksiyasi nima?",
        "option_a": "Aminoguruhni aminokislotadan erkin NH3 sifatida ajratish",
        "option_b": "Aminoguruhni aminokislotadan α-ketokislotaga ko'chirish (erkin NH3 hosil bo'lmasdan)",
        "option_c": "Karboksil guruhining CO2 sifatida ajralishi",
        "option_d": "Peptid bog'larining suv birikishi bilan uzilishi",
        "correct_answer": "B",
        "explanation": "Transaminlanish — aminotransferaza fermenti (kofermenti B6 — piridoksalfosfat) ishtirokida aminoguruhning α-ketokislotaga ko'chirilishi jarayonidir.",
        "topic": "Aminokislotalar metabolizmi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Biogen aminlar aminokislotalardan qaysi reaksiya natijasida hosil bo'ladi?",
        "option_a": "Transaminlanish reaksiyasi natijasida",
        "option_b": "Dekarboksillanish reaksiyasi natijasida",
        "option_c": "Oksidlovchi dezaminlanish natijasida",
        "option_d": "Gidroksillanish reaksiyasi natijasida",
        "correct_answer": "B",
        "explanation": "Aminokislotalar dekarboksilaza fermentlari ta'sirida karboksil guruhini (-COOH) CO2 ko'rinishida yo'qotib biogen aminlar hosil qiladi.",
        "topic": "Biogen aminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Biogen aminlarning inaktivatsiyasini qaysi fermentlar amalga oshiradi?",
        "option_a": "Monoaminoksidaza (MAO) va diaminoksidaza (DAO)",
        "option_b": "Transaminaza va karboksilaza",
        "option_c": "Pepsin va tripsin",
        "option_d": "Laktatdegidrogenaza va amilaza",
        "correct_answer": "A",
        "explanation": "Biogen aminlar MAO va DAO fermentlari ishtirokida oksidlovchi dezaminlanish orqali zararsizlantiriladi.",
        "topic": "Biogen aminlar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Tormozlovchi neyrotransmitter γ-aminomoy kislota qaysi aminokislotaning dekarboksillanishidan hosil bo'ladi?",
        "option_a": "Glitsindan",
        "option_b": "Glutamin (glutamat) kislotasidan",
        "option_c": "Asparagin kislotasidan",
        "option_d": "Tirozindan",
        "correct_answer": "B",
        "explanation": "Glutamat kislotasi B6 kofermenti ishtirokida dekarboksillanib, GAMK (GABA) hosil qiladi.",
        "topic": "Biogen aminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Fenilalanin organizmda qaysi birikmalarni sintez qilishda ishtirok etadi?",
        "option_a": "Tirozin, katexolaminlar (dofamin, noradrenalin, adrenalin), tireoid gormonlar va melanin",
        "option_b": "Faqat xolesterin va yog' kislotalari",
        "option_c": "Gemoglobin va mioglobinning oqsil bo'lmagan qismi",
        "option_d": "Faqat o't kislotalari",
        "correct_answer": "A",
        "explanation": "Fenilalanin dastlab tirozinga aylanadi, undan esa katexolaminlar, qalqonsimon bez gormonlari va melanin pigmenti sintezlanadi.",
        "topic": "Aminokislotalar ixtisoslashishi",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Ba'zi almashinadigan aminokislotalar inson tanasida qanday sintezlanadi?",
        "option_a": "Uglevod va lipidlar almashinuvi mahsulotlaridan (α-ketokislotalardan transaminlanish orqali)",
        "option_b": "Faqat nuklein kislotalar parchalanishidan",
        "option_c": "To'g'ridan-to'g'ri molekulyar azotni fiksatsiya qilish orqali",
        "option_d": "Faqat vitaminlarning o'zgarishi orqali",
        "correct_answer": "A",
        "explanation": "Glikoliz va Krebs siklining oraliq α-ketokislotalari transaminlanish orqali mos almashinadigan aminokislotalarga aylanadi.",
        "topic": "Aminokislotalar sintezi",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Tananing qaysi holatida ijobiy azot balansi kuzatiladi?",
        "option_a": "O'sish davrida, homiladorlik va laktatsiyada, kasallikdan tuzalish davrida",
        "option_b": "Och qolganda va oqsilsiz parhezda",
        "option_c": "Og'ir kuyish va jarohatlarda",
        "option_d": "Qarilikda va kaxeksiyada",
        "correct_answer": "A",
        "explanation": "Oqsil sintezi uning parchalanishidan ustun bo'lgan holatlarda ijobiy azot balansi kuzatiladi.",
        "topic": "Azot balansi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Tananing qaysi holatida salbiy azot balansi kuzatiladi?",
        "option_a": "Bolalarning tez o'sish davrida",
        "option_b": "Homiladorlik davrida",
        "option_c": "Och qolganda, oqsilsiz parhezda, og'ir kasalliklar, kuyish, jarohat va qarilikda",
        "option_d": "Mushak massasini oshirish mashg'ulotlarida",
        "correct_answer": "C",
        "explanation": "Oqsil parchalanishi sintezdan oshib ketganda va oqsil tanqisligida salbiy azot balansi vujudga keladi.",
        "topic": "Azot balansi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Yangi tug'ilgan chaqaloqlarda oshqozonda oqsillar gidrolizini nima katalizlaydi?",
        "option_a": "Tripsin va elastaza",
        "option_b": "Rennin (ximozin) va gastriksin",
        "option_c": "Faqat pepsin A",
        "option_d": "Aminopeptidaza va karboksipeptidaza",
        "correct_answer": "B",
        "explanation": "Chaqaloqlarda sut oqsili kazeinni iviydigan asosiy ferment rennin (ximozin) hisoblanadi.",
        "topic": "Hazm fermentlari",
        "difficulty": "Medium",
        "timer": 20
    },
    {
        "question": "Katta yoshdagi odamlar oshqozonida oqsillar gidrolizini nima katalizlaydi?",
        "option_a": "Pepsin (va gastriksin), xlorid kislota ishtirokida",
        "option_b": "Enterokinaza va tripsin",
        "option_c": "Faqat oshqozon amilazasi",
        "option_d": "Faqat ximotripsin",
        "correct_answer": "A",
        "explanation": "Pepsinogen HCl ta'sirida pepsinga aylanib, oshqozonda oqsillarni polipeptidlargacha parchalaydi.",
        "topic": "Hazm fermentlari",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Ingichka ichakdagi oqsillar gidrolizini qaysi fermentlar majmuasi katalizlaydi?",
        "option_a": "Tripsin, ximotripsin, elastaza, karboksipeptidaza A va B, aminopeptidaza, dipeptidazalar",
        "option_b": "Faqat pepsin va rennin",
        "option_c": "Faqat oshqozon osti bezi lipazasi",
        "option_d": "Pepsin va xlorid kislota",
        "correct_answer": "A",
        "explanation": "Ichakda oshqozon osti bezi va ichak shirasining endo- va ekzopeptidazalari oqsillarni erkin aminokislotalargacha parchalaydi.",
        "topic": "Hazm fermentlari",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Kattalar uchun almashtiriladigan va bolalar uchun qisman almashtiriladigan aminokislotalarni ko'rsating:",
        "option_a": "Valin, leysin, izoleysin",
        "option_b": "Arginin, tirozin va gistidin",
        "option_c": "Glitsin va alanin",
        "option_d": "Faqat prolin",
        "correct_answer": "B",
        "explanation": "Arginin va gistidin bolalarning o'suvchi organizmida yetarli darajada sintezlanmaydi, shuning uchun qisman almashtirib bo'lmaydi.",
        "topic": "Aminokislotalar tasnifi",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Bolalarda oqsil yetishmovchiligi tufayli qanday og'ir kasallik rivojlanadi?",
        "option_a": "Kvashiorkor (oqsil yetishmovchiligi: o'sishdan to'xtash, shishlar, anemiya)",
        "option_b": "Pellagra",
        "option_c": "Raxit",
        "option_d": "Skorbut",
        "correct_answer": "A",
        "explanation": "Kvashiorkor oziq-ovqatda oqsil tanqis bo'lganda rivojlanuvchi kasallik bo'lib, gipoproteinemiya, shishlar va jigar distrofiyasi bilan kechadi.",
        "topic": "Oqsil tanqisligi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Yangi tug'ilgan chaqaloqlarda me'da shirasi qanday pH ga ega?",
        "option_a": "pH 1,0–1,5",
        "option_b": "Taxminan pH 5,0–6,0 (kuchsiz kislotali, neytralga yaqin)",
        "option_c": "pH 8,0–9,0",
        "option_d": "Mutlaq neytral pH 7,0",
        "correct_answer": "B",
        "explanation": "Chaqaloqlarda oshqozon kislotaligi past (pH 5,0–6,0) bo'lib, keyinchalik kislotalik ortib 1,5–2,0 ga yetadi.",
        "topic": "Hazm a'zolari biokimyosi",
        "difficulty": "Medium",
        "timer": 20
    },
    {
        "question": "Ornitin siklining buzilishi bilan qanday irsiy kasalliklar bog'liq?",
        "option_a": "Sitrullinemiya, argininsuksinat atsiduriya, giperammoniemiya (I va II tur)",
        "option_b": "Alkaptonuriya va albinizm",
        "option_c": "Fenilketonuriya va sistinoz",
        "option_d": "Podagra va diabet",
        "correct_answer": "A",
        "explanation": "Mochevina hosil bo'lish sikli fermentlari defektida oraliq birikmalar (sitrullin, argininsuksinat) va ammiak qonda ortadi.",
        "topic": "Ornitin sikli",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Tirozin almashinuvining buzilishi bilan bog'liq irsiy kasalliklarni ko'rsating:",
        "option_a": "Kvashiorkor va kaxeksiya",
        "option_b": "Alkaptonuriya, albinizm, tirozinemiya",
        "option_c": "Gomosistinuriya va sistinuriya",
        "option_d": "Glitsinoz va glitsinuriya",
        "correct_answer": "B",
        "explanation": "Tirozin katabolizmi buzilishi alkaptonuriya, tirozinemiya va melanin sintezi buzilishi albinizmga olib keladi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Ekzopeptidazalarga quyidagilar kiradi:",
        "option_a": "Pepsin va tripsin",
        "option_b": "Karboksipeptidaza A va B, aminopeptidazalar (peptidning uchidan uzadi)",
        "option_c": "Ximotripsin va elastaza",
        "option_d": "Faqat gastriksin",
        "correct_answer": "B",
        "explanation": "Ekzopeptidazalar peptid zanjirining uchlaridan bittalab aminokislota ajratib oladi.",
        "topic": "Hazm fermentlari",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Endopeptidazalarga quyidagi fermentlar kiradi:",
        "option_a": "Karboksipeptidaza va aminopeptidaza",
        "option_b": "Pepsin, gastriksin, tripsin, ximotripsin, elastaza (ichki peptid bog'larni uzadi)",
        "option_c": "Dipeptidazalar",
        "option_d": "Faqat enterokinaza",
        "correct_answer": "B",
        "explanation": "Endopeptidazalar oqsil molekulasining ichki qismidagi peptid bog'larini gidrolizlaydi.",
        "topic": "Hazm fermentlari",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Yo'g'on ichak mikroflorasi ta'sirida tirozindan qanday zaharli mahsulot hosil bo'ladi?",
        "option_a": "Indol va skatol",
        "option_b": "Krezol va fenol",
        "option_c": "Kadaverin va putresin",
        "option_d": "Ammiak va karbonat angidrid",
        "correct_answer": "B",
        "explanation": "Tirozindan ichak bakteriyalari ta'sirida fenol va krezol, triptofandan esa indol va skatol hosil bo'ladi.",
        "topic": "Ichakda oqsillarning chirishi",
        "difficulty": "Medium",
        "timer": 20
    },
    {
        "question": "Qaysi aminokislota inson to'qimalarida to'g'ridan-to'g'ri oksidlovchi dezaminlanishga uchraydi?",
        "option_a": "Glutamin kislotasi (glutamatdegidrogenaza ishtirokida)",
        "option_b": "Valin",
        "option_c": "Glitsin",
        "option_d": "Lizin",
        "correct_answer": "A",
        "explanation": "Glutamatdegidrogenaza fermenti orqali to'g'ridan-to'g'ri va tezkor oksidlovchi dezaminlanadigan asosiy aminokislota glutamatdir.",
        "topic": "Aminokislotalar dezaminlanishi",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Serotonin qaysi moddaning dekarboksillanishidan hosil bo'ladi?",
        "option_a": "Tirozindan",
        "option_b": "5-Gidroksitriptofandan (triptofandan)",
        "option_c": "Gistidindan",
        "option_d": "Glutamatdan",
        "correct_answer": "B",
        "explanation": "Triptofan dastlab 5-gidroksitriptofanga aylanadi, so'ngra dekarboksillanib serotonin hosil bo'ladi.",
        "topic": "Biogen aminlar",
        "difficulty": "Medium",
        "timer": 20
    },
    {
        "question": "γ-Aminomoy kislota (GAMK) qaysi moddaning dekarboksillanishidan hosil bo'ladi?",
        "option_a": "Glutamat (glutamin kislotasi) dan",
        "option_b": "Aspartatdan",
        "option_c": "Serindan",
        "option_d": "Metionindan",
        "correct_answer": "A",
        "explanation": "Glutamat kislotasi glutamatdekarboksilaza ishtirokida dekarboksillanib GAMK hosil qiladi.",
        "topic": "Biogen aminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Gistidinning dekarboksillanishi natijasida nima hosil bo'ladi?",
        "option_a": "Serotonin",
        "option_b": "Gistamin (gistidindan)",
        "option_c": "Dofamin",
        "option_d": "Tiroksin",
        "correct_answer": "B",
        "explanation": "Gistidindekarboksilaza ta'sirida gistidindan biologik faol amin — gistamin hosil bo'ladi.",
        "topic": "Biogen aminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Qaysi biogen amin markaziy nerv sistemasida tormozlovchi neyrotransmitter hisoblanadi?",
        "option_a": "Adrenalin",
        "option_b": "Gamma-aminomoy kislota (GAMK)",
        "option_c": "Gistamin",
        "option_d": "Noradrenalin",
        "correct_answer": "B",
        "explanation": "GAMK bosh miya po'stlog'idagi asosiy tormozlovchi vositachi hisoblanadi.",
        "topic": "Biogen aminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Kadavr zahari bo'lgan biogen aminlar qaysilar?",
        "option_a": "Kadaverin (lizindan) va putresin (ornitindan)",
        "option_b": "Fenol va krezol",
        "option_c": "Indol va skatol",
        "option_d": "Mochevina va siydik kislotasi",
        "correct_answer": "A",
        "explanation": "Oqsillarning chirishida lizin va ornitinning dekarboksillanishidan kadaverin va putresin (ptomainlar) hosil bo'ladi.",
        "topic": "Biogen aminlar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Oshqozonda qaysi biogen amin HCl sekretsiyasini kuchli rag'batlantiradi?",
        "option_a": "Serotonin",
        "option_b": "Gistamin",
        "option_c": "Dofamin",
        "option_d": "GAMK",
        "correct_answer": "B",
        "explanation": "Gistamin me'da parietal hujayralaridagi H2-retseptorlarni qo'zg'atib, xlorid kislota ajralishini rag'batlantiradi.",
        "topic": "Biogen aminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Monoaminoksidaza (MAO) fermentining kofermenti nima?",
        "option_a": "FAD",
        "option_b": "NAD+",
        "option_c": "Piridoksalfosfat (B6)",
        "option_d": "Tiamindifosfat (B1)",
        "correct_answer": "A",
        "explanation": "MAO flavoprotein bo'lib, uning kofaktori FAD (flavinadenindinukleotid) hisoblanadi.",
        "topic": "Fermentlar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Ornitin siklining yakuniy mahsuloti nima?",
        "option_a": "Siydik kislotasi",
        "option_b": "Mochevina (karbamid)",
        "option_c": "Kreatinin",
        "option_d": "Karbamoilfosfat",
        "correct_answer": "B",
        "explanation": "Ornitin sikli orqali ammiak zararsiz yakuniy mahsulot — mochevina (karbamid)ga aylanadi.",
        "topic": "Ornitin sikli",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Qaysi kasalliklar ornitin sikli fermentlari buzilishi bilan bog'liq?",
        "option_a": "Sitrullinemiya, argininsuksinat atsiduriya, giperammoniemiya",
        "option_b": "Fenilketonuriya va albinizm",
        "option_c": "Alkaptonuriya va podagra",
        "option_d": "Seliakiya va mukovissidoz",
        "correct_answer": "A",
        "explanation": "Ornitin sikli fermentlarining tug'ma yetishmovchiligi qonda ammiak va sikl metabolitlarining to'planishiga sabab bo'ladi.",
        "topic": "Ornitin sikli",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Yangi tug'ilgan chaqaloqlarda ammiakni zararsizlantirishning asosiy usuli qaysi?",
        "option_a": "Glutamin sintezi (glutaminsintetaza)",
        "option_b": "Jigarda mochevina hosil qilish",
        "option_c": "O'pka orqali chiqarish",
        "option_d": "Kreatin sintezi",
        "correct_answer": "A",
        "explanation": "Chaqaloqlarda ornitin sikli fermentlari to'liq faollashmagani sababli ammiak asosan glutamin sintezi orqali zararsizlantiriladi.",
        "topic": "Ammiak metabolizmi",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Kattalarda ammiakni zararsizlantirishning asosiy usuli qaysi?",
        "option_a": "Mochevina sintezi (ornitin sikli, jigarda)",
        "option_b": "Siydik kislotasiga aylantirish",
        "option_c": "Teri orqali ajratish",
        "option_d": "Glitsin hosil qilish",
        "correct_answer": "A",
        "explanation": "Katta yoshdagi sog'lom odamda ammiakning 80% dan ortig'i jigarda ornitin sikli orqali mochevinaga aylantiriladi.",
        "topic": "Ornitin sikli",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Glitsin ajratuvchi ferment tizimining nuqsoni bilan qaysi irsiy kasallik rivojlanadi?",
        "option_a": "Glitsinoz (glitsin ensefalopatiyasi, glitsin ajratuvchi tizim nuqsoni)",
        "option_b": "Fenilketonuriya",
        "option_c": "Alkaptonuriya",
        "option_d": "Tirozinemiya",
        "correct_answer": "A",
        "explanation": "Glitsin-cleavage system (glitsin parchalovchi tizim) nuqsonida likvor va qonda glitsin to'planib, glitsinoz rivojlanadi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "S-adenozilmetionin (SAM) qaysi reaksiyalarda ishtirok etadi?",
        "option_a": "Transmetillanish (metil guruhini ko'chirish): adrenalin, kreatin, fosfatidilxolin sintezi",
        "option_b": "Transaminlanish reaksiyalarida",
        "option_c": "Oksidlovchi fosforillanishda",
        "option_d": "Dekarboksillanish reaksiyalarida",
        "correct_answer": "A",
        "explanation": "S-adenozilmetionin (SAM) hujayrada metil guruhlarining universal donori hisoblanadi.",
        "topic": "Transmetillanish",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Ishlayotgan mushakda ATF ning tez hosil bo'lishi qaysi modda ishtirokida sodir bo'ladi?",
        "option_a": "Kreatinfosfat (kreatinkinaza ishtirokida)",
        "option_b": "Glikogen",
        "option_c": "Xolesterin",
        "option_d": "Triglitseridlar",
        "correct_answer": "A",
        "explanation": "Kreatinfosfat o'zining yuqori energiyali fosfatini ADF ga berib, bir lahzada ATF ni qayta hosil qiladi.",
        "topic": "Mushaklar biokimyosi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Almashinadigan aminokislota sistein qaysi aminokislotalardan sintezlanadi?",
        "option_a": "Metionin (oltingugurt manbayi) va serindan",
        "option_b": "Valin va leysindan",
        "option_c": "Tirozin va triptofandan",
        "option_d": "Alanin va glitsindan",
        "correct_answer": "A",
        "explanation": "Sistein sintezida oltingugurt atomi metionindan, uglerod skeleti esa serindan olinadi.",
        "topic": "Aminokislotalar sintezi",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Sistein dimeri nima deb ataladi?",
        "option_a": "Sistin",
        "option_b": "Metionin",
        "option_c": "Gomosistein",
        "option_d": "Taurin",
        "correct_answer": "A",
        "explanation": "Ikki molekula sistein disulfid bog'i orqali birlashib sistin dimerini hosil qiladi.",
        "topic": "Aminokislotalar tuzilishi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Fenilalanin inson tanasida gidroksillanganda nima hosil bo'ladi?",
        "option_a": "Tirozin",
        "option_b": "Triptofan",
        "option_c": "Treonin",
        "option_d": "Gistidin",
        "correct_answer": "A",
        "explanation": "Fenilalaningidroksilaza fermenti fenilalaninni gidroksillab tirozinga aylantiradi.",
        "topic": "Aminokislotalar metabolizmi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Fenilalanindan tirozin hosil bo'lishini qaysi ferment katalizlaydi?",
        "option_a": "Fenilalaningidroksilaza (koferment — tetragidrobiopterin)",
        "option_b": "Tirozinaza",
        "option_c": "Fenilalanintransaminaza",
        "option_d": "Dofamin-beta-gidroksilaza",
        "correct_answer": "A",
        "explanation": "Fenilalaningidroksilaza fermenti tetragidrobiopterin (BH4) kofaktori ishtirokida fenilalanindan tirozin hosil qiladi.",
        "topic": "Fermentlar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Melanotsitlarda melanin qaysi aminokislotadan hosil bo'ladi?",
        "option_a": "Tirozin (tirozinaza fermenti)",
        "option_b": "Glitsin",
        "option_c": "Valin",
        "option_d": "Sistein",
        "correct_answer": "A",
        "explanation": "Tirozinaza fermenti ta'sirida tirozindan qora pigment — melanin sintezlanadi.",
        "topic": "Pigmentlar sintezi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Asab to'qimasidagi katexolaminlar qaysi aminokislotadan hosil bo'ladi?",
        "option_a": "Tirozin",
        "option_b": "Glitsin",
        "option_c": "Prolin",
        "option_d": "Lizin",
        "correct_answer": "A",
        "explanation": "Tirozindan dofamin, noradrenalin va adrenalin sintezlanadi.",
        "topic": "Katexolaminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Qalqonsimon bezda tireoid gormonlari qaysi aminokislotadan sintezlanadi?",
        "option_a": "Tirozin (tiroglobulin tarkibida)",
        "option_b": "Triptofan",
        "option_c": "Fenilalanin",
        "option_d": "Gistidin",
        "correct_answer": "A",
        "explanation": "Tiroglobulin tarkibidagi tirozin qoldiqlari yodlanib T3 va T4 gormonlariga aylanadi.",
        "topic": "Gormonlar biokimyosi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Katexolaminlarga quyidagilar kiradi:",
        "option_a": "Dofamin, noradrenalin va adrenalin",
        "option_b": "Serotonin, gistamin, melatonin",
        "option_c": "Tiroksin va triyodtironin",
        "option_d": "Insulin va glyukagon",
        "correct_answer": "A",
        "explanation": "Dofamin, noradrenalin va adrenalin pirokatexin yadrosiga ega katexolaminlar hisoblanadi.",
        "topic": "Katexolaminlar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Qalqonsimon bez follikulalarida tireoid gormonlari oqsil tarkibidagi qaysi qoldiqlardan hosil bo'ladi?",
        "option_a": "Tirozin (tiroglobulindagi tirozin qoldiqlari yodlanib T3 va T4 hosil bo'ladi)",
        "option_b": "Erkin triptofan",
        "option_c": "Fenilalanin",
        "option_d": "Gistidin",
        "correct_answer": "A",
        "explanation": "Tiroksin va triyodtironin tiroglobulin tarkibidagi tirozin qoldiqlarining yodlanishi natijasida hosil bo'ladi.",
        "topic": "Gormonlar biokimyosi",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Leysin, valin, izoleysin metabolizmida qaysi ko'p fermentli kompleks ishtirok etadi?",
        "option_a": "Tarmoqlangan zanjirli α-ketokislotalar degidrogenaza kompleksi",
        "option_b": "Piruvatdegidrogenaza kompleksi",
        "option_c": "alfa-Ketoglutaratdegidrogenaza kompleksi",
        "option_d": "Suksinatdegidrogenaza",
        "correct_answer": "A",
        "explanation": "Tarmoqlangan zanjirli aminokislotalarning katabolizmida tarmoqlangan zanjirli α-ketokislotalar degidrogenaza kompleksi qatnashadi.",
        "topic": "Aminokislotalar metabolizmi",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Me'da shirasining umumiy kislotaligi 80 ga teng bo'lsa (norma 40-60), ya'ni bemorda:",
        "option_a": "Giperxlorgidriya (kislotalik oshgan)",
        "option_b": "Gipoxlorgidriya",
        "option_c": "Axlorgidriya",
        "option_d": "Anasid holat",
        "correct_answer": "A",
        "explanation": "Umumiy kislotalik 60 dan yuqori bo'lishi giperxlorgidriya (kislotalik oshishi) deb baholanadi.",
        "topic": "Oshqozon sekretsiyasi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Me'da shirasining umumiy kislotaligi 20 ga teng bo'lsa (norma 40-60), ya'ni bemorda:",
        "option_a": "Giperxlorgidriya",
        "option_b": "Gipoxlorgidriya (kislotalik pasaygan)",
        "option_c": "Normotsid holat",
        "option_d": "Giperatsid holat",
        "correct_answer": "B",
        "explanation": "Kislotalik ko'rsatkichi 40 dan past bo'lsa, bu gipoxlorgidriya (kislotalik pasayishi) hisoblanadi.",
        "topic": "Oshqozon sekretsiyasi",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Kislotalikning pasayishi va oshqozon shirasida sut kislotasining mavjudligi qaysi holat uchun xos?",
        "option_a": "Oshqozon saratoni (axlorgidriya, anasid holat)",
        "option_b": "O'n ikki barmoqli ichak yarasi",
        "option_c": "Giperasid gastrit",
        "option_d": "O't tosh kasalligi",
        "correct_answer": "A",
        "explanation": "Axlorgidriyada o'sma to'qimalarining anaerob glikolizi natijasida oshqozonda sut kislotasi to'planadi.",
        "topic": "Klinik biokimyo",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Oshqozon shirasida kislotalikning ko'payishi va safro kislotalarining mavjudligi qaysi holat uchun xos?",
        "option_a": "O'n ikki barmoqli ichak yarasi, giperasid gastrit (safro reflyuksi bilan)",
        "option_b": "Oshqozon saratoni",
        "option_c": "Atrofik anasid gastrit",
        "option_d": "Jigar sirrozi",
        "correct_answer": "A",
        "explanation": "Yuqori kislotalik va duodenogastral safro reflyuksi ko'pincha o'n ikki barmoqli ichak yarasida kuzatiladi.",
        "topic": "Klinik biokimyo",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Don tarkibidagi oqsillarga (bug'doy, jo'xori, javdar) chidamsizlik qaysi kasallikda kuzatiladi?",
        "option_a": "Seliakiya (glyuten enteropatiyasi)",
        "option_b": "Mukovissidoz",
        "option_c": "Kron kasalligi",
        "option_d": "Nospetsifik yarali kolit",
        "correct_answer": "A",
        "explanation": "Seliakiya — glyuten oqsiliga nisbatan tug'ma chidamsizlik bo'lib, ingichka ichak vorsinkalari atrofiyasiga olib keladi.",
        "topic": "Oqsil patologiyalari",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Bolalarda grippdan keyin ferment ingibirlanishi tufayli paydo bo'lishi mumkin bo'lgan giperammoniemiya qaysi sindrom?",
        "option_a": "Rey sindromi (ornitin sikli fermentlarining ingibirlanishi)",
        "option_b": "Daun sindromi",
        "option_c": "Terner sindromi",
        "option_d": "Klaynfelter sindromi",
        "correct_answer": "A",
        "explanation": "Rey sindromida virusli kasallik va aspirin qabulidan keyin jigar mitoxondriyalaridagi ornitin sikli fermentlari ingibirlanadi.",
        "topic": "Klinik biokimyo",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Buyraklarda glitsin reabsorbsiyasining buzilishi nimaga olib keladi?",
        "option_a": "Glitsinuriya",
        "option_b": "Proteinuriya",
        "option_c": "Gematuriya",
        "option_d": "Glyukozuriya",
        "correct_answer": "A",
        "explanation": "Buyrak naychalarida glitsin tashuvchi tizim nuqsonida glitsinning siydik bilan ajralishi ortadi (glitsinuriya).",
        "topic": "Buyraklar biokimyosi",
        "difficulty": "Medium",
        "timer": 20
    },
    {
        "question": "Osteoporoz, ko'z linzalarining siljishi, aqliy zaiflik qaysi kasallikda kuzatiladi?",
        "option_a": "Gomosistinuriya",
        "option_b": "Fenilketonuriya",
        "option_c": "Albinizm",
        "option_d": "Gistidinemiya",
        "correct_answer": "A",
        "explanation": "Gomosistinuriya — sistationin-beta-sintaza fermenti nuqsoni bo'lib, suyak va biriktiruvchi to'qima anomaliyalari bilan kechadi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Buyrak kanallarida sistin toshlarining paydo bo'lishi qaysi kasallikda kuzatiladi?",
        "option_a": "Sistinuriya",
        "option_b": "Sistinoz",
        "option_c": "Alkaptonuriya",
        "option_d": "Oksaluriya",
        "correct_answer": "A",
        "explanation": "Sistinuriya buyrakda sistin, lizin, arginin va ornitin reabsorbsiyasi buzilishidir; sistin yomon eriganligi uchun tosh hosil qiladi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Retikuloendotelial tizim va parenximal organlarda sistin kristallarining shakllanishi qaysi kasallikda kuzatiladi?",
        "option_a": "Sistinuriya",
        "option_b": "Sistinoz",
        "option_c": "Podagra",
        "option_d": "Albinizm",
        "correct_answer": "B",
        "explanation": "Sistinoz — lizosomalarda sistin tashuvchisi nuqsoni bo'lib, a'zolarda sistin kristallari to'planishi bilan xarakterlanadi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Fenilketonuriyada fenilalanin almashinuvining qanday toksik yon mahsulotlari to'planadi?",
        "option_a": "Fenilpiruvat, fenillaktat, fenilsirka kislota",
        "option_b": "Asetoatsetat va gidroksibutirat",
        "option_c": "Indol va skatol",
        "option_d": "Krezol va fenol",
        "correct_answer": "A",
        "explanation": "Fenilalanin fenilalaningidroksilaza yetishmovchiligida fenilpiruvat, fenillaktat va fenilsirka kislotaga aylanadi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Variantli (atipik) fenilketonuriyaning sababi qaysi ferment nuqsoni hisoblanadi?",
        "option_a": "Digidropteridinreduktaza (yoki tetragidrobiopterin sintezi) nuqsoni",
        "option_b": "Faqat fenilalaningidroksilaza yo'qligi",
        "option_c": "Tirozinaza fermenti nuqsoni",
        "option_d": "Arginaza fermenti nuqsoni",
        "correct_answer": "A",
        "explanation": "Variantli fenilketonuriyada fenilalaningidroksilaza kofaktori BH4 (tetragidrobiopterin) sintezi yoki qaytarilishi buzilgan bo'ladi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Hard",
        "timer": 25
    },
    {
        "question": "Aqliy zaiflik, 'sichqon' hidi, qon va siydikda fenilalaninning ko'payishi qaysi kasallikda kuzatiladi?",
        "option_a": "Alkaptonuriya",
        "option_b": "Fenilketonuriya",
        "option_c": "Galaktozemiya",
        "option_d": "Gistidinemiya",
        "correct_answer": "B",
        "explanation": "Fenilketonuriyada to'plangan fenilsirka kislotasi siydik va terga o'ziga xos sichqon (mog'or) hidini beradi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Oqargan teri, oq sochlar va qizil ko'zli bolada qaysi ferment genetik yo'q bo'ladi?",
        "option_a": "Tirozinaza (albinizm)",
        "option_b": "Gomogentizatoksidaza",
        "option_c": "Fenilalaningidroksilaza",
        "option_d": "Arginaza",
        "correct_answer": "A",
        "explanation": "Tirozinaza fermenti yetishmovchiligida tirozindan melanin pigmenti hosil bo'lmaydi (albinizm).",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Chaqaloq siydik chiqargandan keyin tagliklarda qora dog'lar paydo bo'lsa, bu qaysi kasallik?",
        "option_a": "Fenilketonuriya",
        "option_b": "Alkaptonuriya (gomogentizin kislota)",
        "option_c": "Sistinuriya",
        "option_d": "Tirozinemiya",
        "correct_answer": "B",
        "explanation": "Alkaptonuriyada gomogentizin kislotasi siydikda havo kislorodi ta'sirida oksidlanib, qora pigment hosil qiladi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Easy",
        "timer": 20
    },
    {
        "question": "Yangi tug'ilgan bolada qusish, diareya, 'qaynatilgan karam' hidi, qonda tirozin miqdorining ko'payishi qaysi kasallikka xos?",
        "option_a": "Gistidinemiya",
        "option_b": "Tirozinemiya",
        "option_c": "Albinizm",
        "option_d": "Fenilketonuriya",
        "correct_answer": "B",
        "explanation": "Tirozinemiya (I tur) da tirozin almashinuvi buzilib, xarakterli karam hidi va og'ir jigar-buyrak zararlanishi kuzatiladi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Kasal bolada qon plazmasi va siydikda leysin, valin, izoleysin va ularga mos α-ketokislotalar ko'payadi. Bu qaysi kasallik?",
        "option_a": "Zarang siropi kasalligi (maple syrup urine disease)",
        "option_b": "Fenilketonuriya",
        "option_c": "Alkaptonuriya",
        "option_d": "Gomosistinuriya",
        "correct_answer": "A",
        "explanation": "Tarmoqlangan zanjirli aminokislotalar ketokislotalarining oksidlovchi dekarboksillanishi buzilishi natijasida zarang siropi kasalligi kelib chiqadi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 25
    },
    {
        "question": "Zarang siropi kasalligi qaysi metabolik buzilishlar bilan kuzatiladi?",
        "option_a": "Tarmoqlangan zanjirli aminokislotalar (leysin, izoleysin, valin) almashinuvining buzilishi bilan",
        "option_b": "Aromatik aminokislotalar buzilishi bilan",
        "option_c": "Oltingugurtli aminokislotalar buzilishi bilan",
        "option_d": "Asosli aminokislotalar buzilishi bilan",
        "correct_answer": "A",
        "explanation": "Leysin, izoleysin va valin tarmoqlangan zanjirli aminokislotalar bo'lib, zarang siropi kasalligida ularning parchalanishi buziladi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 20
    },
    {
        "question": "Alkaptonuriyaning sababi qaysi ferment nuqsoni?",
        "option_a": "Tirozinaminotransferaza",
        "option_b": "Gomogentizat-1,2-dioksigenaza (gomogentizin kislota oksidaza)",
        "option_c": "Fumarilatsetoatsetathidrolaza",
        "option_d": "Fenilalaningidroksilaza",
        "correct_answer": "B",
        "explanation": "Gomogentizat-1,2-dioksigenaza yetishmovchiligida gomogentizin kislotasi parchalanmay to'qima va siydikda to'planadi.",
        "topic": "Irsiy fermentopatiyalar",
        "difficulty": "Medium",
        "timer": 25
    }
]

async def main():
    print("Initializing Database...")
    db = Database(config.DB_PATH)
    await db.init()

    all_questions = QUESTIONS_PART_1 + QUESTIONS_PART_2
    print(f"Total questions compiled: {len(all_questions)}")

    # 1. Export Excel and CSV for administration & downloads
    excel_path = config.DATA_DIR / "oqsillar_almashinuvi_85.xlsx"
    csv_path = config.DATA_DIR / "oqsillar_almashinuvi_85.csv"

    df = pd.DataFrame(all_questions)
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Oqsillar Almashinuvi")
        worksheet = writer.sheets["Oqsillar Almashinuvi"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 15)

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Saved Excel file: {excel_path}")
    print(f"Saved CSV file: {csv_path}")

    # 2. Insert into SQLite Database
    async with db.get_connection() as conn:
        # Bitta umumiy to'liq imtihon (85 ta savol)
        admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else 5606522749
        q_id = await queries.create_quiz(
            conn,
            title="Oqsillar almashinuvi — To'liq Imtihon (85 ta savol)",
            description="Oqsillar almashinuvi mavzusidagi barcha 85 ta savoldan iborat to'liq imtihon testi.",
            category="Biokimyo",
            default_timer=25,
            shuffle_options=True,
            show_explanation=True,
            pass_percentage=70,
            is_published=True,
            created_by=admin_id
        )
        c = await queries.bulk_insert_questions(conn, q_id, all_questions)
        print(f"Quiz created (ID: {q_id}): inserted {c} questions.")

        # Verify in database
        total_quizzes = await queries.count_quizzes(conn, published_only=True)
        total_questions = await queries.count_questions(conn)
        print(f"Database verification: {total_quizzes} published quizzes, {total_questions} total questions stored.")

if __name__ == "__main__":
    asyncio.run(main())
