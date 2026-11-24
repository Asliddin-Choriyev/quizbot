import csv
from pathlib import Path

# Parsed questions 69 to 120
NEW_QUESTIONS = [
    (69, "Go'daklar oshqozonida sut ivishining fiziologik ahamiyati uning uglevod va yog'lar hazm bo'ladigan vaqtgacha oshqozonda ushlab turishidan iboratdir.", "Yo'q"),
    (70, "Oshqozon shirasi murakkab uglevodlarni parchalaydigan fermentni o'zida saqlamaydi.", "Ha"),
    (71, "Oshqozonda so'lak amilazasi ta'siri to'xtamasdan uglevodlarni parchalashga ishtirok etadi. (pH=1-2)", "Yo'q"),
    (72, "Oshqozonda so'lak amilazasi ta'siri to'xtaydi, biroq oshqozon shirasi ta'sir ko'rsatolmaydigan ovqat luqmasining chuqur ichki qismida so'lak amilazasi ta'siri saqlanadi. (pH=1-2)", "Ha"),
    (73, "GLYUT 3, GLYUT 1 ga nisbatan glyukoza bilan yaxshiroq bog'lanadi. U glyukozani nerv hujayralari va boshqa to'qimalarga doimiy tushib turishini ta'minlaydi.", "Ha"),
    (74, "Glyukozaning laktatga aylanish jarayoni sut kislotali bijg'ish deb ataladi. Ushbu jarayonni katalizlovchi ferment bu – laktatdegidrogenaza.", "Ha"),
    (75, "Glyukozaning laktatga aylanish jarayoni sut kislotali bijg'ish deb ataladi. Ushbu jarayonni katalizlovchi ferment bu – piruvatkinaza.", "Yo'q"),
    (76, "Piruvat (laktatdegidrogenaza) → laktat", "Ha"),
    (77, "Fruktoza va galaktoza glyukoza singari CO2 va H2O ga oksidlanadi.", "Ha"),
    (78, "Fruktoza va galaktoza aminokislotalar singari CO2 va H2O, mochevinaga oksidlanadi.", "Yo'q"),
    (79, "Saxarozadan hosil bo'lgan fruktoza metabolizmi fruktokinaza fermenti yordamida fruktoza-1-fosfat hosil bo'ladigan fosforlanish reaksiyasi bilan boshlanadi.", "Ha"),
    (80, "Saxarozadan hosil bo'lgan fruktoza metabolizmi fruktokinaza fermenti yordamida fruktoza-6-fosfat hosil bo'ladigan fosforlanish reaksiyasi bilan boshlanadi.", "Yo'q"),
    (81, "Fruktoza-1-fosfat aldolaza fermentining genetik nuqsoni tufayli fruktozani irsiy ko'taraolmaslik yuzaga keladi.", "Ha"),
    (82, "Glyukoza-6-fosfat aldolaza fermentining genetik nuqsoni tufayli ratsionga mevalar, saxaroza qo'shilganda qusish, qorinda og'riq, diareya, gipoglikemiya hatto koma fruktoza saqlovchi ozuqa qabul qilingandan keyin 30 daqiqada namoyon bo'ladi.", "Yo'q"),
    (83, "Fruktoza-1-fosfat aldolaza fermentining genetik nuqsoni tufayli ratsionga mevalar, saxaroza qo'shilganda qusish, qorinda og'riq, diareya, gipoglikemiya hatto koma fruktoza saqlovchi ozuqa qabul qilingandan keyin 30 daqiqada namoyon bo'ladi.", "Ha"),
    (84, "Galaktoza ichaklarda laktoza gidrolizi tufayli hosil bo'ladi.", "Ha"),
    (85, "Galaktozemiya kasalligi glyukoza metabolizmida galaktozani kirituvchi 3 fermentning birortasida nasliy nuqson bo'lishi tufayli yuzaga keladi.", "Ha"),
    (86, "Galaktozemiya kasalligi erta boshlanib, bolalar uchun xavfli. Chunki asosiy sabab uglevod manbai laktoza saqlovchi ona sutidir.", "Ha"),
    (87, "Galaktozemiya kasalligi erta boshlanib, bolalar uchun xavfli. Chunki asosiy sabab kazein oqsili hisoblanadi va bu oqsil ona suti tarkibida bor.", "Yo'q"),
    (88, "Galaktozemiya kasalligi tug'ilganidan bir necha kun o'tgandan keyin gavharda katarakta rivojlanishiga olib keladi.", "Ha"),
    (89, "Gipolaktaziya kasalligida davo choralari sifatida: 1) Laktoza saqlovchi mahsulotlarni cheklash; 2) Peroral laktoza fermentini qabul qilishni ko'rsatish mumkin.", "Ha"),
    (90, "Gipolaktaziya kasalligida davo choralari sifatida: 1) Kazein saqlovchi mahsulotlarni cheklash; 2) Aminokislotalargacha parchalangan sut iste'moli.", "Yo'q"),
    (91, "Alanin glikogen aminokislota hisoblanadi.", "Ha"),
    (92, "Serin glikogen aminokislota hisoblanadi.", "Yo'q"),
    (93, "Aminokislotalar molekulalararo dezaminlanish reaksiyalari natijasida to'yinmagan yog' kislotalar hosil bo'ladi.", "Ha"),
    (94, "Aminokislotalar dekarboksillanish reaksiyalari natijasida to'yinmagan yog' kislotalar hosil bo'ladi.", "Yo'q"),
    (95, "Organizmda ammiakning ma'lum qismi ichakda bakteriyalarning ovqat oqsillariga ta'siri natijasida hosil bo'ladi va qopqa vena orqali qonga tushadi.", "Ha"),
    (96, "Organizmda ammiakning ma'lum qismi ichakda bakteriyalarning xolesterolga ta'siri natijasida hosil bo'ladi va qopqa vena orqali qonga tushadi.", "Yo'q"),
    (97, "Jigarda ammiakning katta qismi ushlanib qolishi natijasida qonda miqdori yuqori bo'lmaydi (0.4-0.7 mg/l).", "Ha"),
    (98, "Buyrak va ichakda ammiakning katta qismi ushlanib qolishi natijasida qonda miqdori yuqori bo'lmaydi (0.4-0.7 mg/l).", "Yo'q"),
    (99, "Giperglikemiyaning yengil holatida letal natija koma rivojlanadi.", "Yo'q"),
    (100, "Giperammonimiyaning og'ir holatida letal natija koma rivojlanadi.", "Ha"),
    (101, "Atsidoz kasalligining sababi qonda ammiak konsentratsiyasining ortishi pH ni ishqoriy tarafga siljitadi.", "Yo'q"),
    (102, "Ammiakning yuqori konsentratsiyasi nerv to'qimasida glutamatdan glyukoza sintezini stimullaydi.", "Yo'q"),
    (103, "Ammiakning yuqori konsentratsiyasi nerv to'qimasida glutamatdan glutamin sintezini stimullaydi.", "Ha"),
    (104, "Alkaloz kasalligining sababi qonda ammiak konsentratsiyasining ortishi pH ni ishqoriy tarafga siljitadi.", "Ha"),
    (105, "Serotonin o'tkazuvchi yo'llar mediatori hisoblanadi.", "Ha"),
    (106, "Fenilalanin va tirozin almashtirib bo'lmaydigan aminokislota hisoblanadi.", "Yo'q"),
    (107, "Fenilalanin almashtirib bo'lmaydigan, tirozin almashadigan aminokislota hisoblanadi.", "Ha"),
    (108, "Fenilalaningidroksilaza nuqsoni fenilketonuriya kasalligiga olib keladi.", "Ha"),
    (109, "Fenilalaningidroksilaza nuqsoni giperurikemiya kasalligiga olib keladi.", "Yo'q"),
    (110, "Nukleotidlar organik birikmalar guruhi bo'lib, aminokislotalarning fosforli efirlari hisoblanadi.", "Yo'q"),
    (111, "Klassik FKU (fenilketonuriya) kasalligi fenilalaningidroksilaza genidagi mutatsiyalarga bog'liq irsiy kasallik, ferment faolligining pasayishi yoki to'liq inaktivatsiyasiga olib kelishi.", "Ha"),
    (112, "Nuklein kislotalar organik birikmalar guruhi bo'lib, nukleotidlarning fosforli efirlari hisoblanadi.", "Ha"),
    (113, "Organizmdagi barcha hujayralar amalda nukleotidlarni sintezlashga qodirdir.", "Ha"),
    (114, "Organizmdagi ma'lum bir hujayralargina amalda nukleotidlarni sintezlashga qodirdir.", "Yo'q"),
    (115, "Ichak shirasi tarkibida polinukleotidaza, nukleozidazalar, fosfatazalar bo'lib nukleotidlarning parchalanishini ta'minlaydi.", "Ha"),
    (116, "Dezoksiribonukleaza DNK molekulasidagi fosfoefir bog'lar uzilishini katalizlab, n-oligodezoksiribonukleotidlarni hosil qiladi.", "Ha"),
    (117, "Restriktazalar aniq va spesifik ta'sir ko'rsatadi, shu tufayli FAG va virus DNK nukleotidlar qoldiqlarini aniqlashda ulardan foydalaniladi.", "Ha"),
    (118, "Oratatsiduriya bu siydik bilan ko'p miqdorda orotat kislota ajralib chiqishi hisoblanadi.", "Ha"),
    (119, "Davolanmagan holatlarda irsiy oratatsiduriya kasalligi qaytmas aqliy va jismoniy rivojlanishdan ortda qolishga olib keladi.", "Ha"),
    (120, "Davolanmagan holatlarda irsiy oratatsiduriya kasalligi falajlikka olib keladi.", "Yo'q"),
]

def main():
    # 1. Read existing rows 1 to 68
    csv_old = Path("data/biokimyo_collections/biokimyo_ha_yoq_68.csv")
    with open(csv_old, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        
    print(f"Loaded {len(all_rows)} existing rows.")
    assert len(all_rows) == 68
    
    # 2. Append new rows 69 to 120
    for num, q_text, ans in NEW_QUESTIONS:
        row = {
            "question": q_text,
            "option_a": "Ha",
            "option_b": "Yo'q",
            "option_c": "",
            "option_d": "",
            "correct_answer": "A" if ans == "Ha" else "B",
            "explanation": f"To'g'ri javob: {ans}",
            "topic": "Biokimyo: Ha / Yo'q testlari",
            "difficulty": "Medium",
            "timer": 20,
            "image": ""
        }
        all_rows.append(row)
        
    print(f"Total rows now: {len(all_rows)} (1 to 120)")
    assert len(all_rows) == 120
    
    # Verify all rows
    for idx, r in enumerate(all_rows):
        assert len(r["question"]) <= 295, f"Row {idx+1} question too long: {len(r['question'])}"
        assert r["correct_answer"] in ["A", "B"], f"Row {idx+1} invalid correct_answer: {r['correct_answer']}"
        assert len(r["explanation"]) <= 200, f"Row {idx+1} explanation too long: {len(r['explanation'])}"
        
    # Write to both biokimyo_ha_yoq_120.csv and biokimyo_ha_yoq_68.csv
    fieldnames = [
        "question", "option_a", "option_b", "option_c", "option_d",
        "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
    ]
    
    csv_120 = Path("data/biokimyo_collections/biokimyo_ha_yoq_120.csv")
    for target in [csv_120, csv_old]:
        with open(target, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"Successfully saved {len(all_rows)} rows to {target}")

if __name__ == "__main__":
    main()
