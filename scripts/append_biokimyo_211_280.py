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

NEW_QUESTIONS_DATA = [
    (
        211,
        "Miyada glyukozaning barqaror oqimini ta'minlovchi GLYUT (tashuvchi) qaysi?",
        "GLYUT-1",
        ["GLYUT-2", "GLYUT-3", "GLYUT-4"],
        "Miyada glyukozaning barqaror oqimini GLYUT-1 tashuvchisi ta'minlaydi."
    ),
    (
        212,
        "Ushbu tashuvchi ishtirokida glyukoza jigar va enterotsitlardan qonga o'tadi:",
        "GLYUT-2",
        ["GLYUT-1", "GLYUT-4", "GLYUT-5"],
        "GLYUT-2 jigar va ichak enterotsitlarida glyukoza transportini amalga oshiradi."
    ),
    (
        213,
        "Yog' to'qimasi va mushak hujayralarida glyukozaning asosiy insulin-bog'liq tashuvchisi hisoblanadi:",
        "GLYUT-4",
        ["GLYUT-1", "GLYUT-2", "GLYUT-3"],
        "GLYUT-4 yog' va mushak to'qimalarida insulin ta'sirida faollashuvchi tashuvchidir."
    ),
    (
        215,
        "Glikoliz jarayonida qanday asosiy mahsulotlar hosil bo'ladi?",
        "ATF va piruvat",
        ["Laktat va glyukoza", "Atsetil-KoA va CO2", "Oksaloatsetat va malat"],
        "Glikoliz natijasida 1 molekula glyukozadan 2 molekula piruvat va ATF hosil bo'ladi."
    ),
    (
        216,
        "Anaerob glikolizning sof energetik samaradorligi qanday?",
        "2 mol ATF",
        ["4 mol ATF", "8 mol ATF", "38 mol ATF"],
        "Anaerob sharoitda 1 mol glyukoza parchalanganda sof 2 mol ATF hosil bo'ladi."
    ),
    (
        217,
        "Aerob glikolizning (to'liq oksidlanish) energetik samaradorligi qanday?",
        "38 mol ATF",
        ["2 mol ATF", "12 mol ATF", "24 mol ATF"],
        "Glyukozaning aerob to'liq oksidlanishida 36-38 mol ATF sintezlanadi."
    ),
    (
        218,
        "Kori sikli nima?",
        "Mushaklardagi glikoliz va jigardagi glyukoneogenez o'rtasidagi bog'liqlik",
        ["O't suyuqligining ichak va jigar orasidagi sirkulyatsiyasi", "Mitoxondriyada piruvatning to'liq oksidlanish sikli", "Aminokislotalardan mochevina hosil bo'lish sikli"],
        "Kori sikli — mushakda hosil bo'lgan laktatning jigarda qayta glyukozaga aylanish siklidir."
    ),
    (
        219,
        "Krebs sikli (trikarbon kislotalar sikli) nima?",
        "Mitoxondriya matritsasida boruvchi universal ATF sintezi jarayoni",
        ["Sitoplazmada glikogen parchalanishi jarayoni", "Endoplazmatik to'rda oqsillar biosintezi", "Ribosomada kechuvchi peptid zanjiri sintezi"],
        "Krebs sikli — mitoxondriyada atsetil-KoA ning CO2 gacha oksidlanishi va ATF/NADH hosil bo'lishi."
    ),
    (
        220,
        "Enterogepatik (interogepatik) sikl nima?",
        "Jigar va ingichka ichak o'rtasida o't kislotalarining aylanishi",
        ["Mushak va jigar o'rtasida laktat va glyukoza aylanishi", "Qon va buyrak o'rtasida mochevina filtrlash sikli", "Oshqozon va qizilo'ngach o'rtasida shira harakati"],
        "Enterogepatik sirkulyatsiya — o't kislotalarining ichakdan qayta so'rilib jigarga qaytishi."
    ),
    (
        221,
        "Fruktokinaza fermentining yetishmovchiligi qanday holatga sabab bo'ladi?",
        "Fruktozemiya va fruktozuriya",
        ["Galaktozemiya va katarakta", "Gipolaktaziya va diareya", "Fenilketonuriya"],
        "Fruktokinaza yetishmaganda fruktoza qonda to'planib (fruktozemiya) siydik bilan ajraladi."
    ),
    (
        222,
        "Galaktozadan galaktoza-1-fosfat hosil bo'lishi qanday moddalar ishtirokida kechadi?",
        "Galaktokinaza fermenti va ATF ishtirokida",
        ["Geksokinaza fermenti va ADF ishtirokida", "Fosfofruktokinaza va NAD+", "Laktaza fermenti va fosfat"],
        "Galaktozaning fosforillanishini galaktokinaza fermenti ATF sarflab amalga oshiradi."
    ),
    (
        223,
        "Galaktozemiya kasalligining asosiy belgilarini ko'rsating:",
        "Miya zararlanishi, katarakta, sariqlik, jigar va buyrak kattalashishi",
        ["Teri qizarishi, qon bosimi oshishi va taxikardiya", "Qonda qand miqdorining keskin ko'tarilishi va poliuriya", "Suyaklarning tez sinishi va mushak atrofiyasi"],
        "Galaktozemiya — galaktoza-1-fosfat to'planishi tufayli katarakta, jigar va MNT zararlanishi bilan kechadi."
    ),
    (
        224,
        "Gipolaktaziya qanday kasallik?",
        "Laktozani hazm qila olmaslik (sut qandi o'zlashtirilmasligi)",
        ["Saxaroza parchalanishining ortib ketishi", "Glyukozaning buyrak orqali chiqib ketishi", "Maltozaning to'qimalarda to'planishi"],
        "Gipolaktaziya — laktaza yetishmovchiligi sababli sut qandini o'zlashtira olmaslik."
    ),
    (
        225,
        "Mushaklar qondan qaysi aminokislotalarni faol qabul qiladi?",
        "Serin, sistin, glutamin",
        ["Faqat fenilalanin va tirozin", "Faqat lizin va arginin", "Faqat prolin va gidroksiprolin"],
        "Mushak to'qimasi metabolizm uchun qondan serin, sistin va glutaminni qabul qiladi."
    ),
    (
        226,
        "Mushaklar qonga asosan qaysi aminokislotalarni ajratib chiqaradi?",
        "Alanin va glutamin",
        ["Valin va leysin", "Triptofan va metionin", "Glitsin va gistidin"],
        "Mushaklarda ammiak zararsizlantirilib, qonga alanin va glutamin ko'rinishida chiqariladi."
    ),
    (
        227,
        "Ichaklar qondan asosan qaysi aminokislotani energiya manbai sifatida qabul qiladi?",
        "Glutamin",
        ["Alanin", "Leysin", "Metionin"],
        "Enterotsitlar uchun asosiy energiya substrati qondan olinadigan glutamindir."
    ),
    (
        228,
        "Jigar asosan qondan qaysi aminokislotani glyukoneogenez uchun qabul qiladi?",
        "Alanin",
        ["Izoleysin", "Triptofan", "Gidroksiprolin"],
        "Glyukoza-alanin sikli orqali mushaklardan kelgan alanin jigarda qabul qilinadi."
    ),
    (
        229,
        "Buyraklar qondan qaysi aminokislotalarni ko'proq qabul qiladi?",
        "Glutamin, prolin, glitsin",
        ["Faqat fenilalanin va tirozin", "Faqat triptofan va leysin", "Faqat metionin va sistein"],
        "Buyraklar ammoniogenez va kislota-ishqor muvozanati uchun glutamin, prolin va glitsinni qabul qiladi."
    ),
    (
        230,
        "Buyraklar asosan qaysi aminokislotalarni qonga ajratadi?",
        "Serin, ozroq alanin",
        ["Glutamin va leysin", "Valin va izoleysin", "Triptofan va tirozin"],
        "Buyrak to'qimasi metabolizm mahsuloti sifatida qonga serin va alaninni ajratadi."
    ),
    (
        231,
        "Miya to'qimasi qon zardobidan qaysi tarmoqlangan aminokislotalarni faol so'rib oladi?",
        "Valin, leysin, izoleysin",
        ["Glitsin, alanin, serin", "Aspartat, glutamat, prolin", "Lizin, arginin, gistidin"],
        "Miya to'qimasi tarmoqlangan zanjirli aminokislotalar (valin, leysin, izoleysin) ni intensiv o'zlashtiradi."
    ),
    (
        232,
        "Aminokislotalarning dezaminlanish reaksiyasi natijasida qanday mahsulotlar hosil bo'ladi?",
        "Ketokislotalar, gidrokislotalar va NH3 (ammiak)",
        ["Faqat mochevina va siydik kislotasi", "Faqat glyukoza va glikogen", "Faqat yog' kislotalari va xolesterin"],
        "Dezaminlanishda aminoguruh ammiak (NH3) holida ajralib, ketokislota qoldig'i qoladi."
    ),
    (
        233,
        "Transaminlanish reaksiyasi natijasida qanday aminokislotalar sintezlanadi?",
        "Almashinadigan aminokislotalar",
        ["Almashinmaydigan aminokislotalar", "Faqat aromatik aminokislotalar", "Faqat geterosiklik aminokislotalar"],
        "Transaminlanish orqali organizmda almashinadigan aminokislotalar yangidan sintezlanadi."
    ),
    (
        234,
        "To'qimalarda aminokislotalar katabolizmi qanday o'rtacha tezlikda boradi?",
        "Sutkasiga taxminan 100 g",
        ["Sutkasiga 10-20 g", "Sutkasiga 500 g", "Sutkasiga 1-2 kg"],
        "Katta yoshli odamda sutkasiga o'rtacha 100 g aminokislotalar katabolizmga uchraydi."
    ),
    (
        235,
        "To'qimalarda aminokislotalar katabolizmining qaysi bosqichida eng ko'p ammiak ajraladi?",
        "Dezaminlanish bosqichida",
        ["Transaminlanish bosqichida", "Dekarboksillanish bosqichida", "Peptid bog'i hosil bo'lishida"],
        "Ammiakning to'g'ridan-to'g'ri ajralishi dezaminlanish reaksiyalarida kechadi."
    ),
    (
        236,
        "Ammiak organizmda qanday reaksiyalar natijasida hosil bo'ladi?",
        "Aminokislotalar, biogen aminlar va purin/pirimidinlar dezaminlanishida",
        ["Glikogen va kraxmal gidrolizida", "Yog'larning beta-oksidlanishida", "Xolesterin biosintezida"],
        "Ammiak azot saqlovchi birikmalar: aminokislotalar, nukleotidlar va aminlar dezaminlanishidan hosil bo'ladi."
    ),
    (
        237,
        "Miyada ammiakning qanday miqdori tutqanoqli qaltirashni chaqiradi?",
        "0,6 mmol/l",
        ["0,05 mmol/l", "2,5 mmol/l", "10,0 mmol/l"],
        "Qonda va miyada ammiak 0,6 mmol/l ga yetganda neyrotoksiklik va tutqanoqlar kelib chiqadi."
    ),
    (
        238,
        "Giperammonemiya (ammiakdan zaharlanish) simptomlarini to'g'ri ko'rsating:",
        "Nutq chalkashishi, qusish, tutqanoqli qaltirash, hushdan ketish",
        ["Qonda qand miqdori pasayishi va terlash", "Suyaklarda kuchli og'riq va deformatsiya", "Teri sarg'ayishi va qichishish"],
        "Giperammonemiyada neyrotoksiklik rivojlanib, nutq buzilishi, qusish, tremor va koma kuzatiladi."
    ),
    (
        239,
        "Ammiak mitoxondriyada alfa-ketoglutarat va NADH bilan birikkanda qanday mahsulotlar hosil bo'ladi?",
        "Glutamat va NAD+",
        ["Aspartat va FAD", "Alanin va piruvat", "Glutamin va ATF"],
        "Glutamatdegidrogenaza qaytar reaksiyada alfa-ketoglutarat + NH3 + NADH dan glutamat va NAD+ hosil qiladi."
    ),
    (
        240,
        "Qonda ammiak konsentratsiyasining ortishi pH ni ishqoriy tomonga siljitib, qanday holatga sabab bo'ladi?",
        "Gazsiz alkaloz",
        ["Metabolik atsidoz", "Gazli atsidoz", "Ketotsidoz"],
        "Ammiak eriganida NH4+ va OH- hosil qilib, qon pH qiymatini ishqoriylashtiradi (alkaloz)."
    ),
    (
        241,
        "Qonda ammiak ortishi oqibatida qanday patologik holatlar yuzaga keladi?",
        "To'qimalarda gipoksiya, gipoenergetik holat va bosh miya zararlanishi",
        ["Glikogen to'planishi va suyak qattiqlashishi", "Qon bosimining keskin tushib ketishi", "Eritrotsitlar gemolizi"],
        "Giperammonemiya Krebs siklini susaytirib, energiya taqchilligi va neyrotoksik gipoksiya chaqiradi."
    ),
    (
        242,
        "Gamma-aminomoy kislotaning (GAMK) organizmdagi asosiy fiziologik ta'siri qanday?",
        "Markaziy nerv sistemasining asosiy tormozlovchi neyromediatori",
        ["Kuchli qo'zg'atuvchi mediator", "Oshqozon shirasini stimullaydigan gormon", "Qon tomirlarini toraytiruvchi omil"],
        "GAMK — bosh miyadagi bosh tormozlovchi neyromediator hisoblanadi."
    ),
    (
        243,
        "Fenilketonuriya kasalligida qonda fenilalanin konsentratsiyasi qanday o'zgaradi?",
        "20–30 marta ortadi",
        ["2–3 marta kamayadi", "100–200 marta kamayadi", "O'zgarishsiz qoladi"],
        "Fenilalaningidroksilaza yetishmaganda qonda fenilalanin 20-30 martagacha ko'payib ketadi."
    ),
    (
        244,
        "Fenilketonuriya kasalligida siydikda fenilalanin konsentratsiyasi qanday o'zgaradi?",
        "100–300 marta ortadi",
        ["2–5 marta ortadi", "20–30 marta kamayadi", "Siydikda butunlay yo'qoladi"],
        "Fenilalanin va uning ketohosilalari siydik orqali 100-300 baravar ko'p miqdorda ajraladi."
    ),
    (
        245,
        "Fenilketonuriya kasalligining og'ir ko'rinishlarida qanday belgilar mavjud?",
        "Aqliy va jismoniy orqada qolish, tutqanoq sindromi, gipopigmentatsiya",
        ["Bo'yning haddan tashqari o'sib ketishi, semizlik", "Qandli diabet va poliuriya", "Gipertoniya va yurak yetishmovchiligi"],
        "Toksik fenilmahsulotlar miyani zararlab aqliy zaiflik va melanin sintezi buzilib oqishlik (gipopigmentatsiya) beradi."
    ),
    (
        246,
        "Kofermentga bog'liq giperfenilalaninemiya (variantli FKU) uchrash statistikasi qanday?",
        "Har 1 mln chaqaloqda 1–2 ta",
        ["Har 10 ming chaqaloqda 1 ta", "Har 100 ming chaqaloqda 50 ta", "Har 5 ming chaqaloqda 1 ta"],
        "Tetragidrobiopterin (BH4) sintezi buzilishi bilan bog'liq variantli FKU juda kam: 1 mln chaqaloqda 1-2 ta uchraydi."
    ),
    (
        247,
        "Adenilat qoldig'i saqlovchi degidrogenazalarga qaysi kofermentlar kiradi?",
        "NAD, NADF, FAD",
        ["ATF, GTF, UTF", "Tiaminpirofosfat va piridoksal", "Biotin va koferment A"],
        "NAD+, NADF+ va FAD o'z tuzilishida adenilat (AMP) qoldig'ini saqlovchi piridin va flavin nukleotidlardir."
    ),
    (
        248,
        "Ovqat tarkibidagi nukleoproteinlar me'da shirasi HCl ta'sirida qanday moddalargacha parchalanadi?",
        "Oqsil va nuklein kislotalargacha",
        ["Erkin azot asoslari va ribozagacha", "Mononukleotidlarga to'liq", "Faqat ammiak va karbonat angidridgacha"],
        "Me'dada xlorid kislota nukleoproteinlarni denaturatsiyalab oqsil va nuklein kislotaga ajratadi."
    ),
    (
        249,
        "Nuklein kislotalar ichakda qaysi fermentlar ta'sirida parchalanadi?",
        "DNK-aza va RNK-aza",
        ["Pepsin va tripsin", "Amilaza va maltaza", "Lipaza va fosfolipaza"],
        "Ichak shirasidagi nukleazalar (DNKaza va RNKaza) nuklein kislotalarni oligonukleotidlarga parchalaydi."
    ),
    (
        250,
        "Nuklein kislotalar ichakdan asosan qanday ko'rinishda so'riladi?",
        "Nukleozidlar ko'rinishida",
        ["Polinukleotidlar ko'rinishida", "Butun DNK molekulasi holida", "Faqat erkin fosfat holida"],
        "Ichak enterotsitlari orqali nuklein komponentlari nukleozidlar va erkin asoslar holida so'riladi."
    ),
    (
        251,
        "To'qimalarda DNK gidrolizini qaysi fermentlar amalga oshiradi?",
        "Endonukleazalar",
        ["Polimerazalar", "Ligazalar", "Sintetazalar"],
        "To'qima ichidagi DNK zanjirlarini endonukleaza fermentlari gidrolizlaydi."
    ),
    (
        252,
        "EcoRI va EcoRII nima?",
        "Restriktazalar (begona DNK ni spetsifik joyidan kesuvchi fermentlar)",
        ["Polimerazalar (DNK zanjirini sintezlovchi fermentlar)", "Ligazalar (uzilgan bo'laklarni ulovchi fermentlar)", "Topoizomerazalar (DNK spiralini yoyuvchi fermentlar)"],
        "EcoRI va EcoRII — bakterial restriksiya endonukleazalari bo'lib, yot DNK ni parchalashda qatnashadi."
    ),
    (
        253,
        "FAG va virus DNK nukleotidlar ketma-ketligini aniqlashda qaysi fermentlardan foydalaniladi?",
        "Restriktazalar",
        ["Proteazalar", "Amilazalar", "Lipazalar"],
        "Restriksiya fermentlari yordamida DNK aniq qismlarga bo'linib tahlil qilinadi."
    ),
    (
        254,
        "Ribonukleaza I (RNKaza I) qanday ferment hisoblanadi?",
        "RNK ni gidrolitik parchalovchi ferment",
        ["DNK ni replikatsiya qiluvchi ferment", "Oqsillarni sintezlovchi ferment", "ATF ni hosil qiluvchi ferment"],
        "Ribonukleaza I — RNK molekulasidagi fosfodiefir bog'larini gidrolizlovchi nukleazadir."
    ),
    (
        255,
        "Pirimidin nukleozidlari parchalanishining oxirgi mahsulotlari qaysilar?",
        "CO2, NH3, siydikchil, beta-alanin, beta-aminoisomoy",
        ["Faqat siydik kislotasi va kalsiy", "Faqat mochevina va glyukoza", "Bilirubin va xolesterin"],
        "Pirimidin asoslari (uratsil, timin, sitozin) parchalanganda CO2, NH3, beta-alanin va beta-aminoisomoy hosil bo'ladi."
    ),
    (
        256,
        "Pirimidinlarning parchalanishidan hosil bo'lgan qaysi mahsulot anserin, karnozin va KoA hosil bo'lishida qatnashadi?",
        "beta-alanin",
        ["alfa-alanin", "Glutamin", "Glitsin"],
        "Uratsil katabolizmidan hosil bo'lgan beta-alanin karnozin, anserin va koferment A tarkibiga kiradi."
    ),
    (
        257,
        "Orotatsiduriya kasalligini davolashda qanday chora ko'riladi?",
        "Sutkada 0,5–1,0 g uridin qabul qilish",
        ["Sutkada 5 g glyukoza kiritish", "Ratsiondan oqsilni butunlay chiqarish", "Kalsiy preparatlarini buyurish"],
        "Uridin qabul qilinganda UMP ga aylanib, orotat sintezini allosterik tormozlaydi va orotatsiduriyani davolaydi."
    ),
    (
        258,
        "Nuklein kislotalardan qaysi ferment ta'sirida pirimidin mono-, di-, trinukleotidlar hosil bo'ladi?",
        "RNK-aza",
        ["DNK-polimeraza", "Peptidaza", "Glukokinaza"],
        "RNK molekulasidan pirimidin oligonukleotidlarni RNK-aza fermenti hosil qiladi."
    ),
    (
        259,
        "Dezoksiribonuklein kislotadan pirimidin nukleotidlari hosil bo'lishini qaysi ferment ta'minlaydi?",
        "DNK-aza",
        ["RNK-aza", "Lizotsim", "Tripsinojen"],
        "DNK-aza DNK zanjirini gidrolizlab nukleotidlar aralashmasini hosil qiladi."
    ),
    (
        260,
        "Nukleotidning tarkibiy qismlarini to'g'ri ko'rsating:",
        "Azot asosi, pentoza va fosfat qoldig'i",
        ["Faqat azot asosi va pentoza", "Azot asosi va yog' kislotasi", "Aminokislota va glyukoza"],
        "Nukleotid = Azot asosi (purin/pirimidin) + pentoza (riboza/dezoksiriboza) + fosfat kislota qoldig'i."
    ),
    (
        261,
        "Nukleozidning tarkibiy qismlarini to'g'ri ko'rsating:",
        "Azot asosi va pentoza",
        ["Azot asosi, pentoza va fosfat", "Faqat azot asosi va lipid", "Peptid va uglevod"],
        "Nukleozid tarkibida fosfat qoldig'i bo'lmaydi, faqat azot asosi va pentoza bo'ladi."
    ),
    (
        262,
        "Endonukleazalar DNK va RNK molekulasidagi qaysi bog'larni uzadi?",
        "Ichki fosfodiefir bog'larini",
        ["Zanjir uchidagi glikozid bog'larini", "Vodorod bog'larini faqat", "Peptid bog'larini"],
        "Endonukleazalar polinukleotid zanjirining ichki qismidagi fosfodiefir bog'larini gidrolizlaydi."
    ),
    (
        263,
        "Hazm qilishda qatnashuvchi DNKaza fermenti qaysi a'zodan ajraladi?",
        "Oshqozon osti bezidan",
        ["Jigardan", "Buyrakdan", "So'lak bezlaridan"],
        "Me'daosti bezi shirasida gidrolitik fermentlar, jumladan DNKaza va RNKaza mavjud."
    ),
    (
        264,
        "Me'daosti bezi DNKaza fermenti qaysi pH muhitda yuqori faollikka ega?",
        "pH = 6,8–8,0",
        ["pH = 1,5–2,0", "pH = 3,5–4,5", "pH = 9,5–11,0"],
        "Me'daosti bezi DNKazasi kuchsiz ishqoriy (pH 6,8-8,0) sharoitda eng faol ishlaydi."
    ),
    (
        265,
        "DNKaza fermenti qaysi ikki valentli ionlar ta'sirida faollashadi?",
        "Mg2+ va Mn2+",
        ["Ca2+ va Fe3+", "Na+ va K+", "Cu2+ va Zn2+"],
        "DNKaza faol markazi ikki valentli kationlar (Mg2+, Mn2+) ishtirokida aktivlashadi."
    ),
    (
        266,
        "Taloqdan ajraladigan nordon DNKaza II fermenti uchun qanday pH muhit optimal hisoblanadi?",
        "pH = 5,5–5,8",
        ["pH = 7,4–8,2", "pH = 1,0–2,0", "pH = 8,5–9,5"],
        "Taloqning lizosomal DNKaza II fermenti kislotali (pH 5,5-5,8) optimal faollikka ega."
    ),
    (
        267,
        "Qaysi fermentlar DNK zanjiri uchidan 5'-dezoksiribonukleotidlarni bosqichma-bosqich ajratadi?",
        "Ekzodezoksiribonukleazalar",
        ["Endonukleazalar", "RNK-polimerazalar", "Restriktazalar"],
        "Ekzonukleazalar zanjirning chetki qismidan nukleotidlarni bittalab ajratib boradi."
    ),
    (
        268,
        "E. coli bakteriyasidan DNK ni parchalovchi nechta ekzodezoksiribonukleaza ajratilgan?",
        "4 ta",
        ["1 ta", "10 ta", "20 ta"],
        "E. coli hujayrasida 4 xil ekzodezoksiribonukleaza (I, II, III, IV) aniqlangan."
    ),
    (
        269,
        "Glutamatga ammiak (NH3) birikishi natijasida qanday mahsulot hosil bo'ladi?",
        "Glutamin",
        ["Asparagin", "Alanin", "Alfa-ketoglutarat"],
        "Glutaminsintetaza fermenti glutamat va NH3 dan ATF sarflab glutamin hosil qiladi."
    ),
    (
        270,
        "Ichak hujayralarida glutamindan ammiak ajralganda qanday mahsulotlar hosil bo'ladi?",
        "Glutamat, piruvat va alfa-ketoglutarat",
        ["Mochevina va glitsin", "Faqat bilirubin va xolesterin", "Faqat laktat va atsetat"],
        "Enterotsitlarda glutamin metabolizmga uchrab ammiak, glutamat, piruvat va alfa-ketoglutarat beradi."
    ),
    (
        271,
        "Alfa-ketoglutaratning Krebs siklida to'liq parchalanish mahsuloti nima?",
        "CO2 va suv",
        ["Laktat va etanol", "Mochevina va ammiak", "Glyukoza va glikogen"],
        "Alfa-ketoglutarat TKS da to'liq oksidlanib yakunda CO2 va H2O hosil qiladi."
    ),
    (
        272,
        "Organizmda siydik orqali chiqarilayotgan umumiy azotning necha foizini mochevina (siydikchil) tashkil etadi?",
        "80–90%",
        ["20–30%", "50%", "10%"],
        "Organizmda oqsillar katabolizmidan chiqqan azotning 80-90% qismi mochevina holida ajraladi."
    ),
    (
        273,
        "Ammiak va karbonat angidriddan karbamoilfosfat hosil bo'lishi qaysi ferment ishtirokida boradi?",
        "Karbamoilfosfatsintaza I",
        ["Ornitintrankarbamoilaza", "Argininosuksinatsintaza", "Arginaza"],
        "Ornitin siklining birinchi tezlikni cheklovchi fermenti Karbamoilfosfatsintaza I dir."
    ),
    (
        274,
        "Ornitin siklida argininning gidrolizlanishi natijasida qanday mahsulotlar hosil bo'ladi?",
        "Ornitin va mochevina",
        ["Sitrullin va malat", "Fumarat va aspartat", "Argininosuksinat va ATF"],
        "Arginaza fermenti argininni gidrolizlab erkin mochevina va ornitin hosil qiladi."
    ),
    (
        275,
        "Ornitin sikli (mochevina biosintezi) asosan qaysi a'zo hujayralarida kechadi?",
        "Jigar hujayralarida (gepatotsitlarda)",
        ["Buyrak po'stlog'ida", "Mushak tolasida", "Bosh miyada"],
        "Mochevina hosil bo'lishi to'liq fermentlar to'plamiga ega bo'lgan jigarda amalga oshadi."
    ),
    (
        276,
        "Ornitin siklining boshlang'ich substratlari nima?",
        "CO2 va NH3 (ammiak)",
        ["Glyukoza va piruvat", "Yog' kislotasi va glitserin", "Mochevina va fumarat"],
        "Ornitin sikli CO2, ammiak va aspartat aminoguruhidan mochevina sintezlaydi."
    ),
    (
        277,
        "Ornitin siklining yakuniy mahsuloti nima?",
        "Mochevina (siydikchil)",
        ["Ammiak", "Siydik kislotasi", "Kreatinin"],
        "Ornitin siklining maqsadi zaharli ammiakdan zararsiz mochevina hosil qilishdir."
    ),
    (
        278,
        "Mushak va ichaklardan ortiqcha miqdordagi ammiak jigarga qaysi aminokislota ko'rinishida chiqariladi?",
        "Alanin",
        ["Lizin", "Metionin", "Triptofan"],
        "Mushak to'qimasida ammiak piruvatga birikib alanin hosil qiladi va qonga chiqadi (glyukoza-alanin sikli)."
    ),
    (
        279,
        "Ichak hujayralarida alanin hosil bo'lishida qaysi mahsulotlardan foydalaniladi?",
        "Glutamat va glutamin",
        ["Xolesterin va yog'lar", "Glitsin va bilirubin", "Gistidin va kalsiy"],
        "Ichak enterotsitlarida glutamin va glutamat transaminlanib alanin hosil bo'lishida qatnashadi."
    ),
    (
        280,
        "Ichaklarda hosil bo'lgan alanin darvoza venasi orqali qaysi organga boradi?",
        "Jigarga",
        ["Buyrakka", "O'pkaga", "Talog'ga"],
        "Qon oqimi orqali alanin jigarga yetib boradi va u yerda glyukoneogenezda ishlatiladi."
    ),
]

def append_to_csv():
    csv_path = Path("data/biokimyo_collections/biokimyo_variantli_209.csv")
    
    # Read existing rows
    existing_rows = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        existing_rows = list(reader)
        
    print(f"Existing rows in {csv_path}: {len(existing_rows)}")
    
    # Generate new rows
    new_rows = []
    for num, q, correct, distractors, explanation in NEW_QUESTIONS_DATA:
        # Check lengths
        assert len(q) <= 295, f"Question {num} too long: {len(q)}"
        assert len(correct) <= 95, f"Correct {num} too long: {len(correct)}"
        for d in distractors:
            assert len(d) <= 95, f"Distractor in {num} too long: {len(d)}"
        assert len(explanation) <= 200, f"Explanation {num} too long: {len(explanation)}"
        
        opt_a, opt_b, opt_c, opt_d, correct_letter = make_options(correct, distractors, seed_val=2100 + num)
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
            "topic": "Biokimyo variantli",
            "difficulty": "Medium",
            "timer": 25,
            "image": ""
        }
        new_rows.append(row)
        
    combined_rows = existing_rows + new_rows
    print(f"Total rows after appending: {len(combined_rows)}")
    
    # Write combined rows back to CSV
    fieldnames = [
        "question", "option_a", "option_b", "option_c", "option_d",
        "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_rows)
        
    print(f"Successfully wrote {len(combined_rows)} rows to {csv_path}")

if __name__ == "__main__":
    append_to_csv()
