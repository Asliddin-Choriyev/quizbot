import csv
import random
from pathlib import Path

# Deterministic shuffle for each question
def make_options(correct, distractors, seed_val):
    options = [correct] + distractors
    rng = random.Random(seed_val)
    rng.shuffle(options)
    correct_idx = options.index(correct)
    letters = ["A", "B", "C", "D"]
    return options[0], options[1], options[2], options[3], letters[correct_idx]

# Question definitions: (num, question_text, correct_answer, [distractor1, distractor2, distractor3], explanation)
QUESTIONS_DATA = [
    (
        1,
        "Timus T-limfotsitlar sistemasiga xos.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat B-limfotsitlarga xos", "Faqat plazmatik hujayralarga xos"],
        "Timus T-limfotsitlar sistemasining markaziy a'zosi hisoblanadi."
    ),
    (
        2,
        "……..-immun javob bo'g'inlarining bir yoki bir necha joyda buzilishi hisobiga normal immun holatning o'zgarishini bildiradi.",
        "Immuntanqislik (IT)",
        ["Immunologik tolerantlik", "Allergik sensibilizatsiya", "Autoimmun reaksiya"],
        "Immuntanqislik — immun javob bo'g'inlarining buzilishi oqibatida normal immun holat o'zgarishi."
    ),
    (
        3,
        "Fagotsitoz vazifasini makrofaglar va polimorf o'zakli leykotsitlar bajaradi.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat eritrotsitlar bajaradi", "Faqat trombotsitlar bajaradi"],
        "Fagotsitozni makrofaglar hamda polimorfo'zakli neytrofillar (mikrofaglar) amalga oshiradi."
    ),
    (
        4,
        "Teleangiektaziya bilan kechadigan autosom-retsessiv immunologik yetishmovchilik sindromi qanday ataladi?",
        "Lui-Bar sindromi (ataksiya-teleangiektaziya)",
        ["Viskott-Oldrich sindromi", "Di-Jorj sindromi", "Bruton agammaglobulinemiyasi"],
        "Teleangiektaziya va ataksiya bilan kechuvchi autosom-retsessiv sindrom — Lui-Bar sindromidir."
    ),
    (
        5,
        "Ekzema va trombotsitopeniya bilan kuzatiladigan immunologik yetishmovchilik sindromi nomi:",
        "Viskott-Oldrich sindromi",
        ["Lui-Bar sindromi", "Di-Jorj sindromi", "Cheydak-Higasi sindromi"],
        "Ekzema, trombotsitopeniya va immuntanqislik — Viskott-Oldrich sindromiga xos triada."
    ),
    (
        6,
        "Lui-Bar va Viskott-Oldrich sindromlari qanday yuritiladi?",
        "Og'ir birlashgan immunologik yetishmovchilik (OBIYe)",
        ["Faqat gumoral immunitet tanqisligi", "Nomaxsus himoya yetishmovchiligi", "Faqat fagotsitoz buzilishi"],
        "Lui-Bar va Viskott-Oldrich sindromlari og'ir birlashgan immunologik yetishmovchilikka kiradi."
    ),
    (
        7,
        "O'zgargan yoki o'zgarmagan o'z to'qimalariga qarshi rivojlanadigan immunologik jarayon …. deb ataladi.",
        "Autoimmun reaksiya (autoimmun jarayon)",
        ["Immunologik tolerantlik", "Giposensibilizatsiya", "Anafilaktik reaksiya"],
        "O'z to'qimalariga qarshi rivojlanadigan immunologik jarayon — autoimmun reaksiya deb ataladi."
    ),
    (
        8,
        "Odam uchun B-limfotsitlarning markaziy a'zosi ……. hisoblanadi.",
        "Suyak ko'migi",
        ["Timus (ayrisimon bez)", "Taloq", "Limfa tugunlari"],
        "Odamda B-limfotsitlarning shakllanishi va markaziy a'zosi suyak ko'migidir."
    ),
    (
        9,
        "Mediatorlari yordamida B-limfotsitlar proliferatsiyasi va differensiyasini ta'minlaydi.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat eritropoezda ishtirok etadi", "Faqat komplement kaskadini to'xtatadi"],
        "T-xelperlar mediatorlari (sitokinlar) orqali B-hujayralar proliferatsiyasi va yetilishini ta'minlaydi."
    ),
    (
        10,
        "T-killer va T-effektor subpopulyatsiyalarini faollashtiradi.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat suyak o'sishini rag'batlantiradi", "Faqat qon ivishini ta'minlaydi"],
        "Sitokinlar (interleykinlar) T-killer va effektor limfotsitlar subpopulyatsiyasini faollashtiradi."
    ),
    (
        11,
        "Timus — …… .",
        "Immun tizimning markaziy a'zosi",
        ["Immun tizimning periferik a'zosi", "To'siq orti ekzokrin bezi", "Gidrolitik fermentlar saqlovchi a'zo"],
        "Timus (ayrisimon bez) immun tizimining asosiy markaziy a'zolaridan biridir."
    ),
    (
        12,
        "Lui-Bar sindromi — autosom-retsessiv immunologik yetishmovchilikdir.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "X-xromosoma dominant kasalligi", "Y-xromosoma bilan bog'langan kasallik"],
        "Lui-Bar sindromi autosom-retsessiv irsiylanuvchi birlamchi immuntanqislik holatidir."
    ),
    (
        13,
        "Diareya immun tizimiga bog'liq kasalliklarga kiradimi?",
        "Yo'q (Noto'g'ri)",
        ["Ha (To'g'ri)", "Barcha turlari birlamchi immun kasallik", "Faqat o'tkir diareya kiradi"],
        "Diareya alohida immun kasallik emas, hazm trakti kasalliklarining klinik alomatidir."
    ),
    (
        14,
        "Tabiiy immunostimulyatorlarga nimalar kiradi?",
        "Vaksinalar",
        ["Sintetik antibiotiklar", "Kimyoviy immunosupressorlar", "Kortikosteroid gormonlar"],
        "Tabiiy immunostimulyatorlarga vaksinalar, bakterial lizatlar va biologik preparatlar kiradi."
    ),
    (
        15,
        "Immun injeneriyasi nima?",
        "Immun a'zo va to'qimalarni (timus, ko'mik) ko'chirib o'tkazish",
        ["Qon plazmasini filtrlash usuli", "Antitanalarni fermentlar bilan parchalash", "Teri ostiga allergen yuborish usuli"],
        "Immun injeneriyasi — timus, ko'mik va homila jigari hujayralarini ko'chirib o'tkazishdir."
    ),
    (
        16,
        "Gemosorbtsiya, affin-sorbtsiya, immunosorbtsiya, splenosorbtsiya qaysi usulga xos?",
        "Sorbtsiya usullari (ekstrakorporal tozalash)",
        ["Fizik immunokorreksiya usullari", "Kimyoviy immunosupressiya usullari", "Genetik tahrirlash usullari"],
        "Ushbu usullar qon va limfani yot moddalardan tozalovchi ekstrakorporal sorbtsiyaga kiradi."
    ),
    (
        17,
        "Lazer, ultrabinafsha nurlari, elektromagnit ta'siri, igna-refleksoterapiya immunokorreksiyaning qaysi usuli?",
        "Fizik usul",
        ["Biologik usul", "Kimyoviy usul", "Sorbtsion usul"],
        "Lazer, UV-nurlar va elektromagnit nurlanishlar fizik immunokorreksiya hisoblanadi."
    ),
    (
        18,
        "Immunitet tanqisligi holatlarini qaysi fan o'rganadi?",
        "Immunologiya (klinik immunologiya)",
        ["Gematologiya", "Toksikologiya", "Farmakognoziya"],
        "Immuntanqislik holatlarini klinik immunologiya fani o'rganadi."
    ),
    (
        19,
        "Allergiya nima?",
        "Umumiy ta'sirlarga tana reaktivligining o'ta kuchayishi",
        ["Organizmdan begona antitanalarning chiqib ketishi", "Oq qon tanachalarining fiziologik kamayishi", "Normal mikrofloraning ko'payib ketishi"],
        "Allergiya — allergenlarga nisbatan organizm sezgirligi va reaktivligining o'ta kuchayishi."
    ),
    (
        20,
        "……-organizmda fagotsitoz vazifasini bajaradilar.",
        "Makrofaglar va polimorf o'zakli leykotsitlar",
        ["Eritrotsitlar va megakariotsitlar", "Trombotsitlar va endoteliotsitlar", "Plazmotsitlar va bazal hujayralar"],
        "Fagotsitoz vazifasini to'qima makrofaglari va mikrofaglar (neytrofillar) bajaradi."
    ),
    (
        21,
        "\"Papula\" so'zining ma'nosi:",
        "Tuguncha / qizarishli bo'rtiq",
        ["Yiringli pufakcha", "Chuqur yara (eroziya)", "Nekroz o'chog'i"],
        "Papula — terida paydo bo'ladigan bo'rtiq, qizarishli tugunchadir."
    ),
    (
        22,
        "Quyidagilardan qaysi biri sorbtsiya usullari?",
        "Affin-sorbtsiya",
        ["Ultrabinafsha nurlanish", "Elektroforez", "Rentgenoterapiya"],
        "Affin-sorbtsiya organizm suyuqliklarini biologik selektiv tozalash sorbtsiya usulidir."
    ),
    (
        23,
        "ACQUIRED IMMUNODEFICIENCY SYNDROME — bu?",
        "Orttirilgan immuntanqislik sindromi (OITS)",
        ["Tug'ma agammaglobulinemiya sindromi", "Og'ir birlashgan autoimmun sindrom", "O'tkir revmatik ensefalopatiya"],
        "AIDS inglizcha atamasi o'zbekchada OITS (orttirilgan immuntanqislik sindromi) deb yuritiladi."
    ),
    (
        24,
        "Immun tizimiga bog'liq kasalliklarga kiradi?",
        "OITS",
        ["Oshqozon yarasi", "Katarakta", "Ateroskleroz"],
        "OITS to'g'ridan-to'g'ri immun tizimning CD4+ T-hujayralarini zararlaydi."
    ),
    (
        25,
        "Sensibilizatsiya paydo qilib, allergik reaksiya keltiruvchi antigenlar nima deyiladi?",
        "Allergenlar",
        ["Haptenlar", "Antibiotiklar", "Gormonlar"],
        "Allergik sezgirlik (sensibilizatsiya) chaqiruvchi har qanday antigen allergen deb ataladi."
    ),
    (
        26,
        "OBIYe bu nima?",
        "Og'ir birlashgan immunologik yetishmovchilik",
        ["O'tkir bakterial infeksion yetishmovchilik", "Organik buyrak immun etishmovchiligi", "O'pka bronxial immun yetishmovchiligi"],
        "OBIYe — og'ir birlashgan immunologik yetishmovchilik (hujayraviy va gumoral buzilish)."
    ),
    (
        27,
        "Mantu sinamasi natijasi qancha vaqtdan so'ng baholanadi?",
        "24 va 48 soatdan so'ng (ba'zan 72 soatda)",
        ["10-15 daqiqadan so'ng", "2-4 soatdan so'ng", "7 kundan so'ng"],
        "Sekinlashgan o'ta sezgirlik reaksiyasi bo'lgan Mantu 24, 48 yoki 72 soatda baholanadi."
    ),
    (
        28,
        "Fizik usul bilan immunokorreksiyaga kiradi?",
        "Lazer va ultrabinafsha nurlari",
        ["Gemosorbtsiya va plazmaferez", "Immunoglobulinlar kiritish", "Levamizol va timalin berish"],
        "Lazer va ultrabinafsha nurlari fizik immunokorreksiya guruhiga kiradi."
    ),
    (
        29,
        "........ va ...... sindromini og'ir birlashgan immunologik yetishmovchilik deb ham yuritiladi.",
        "Lui-Bar va Viskott-Oldrich sindromlari",
        ["Di-Jorj va Daun sindromlari", "Bruton va Nezelof kasalliklari", "Rayno va Shegren sindromlari"],
        "Lui-Bar va Viskott-Oldrich sindromlari OBIYe guruhiga kiritiladi."
    ),
    (
        30,
        "Organizmda fagotsitoz vazifasini nimalar bajaradi?",
        "Makrofaglar (monotsitlar) va mikrofaglar",
        ["T-killerlar va plazmatik hujayralar", "Eritrotsitlar va trombotsitlar", "Fibroblastlar va osteotsitlar"],
        "Fagotsitozni mononuklear makrofaglar hamda polimorfo'zakli mikrofaglar (neytrofillar) bajaradi."
    ),
    (
        31,
        "Mantu sinamasida tuberkulin qanday usulda va qaysi sohaga yuboriladi?",
        "Bilakning ichki yuzasiga teri orasiga (intrakutan)",
        ["Yelka sohasiga teri ostiga", "Son sohasiga mushak orasiga", "Bilak yuzasiga vena ichiga"],
        "Mantu sinamasida tuberkulin bilak ichki yuzasiga qat'iy intrakutan (teri orasiga) yuboriladi."
    ),
    (
        32,
        "Allergik sinamalar ko'pincha qo'lning qaysi sohasiga qo'yiladi?",
        "Bilakning ichki yuzasiga",
        ["Kaftning orqa tomoniga", "Tirsak bo'g'imi orqasiga", "Yelkaning tashqi yuzasiga"],
        "Allergologik teri sinamalari bilakning oldingi-ichki yuzasiga qo'yiladi."
    ),
    (
        33,
        "Allergik sinamalar ko'pincha qaysi usulda qo'yiladi?",
        "Skarifikatsion usulda",
        ["Mushak ichiga ineksiya usulida", "Vena ichiga tomchilab quyishda", "Chuqur suyak ko'migi punksiyasida"],
        "Allergik sinamalar teri tirnash (skarifikatsion) yoki prik-test usulida o'tkaziladi."
    ),
    (
        34,
        "Qanday kasallikda ham hujayraviy, ham gumoral himoya izdan chiqadi?",
        "OITS",
        ["Gepatit A", "O'tkir gastrit", "Gripp"],
        "OITSda CD4+ hujayralar halokati oqibatida ham hujayraviy, ham gumoral immunitet falajlanadi."
    ),
    (
        35,
        "Antigenlarni tanib olish xususiyatiga ega 3 xil immun tizim hujayralari?",
        "T-limfotsitlar, B-limfotsitlar va antigen-prezentantlar",
        ["Eritrotsitlar, trombotsitlar va bazofillar", "Monotsitlar, eozinofillar va adipotsitlar", "Kardiomiotsitlar, miotsitlar va neyronlar"],
        "Spetsifik tanib olish T-, B-limfotsitlar va antigen taqdim qiluvchi hujayralarga xosdir."
    ),
    (
        36,
        "Tabiiy killerlarning xususiyati (vazifasi):",
        "O'sma hujayralarini tezda taniydi va o'ldiradi",
        ["Antitanalar ishlab chiqaradi", "Gistamin sintezlaydi", "Faqat qon ivishini ta'minlaydi"],
        "Tabiiy killerlar (NK) virusli va transformatsiyalangan o'sma hujayralarini tezda yo'q qiladi."
    ),
    (
        37,
        "K-limfotsitlarning xususiyati (vazifasi):",
        "Organizmdagi yot hujayralarni o'ldiradi",
        ["Zardob oqsillarini sintezlash", "Qon bosimini doimiy ushlab turish", "Fermentlarni faollashtirish"],
        "K-hujayralar antiteloga bog'liq sitotoksiklik orqali begona hujayralarni lizis qiladi."
    ),
    (
        38,
        "T-killerlarning xususiyati (vazifasi):",
        "O'sma va mutatsiyalangan hujayralarni topib yo'q qiladi",
        ["Eritrotsitlar shakllanishini nazorat qiladi", "Faqat glyukoza miqdorini boshqaradi", "Plazma oqsillarini filtrlaydi"],
        "T-sitotoksik limfotsitlar (CD8+) o'sma va yot antigen saqlovchi nishon hujayralarni yo'q qiladi."
    ),
    (
        39,
        "Aholini rejali emlash natijasida jamoa immuniteti hosil bo'ladi.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat individual himoya hosil bo'ladi", "Vaksinalar immunitet shakllantirmaydi"],
        "Keng qamrovli emlash populyatsiyada jamoaviy (kollektiv) himoya qatlamini yaratadi."
    ),
    (
        40,
        "Qanday zamburug'lar ko'pincha tug'ma va orttirilgan immuntanqislikda kasallik qo'zg'atadi?",
        "Shartli patogen zamburug'lar (masalan, Candida)",
        ["Obligat patogen spiroxetalar", "Kislotaga chidamli mikobakteriyalar", "Toksin hosil qiluvchi klostridiyalar"],
        "Immunitet pasayganda odatda shartli patogen opportunistik zamburug'lar infeksiya chaqiradi."
    ),
    (
        41,
        "B-tizimining tanlangan yetishmovchiligi, ……….. ning Bruton turida uchraydi.",
        "Tug'ma agammaglobulinemiyaning",
        ["Orttirilgan aplastik anemiyaning", "Surunkali granulomatoz kasalligining", "Leykotsitlar adgeziyasi yetishmovchiligining"],
        "Bruton kasalligi — B-limfotsitlar rivojlanmay qolishi bilan kechuvchi tug'ma agammaglobulinemiya."
    ),
    (
        42,
        "Agammaglobulinemiya jins bilan bog'langan bo'lib, faqat o'g'il bolalarda kuzatiladimi?",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat qiz bolalarda uchraydi", "Ikkala jinsda mutlaqo teng uchraydi"],
        "Bruton agammaglobulinemiyasi X-xromosomaga birikkan retsessiv gen orqali o'g'il bolalarda uchraydi."
    ),
    (
        43,
        "Timus aplaziyasi qalqonsimon bez oldi bezlari aplaziyasi bilan birga uchraydigan sindrom?",
        "Di-Jorj sindromi",
        ["Viskott-Oldrich sindromi", "Bruton kasalligi", "Lui-Bar sindromi"],
        "3- va 4-halqum cho'ntaklarining rivojlanish anomaliyasi — Di-Jorj sindromidir."
    ),
    (
        44,
        "Di-Jorj sindromida neonatal bosqichda bolalarda qanday holat kuzatiladi?",
        "Qaltirash (gipokalsiyemik tirishish)",
        ["Kuchli gipertermiya", "Anasarka va sariqlik", "Gemolitik kriz"],
        "Qalqonsimon bez oldi bezi yetishmovchiligida qonda Ca kamayib gipokalsiyemik tetaniya (qaltirash) bo'ladi."
    ),
    (
        45,
        "Nezelof kasalligi — timus bilan bog'liq ikkinchi sindromga kiruvchi kasallikmi?",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Bu faqat buyrak patologiyasi", "Bu faqat suyak ko'migi kasalligi"],
        "Nezelof sindromi timus gipoplaziyasi va T-hujayraviy immuntanqislik bilan xarakterlanadi."
    ),
    (
        46,
        "Yuqumli mononukleoz va Berkit limfomasini qo'zg'atadigan ….. asosan B-limfotsitlarni zararlaydi.",
        "Epshteyn-Barr virusi",
        ["Sitomegalovirus", "Oddiy gerpes virusi", "Qizamiq virusi"],
        "Epshteyn-Barr virusi (EBV) yuqumli mononukleoz va Berkit limfomasini keltirib chiqaradi."
    ),
    (
        47,
        "Epshteyn-Barr virusi asosan …. zararlaydi.",
        "B-limfotsitlarni",
        ["T-killerlarni", "Eritrotsitlarni", "Trombotsitlarni"],
        "EBV CD21 retseptorlari vositasida aynan B-limfotsitlarni zararlaydi."
    ),
    (
        48,
        "A.D. Ado va A. Polker allergenlarni kelib chiqishiga ko'ra qanday guruhlarga bo'lgan?",
        "Infeksion va noinfeksion",
        ["Tabiiy va gormonal", "Organik va noorganik", "Kuchli va kuchsiz"],
        "Ado va Polker tasnifi bo'yicha barcha allergenlar infeksion va noinfeksion guruhlarga bo'linadi."
    ),
    (
        49,
        "Infeksion guruh allergenlariga hamma mikroorganizmlarning allergenlari kiradi.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat bakteriyalar kiradi", "Faqat gulchanglar kiradi"],
        "Bakteriyalar, viruslar, zamburug'lar va parazitlarning barcha allergenlari infeksion guruhni tashkil etadi."
    ),
    (
        50,
        "Noinfeksion guruh allergenlariga nimalar kiradi?",
        "Maishiy, epidermal, chang, oziq-ovqat va dori allergenlari",
        ["Patogen batsillalar va vibrionlar", "Faqat zamburug' sporalari", "Tirik vaksina shtammlari"],
        "Noinfeksion allergenlar maishiy, o'simlik changi, epidermal, dori va oziq-ovqat turlariga bo'linadi."
    ),
    (
        51,
        "Allergik reaksiyalar tasnifini kimlar tuzishgan?",
        "P. Jell va R. Kumbs",
        ["I.I. Mechnikov va P. Erlix", "L. Paster va R. Kox", "E. Jenner va A. Fleming"],
        "Allergik reaksiyalarning klassik to'rt turli tasnifini 1963-yilda Jell va Kumbs ishlab chiqqan."
    ),
    (
        52,
        "P. Jell va R. Kumbs allergik reaksiyalarni qanday turlarga ajratgan?",
        "I, II, III va IV turlarga",
        ["Birlamchi va ikkilamchi turlarga", "Tizimli va mahalliy turlarga", "Qon va limfa turlariga"],
        "Jell va Kumbs allergik o'ta sezgirlik reaksiyalarini I dan IV gacha tiplarga ajratgan."
    ),
    (
        53,
        "Allergik reaksiyalarning I turi?",
        "Anafilaktik (reaginli, IgE-bog'liq) tip",
        ["Sitotoksik (IgG va IgM) tip", "Immunokompleks (Artyus) tipi", "Sekinlashgan hujayraviy tip"],
        "I tip — anafilaktik (reaginli, atopik) tip bo'lib, IgE antitanalari orqali yuzaga chiqadi."
    ),
    (
        54,
        "Allergik reaksiyalarning II turi?",
        "Sitotoksik (sitolitik, IgG va IgM) tip",
        ["Reaginli darhol tip", "Immunokompleksli tip", "Granulomatoz tip"],
        "II tip — sitotoksik bo'lib, antitanalar hujayra membranasi bilan birikib uni parchalaydi."
    ),
    (
        55,
        "Allergik reaksiyalarning III turi?",
        "Immunokompleks (Artyus fenomeni) tipi",
        ["Reaginli anafilaktik tip", "Sekin kechuvchi tuberkulin tipi", "Faqat retseptor stimulyatsiyasi"],
        "III tip — immunokompleksli o'ta sezgirlik (qonda aylanuvchi immun komplekslar) hisoblanadi."
    ),
    (
        56,
        "III turning oldingi turdan farqi — antigenlar hujayra bilan birikmay qonda aylanib yurishi.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Antigenlar faqat suyak to'qimasida to'planadi", "Mexanizmi II tip bilan mutlaqo bir xil"],
        "III tipda antitanalar hujayraga birikmagan, qonda eruvchan immun kompleks holida aylanib yuradi."
    ),
    (
        57,
        "\"Anafilaksiya\" terminining ma'nosi:",
        "Himoyasizlik (teskari himoya)",
        ["O'ta kuchli immunitet", "Tezkor shifo topish", "Tug'ma immuntanqislik"],
        "Anafilaksiya lotin/yunoncha ana (teskari) va phylaxis (himoya), ya'ni himoyasizlikni anglatadi."
    ),
    (
        58,
        "Qayta yot allergen kiritilganda rivojlanadigan o'ta sezgirlik holati?",
        "Anafilaksiya (allergik reaksiya)",
        ["Immunologik tolerantlik", "Aseptik koma", "Fiziologik regeneratsiya"],
        "Sensibilizatsiyalangan organizmga qayta allergen kiritilganda anafilaktik reaksiya yuzaga keladi."
    ),
    (
        59,
        "Sh. Rishe va P. Port'elar \"anafilaksiya\" terminini tibbiyotga kiritishgan.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Terminni R. Kox kiritgan", "Terminni A. Bordet kiritgan"],
        "Sharl Rishe va Pol Portye 1902-yilda meduzalar toksini ustidagi tajribada terminni kiritgan."
    ),
    (
        60,
        "Anafilaksiyaning qanday turlari tafovut qilinadi?",
        "Umumiy (anafilaktik shok) va mahalliy turlari",
        ["O'tkir va surunkali yuqumli turlari", "Faqat oshqozon va ichak turlari", "Birlamchi va ikkilamchi bakterial turlari"],
        "Anafilaksiya umumiy (shok) va mahalliy (teri anafilaksiyasi, Artyus fenomeni) turlarga bo'linadi."
    ),
    (
        61,
        "Ikkinchi marta antigen kiritilganda yuzaga keladigan patologik reaksiya?",
        "Allergiya",
        ["Eritropoez", "Apoptoz", "Autoliz"],
        "Sensibilizatsiyadan so'ng ikkinchi bor antigen tushganda paydo bo'ladigan jarayon — allergiyadir."
    ),
    (
        62,
        "\"Allergiya\" terminining ma'nosi?",
        "Boshqacha ta'sirlanish (allos — boshqa, ergon — ta'sir)",
        ["Tezkor shifo topish", "Hujayraning bo'linishi", "Qon ivishining buzilishi"],
        "Allergiya grekcha allos (boshqa) va ergon (ta'sir, ish), ya'ni boshqacha ta'sirlanish demakdir."
    ),
    (
        63,
        "\"Allergiya\" terminini tibbiyotga kiritgan olim:",
        "Klemens fon Pirke (1906-yilda)",
        ["Ilya Mechnikov", "Robert Kox", "Lui Paster"],
        "Allergiya atamasini 1906-yilda avstriyalik pediatr Klemens fon Pirke taklif qilgan."
    ),
    (
        64,
        "Taloq qonni filtrlaydi.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat limfani filtrlaydi", "Faqat o't suyuqligini tozalaydi"],
        "Taloq qon aylanish tizimiga ulangan bo'lib, qonni eski hujayralar va mikroblardan tozalaydi."
    ),
    (
        65,
        "Limfatik tugunlar qaysi a'zolarni filtrlaydi?",
        "To'qima va a'zolardan oqib keluvchi limfa suyuqligini",
        ["Faqat orqa miyadagi likvorni", "Faqat oshqozon shilliq qavatini", "Arterial qon oqimini"],
        "Limfa tugunlari to'qimalardan keluvchi limfa suyuqligini begona antigenlardan tozalovchi filtrdir."
    ),
    (
        66,
        "Limfotsitlar populyatsiyasi qanday 3 sinfga bo'linadi?",
        "T-limfotsitlar, B-limfotsitlar va O-hujayralar (NK)",
        ["Monotsitlar, eozinofillar va bazofillar", "Neytrofillar, eritrotsitlar va trombotsitlar", "Miya, jigar va o'pka limfotsitlari"],
        "Limfotsitlar T-, B- va nolinchi (NK va K tabiiy killer) hujayralarga ajratiladi."
    ),
    (
        67,
        "Immun sistemaning asosiy vazifasi?",
        "Organizm ichki strukturasining genetik doimiyligini saqlash",
        ["Moddalar almashinuvini to'xtatish", "Gormonlarni parchalash", "Tana haroratini doim 40 darajada ushlab turish"],
        "Immun tizimning bosh vazifasi ichki muhit va to'qimalarning genetik xavfsizligini ta'minlashdir."
    ),
    (
        68,
        "Makrofaglarni yana qanday atash mumkin?",
        "Antigenni namoyish etuvchi (prezentant) hujayralar",
        ["Antitelo ishlab chiqaruvchi plazmotsitlar", "Qon ivituvchi trombotsitlar", "Nerv impulsi o'tkazuvchi neyronlar"],
        "Makrofaglar yot antigenni o'zlashtirib, T-hujayralarga namoyish etuvchi (prezentatsiyalovchi) hujayradir."
    ),
    (
        69,
        "Antigen prezentant hujayralar bu — ….",
        "Makrofaglar (va dendrit hujayralar)",
        ["Eritrotsitlar", "Trombotsitlar", "Kardiomiotsitlar"],
        "Antigenni taqdim qiluvchi asosiy hujayralar makrofaglar va dendrit hujayralardir."
    ),
    (
        70,
        "Yallig'lanish jarayonlarini boshqaruvchisi — sitokinlardir.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Sitokinlar faqat suyak o'stiradi", "Boshqaruv faqat eritrotsitlarda kechadi"],
        "Sitokinlar immun yallig'lanish reaksiyalarini faollashtiruvchi va muvofiqlashtiruvchi molekulalardir."
    ),
    (
        71,
        "Immun yallig'lanish reaksiyalarini ko'plab ……… boshqaradi.",
        "Sitokinlar (interleykinlar, interferonlar, TNF)",
        ["Hazm fermentlari (pepsin, tripsin)", "Nuklein kislotalar", "Faqat agglyutininlar"],
        "Yallig'lanish reaksiyalarini sitokinlar — interleykinlar, interferon va o'sma nekrozi omillari boshqaradi."
    ),
    (
        72,
        "Sitokinlar ishlab chiqarilishiga qarab qanday turlari bor?",
        "Interleykinlar, limfokinlar, monokinlar",
        ["Globulinlar va albuminlar", "Fibrinogen va protrombin", "Insulin va glyukagon"],
        "Sitokinlar hujayra turiga ko'ra monokinlar, limfokinlar va interleykinlarga bo'linadi."
    ),
    (
        73,
        "Biologik aktivligiga qarab sitokinlar qanday 3 guruhga bo'linadi?",
        "Yallig'lanish oldi, yallig'lanishga qarshi va gemopoetik",
        ["Kislotali, neytral va ishqoriy sitokinlar", "Virusli, bakterial va zamburug'li sitokinlar", "Yengil, o'rta va og'ir sitokinlar"],
        "Sitokinlar proinflamator, antiinflamator va gemopoetik (o'sish omillari) guruhlarga bo'linadi."
    ),
    (
        74,
        "Asosiy sitokinlar antigenspetsifik \"hujayra\" tipidagi immun javobni boshqaruvchisi.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Ular faqat nerv tolalarini o'rab turadi", "Faqat qon bosimini o'zgartiradi"],
        "Sitokinlar antigenspetsifik T-hujayraviy va gumoral immun javob zanjirlarini boshqaradi."
    ),
    (
        75,
        "……. a'zolarga taloq, limfa tugunlari, murtak bezi, ko'richak, qon, ichak va bronxlardagi limfatik follikulalar kiradi.",
        "Periferik (sirtqi) limfoid a'zolarga",
        ["Markaziy immun a'zolariga", "To'siq orti ekzokrin bezlariga", "Gemopoezning birlamchi a'zolariga"],
        "Taloq, limfa tugunlari va shilliq qavat limfoid to'qimalari sirtqi (periferik) immun a'zolaridir."
    ),
    (
        76,
        "Timus ikki pallachadan iborat, qanday qavatlari bor?",
        "Po'stloq (kortikal) va miya (medullyar) qavatlari",
        ["Serioz, shilliq va mushak qavatlari", "Bazal va apikal qavatlari", "Faqat tashqi kapsula va trabekulalar"],
        "Timus parenximasi kortikal (po'stloq) va medullyar (miya/mag'iz) qavatlaridan iborat."
    ),
    (
        77,
        "T-limfotsitlar qayerda BO'LMAYDI?",
        "Ko'mikda (suyak ko'migida yetilmaydi)",
        ["Limfa tugunlarida", "Taloqda", "Qon tomirlarida"],
        "T-limfotsitlar suyak ko'migida differensiallanmaydi, ular yetilish uchun timusga o'tadi."
    ),
    (
        78,
        "……. — immun tizimning markaziy a'zosi.",
        "Suyak ko'migi (va timus)",
        ["Taloq va limfa tuguni", "Murtak bezi va ko'richak", "Peyer pilakchalari"],
        "Suyak ko'migi (va timus) immun tizimining markaziy a'zolari hisoblanadi."
    ),
    (
        79,
        "T- va B-zonalarda nima yetiladi?",
        "T-limfotsitlar va B-limfotsitlar",
        ["Eritrotsitlar va bazofillar", "Monotsitlar va trombotsitlar", "Osteotsitlar va xondrotsitlar"],
        "Periferik limfoid a'zolarning maxsus zonalarida mos ravishda T- va B-limfotsitlar to'planadi."
    ),
    (
        80,
        "Taloqda ……… tafovut qilinadi.",
        "Oq va qizil pulpalar",
        ["Sariq va qora moddalar", "Kortikal va miya naychalari", "Glomerulyar va tubulyar qismlar"],
        "Taloq to'qimasi limfoid oq pulpa va venoz qon bilan to'lgan qizil pulpadan iborat."
    ),
    (
        81,
        "\"To'siq orti a'zolar\"ga qaysi a'zolar kiradi? (4 ta)",
        "Bosh/orqa miya, ko'z gavhari, urug'don, qalqonsimon bez",
        ["Jigar, buyrak, yurak, o'pka", "Oshqozon, ingichka ichak, taloq, o't pufagi", "Suyak, tog'ay, teri, tishlar"],
        "Gematoparenximal to'siqlar bilan ajralgan a'zolar: asab tizimi, ko'z gavhari, urug'don va qalqonsimon bez."
    ),
    (
        82,
        "Organizmning antigenga qarshi immun reaksiya rivojlantira olmasligi?",
        "Immunologik tolerantlik",
        ["Anafilaktik shok", "Antitanalar giperproduksiyasi", "Allergik sensibilizatsiya"],
        "Immun tizimning muayyan antigenga nisbatan tolerantligi — javob reaksiyasi yo'qligidir."
    ),
    (
        83,
        "Patogen mikroorganizmlardan himoya qiluvchi xususiyat?",
        "Immunitet",
        ["Sensibilizatsiya", "Atopiya", "Disfagiya"],
        "Organizmning mikrob, virus va yot moddalardan himoyalanish xususiyati immunitet deb ataladi."
    ),
    (
        84,
        "Nomaxsus himoya omillariga nimalar kiradi?",
        "Teri, shilliq qavatlar, mikroflora, komplement, lizotsim",
        ["Faqat maxsus IgG va IgM antitanalar", "Faqat antigenga mos T-killerlar", "Dori preparatlari va sun'iy zardoblar"],
        "Nomaxsus himoyani mexanik to'siqlar, lizotsim, komplement, interferon va NK hujayralar ta'minlaydi."
    ),
    (
        85,
        "O'z to'qimalariga qarshi rivojlanadigan immunologik jarayon?",
        "Autoimmun reaksiya",
        ["Izotransplantatsiya", "Gipoallergiya", "Immunodepressiya"],
        "Immun tizimining o'z hujayra va to'qimalariga qarshi patologik javobi — autoimmun reaksiyadir."
    ),
    (
        86,
        "Autoimmun kasalliklarning turlari (joyiga qarab)?",
        "A'zo-maxsus, tizimli (a'zoga nomaxsus) va oraliq",
        ["Bosh miya va orqa miya turlari", "Teri va shilliq turlari", "Faqat suyak va bo'g'im turlari"],
        "Autoimmun jarayonlar a'zo-maxsus va tizimli (tizimli qizil yugurik kabi) turlarga bo'linadi."
    ),
    (
        87,
        "A'zo-maxsus autoimmun kasalliklarga misol?",
        "I tur qandli diabet, autoimmun tireoidit, miasteniya",
        ["Tizimli qizil yugurik va revmatoid artrit", "Gripp va pnevmoniya", "Bruton kasalligi va OITS"],
        "A'zo-maxsus kasalliklar aniq bir a'zoning autoantigenlariga qaratilgan bo'ladi."
    ),
    (
        88,
        "Plasenta orqali o'ta oladigan immunoglobulin?",
        "IgG",
        ["IgM", "IgA", "IgE"],
        "Faqat IgG molekulalari yo'ldosh to'sig'idan o'tib homilani tug'ruqqacha va undan keyin himoya qiladi."
    ),
    (
        89,
        "Proteaza fermentiga chidamli immunoglobulin?",
        "IgA (sekretor IgA)",
        ["IgE", "IgD", "IgM"],
        "Sekretor komponentli IgA shilliq qavatlardagi hazm fermentlari ta'siriga juda chidamli."
    ),
    (
        90,
        "Antigen ta'sirida birinchi bo'lib qaysi immunoglobulin hosil bo'ladi?",
        "IgM",
        ["IgG", "IgE", "IgD"],
        "Birlamchi immun javob yuzaga kelganda dastlab yirik IgM molekulalari sintezlanadi."
    ),
    (
        91,
        "B-limfotsitlar retseptori qaysi immunoglobulin?",
        "IgD (va monomer IgM)",
        ["Sekretor IgA", "Pentamer IgM", "IgE reagini"],
        "Yetilgan B-limfotsitlar membranasida IgD antitanasi asosiy antigen retseptori hisoblanadi."
    ),
    (
        92,
        "Timus po'stloq qavatining 90% i limfotsitlardan iborat.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat 10% ini tashkil qiladi", "Limfotsitlar po'stloqda bo'lmaydi"],
        "Timus po'stloq (kortikal) qavatining 90% qismi timotsitlar (limfotsitlar) bilan band."
    ),
    (
        93,
        "Timus po'stloq qavatining 10% i epitelial hujayralar va makrofaglardan iborat.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Unda makrofaglar mutlaqo uchramaydi", "Po'stloqning 100% i neytrofillardan iborat"],
        "Qolgan 10% hujayralar esa timusning epitelial stromasi va makrofaglaridan iborat."
    ),
    (
        94,
        "Qanday omillar ta'sirida interferonlar ishlab chiqariladi?",
        "Virus, bakteriya, endotoksin va nuklein kislotalar ta'sirida",
        ["Faqat sovuq harorat ta'sirida", "Faqat qon bosimi oshganda", "Faqat toza suv ichganda"],
        "Interferon ishlab chiqarilishini viruslar, bakteriyalar, endotoksinlar va yot nuklein kislotalar chaqiradi."
    ),
    (
        95,
        "IgG yo'ldosh orqali o'tish xususiyatiga ega.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat IgM o'tadi", "Hech qanday antitelo o'ta olmaydi"],
        "IgG onadan homilaga yo'ldosh orqali o'tuvchi yagona immunoglobulin sinfidir."
    ),
    (
        96,
        "IgM — pentamer, 10 ta antigen bog'lovchi markazi bor.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "IgM monomer bo'lib 2 ta markazi bor", "IgM 4 ta markazli dimerdir"],
        "IgM 5 ta monomerik birlikdan iborat pentamer bo'lib, 10 ta Fab faol markazga ega."
    ),
    (
        97,
        "IgE tez kechuvchi allergik reaksiyalarda ishtirok etadi.",
        "Ha (To'g'ri)",
        ["Yo'q (Noto'g'ri)", "Faqat sekinlashgan o'ta sezgirlikda qatnashadi", "Faqat kalsiy almashinuvida qatnashadi"],
        "IgE antitanalari semiz hujayralarga fiksatsiyalangan holda I tip darhol o'ta sezgirlikda qatnashadi."
    ),
    (
        98,
        "Immunoglobulinlarning organizmdagi ahamiyati:",
        "Gumoral immun javobni ta'minlash",
        ["Hujayra ichi ATF sintezini oshirish", "Qon tomir devorini mustahkamlash", "Faqat yog'larni eritish"],
        "Immunoglobulinlar (antitanalar) qon va to'qima suyuqliklarida gumoral himoyani amalga oshiradi."
    ),
    (
        99,
        "Xalqaro klassifikatsiya bo'yicha immunoglobulinlar nechta va qanday sinflarga bo'lingan?",
        "5 ta sinfga: IgG, IgM, IgA, IgE, IgD",
        ["3 ta sinfga: IgA, IgG, IgM", "2 ta sinfga: yengil va og'ir zanjirli", "7 ta sinfga: IgA dan IgH gacha"],
        "Xalqaro tasnifga binoan og'ir zanjir xususiyatiga ko'ra 5 ta sinf ajratiladi: G, M, A, E, D."
    ),
    (
        100,
        "Lotincha \"serum\" atamasi nimani anglatadi?",
        "Qon zardobi (zardob)",
        ["Qon shaklli elementlari", "Limfa tomirlari devori", "To'qima suyuqligi"],
        "Lotincha \"serum\" so'zi qon zardobini anglatadi (immun zardoblar tibbiyotda keng qo'llaniladi)."
    ),
]

def build_csv():
    out_path = Path("data/mikrobiologiya_collections/mikrobiologiya_mavzu_12.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for num, q, correct, distractors, explanation in QUESTIONS_DATA:
        # Check lengths
        assert len(q) <= 295, f"Question {num} too long: {len(q)}"
        assert len(correct) <= 95, f"Correct {num} too long: {len(correct)}"
        for d in distractors:
            assert len(d) <= 95, f"Distractor in {num} too long: {len(d)}"
        assert len(explanation) <= 200, f"Explanation {num} too long: {len(explanation)}"
        
        opt_a, opt_b, opt_c, opt_d, correct_letter = make_options(correct, distractors, seed_val=1200 + num)
        full_explanation = f"To'g'ri javob: {correct}. {explanation}"
        if len(full_explanation) > 195:
            full_explanation = full_explanation[:192] + "..."
            
        row = {
            "question": q,
            "option_a": opt_a,
            "option_b": opt_b,
            "option_c": opt_c,
            "option_d": opt_d,
            "correct_answer": correct_letter,
            "explanation": full_explanation,
            "topic": "Mikrobiologiya: 12-mavzu",
            "difficulty": "Medium",
            "timer": 25,
            "image": ""
        }
        rows.append(row)
        
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "question", "option_a", "option_b", "option_c", "option_d",
            "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Successfully generated {len(rows)} questions in {out_path}")

if __name__ == "__main__":
    build_csv()
