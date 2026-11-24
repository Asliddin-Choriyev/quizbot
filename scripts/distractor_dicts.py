import os
import re
import csv
import random
from pathlib import Path

# Special dictionary of manual overrides or specific domain distractors for key short questions
DOMAIN_DISTRACTORS = {
    # Ions
    "kalsiy ionlari": ["Kaliy ionlari", "Natriy ionlari", "Magniy ionlari"],
    "natriy ioni": ["Kaliy ioni", "Kalsiy ioni", "Xlor ioni"],
    "3 na⁺ tashqariga va 2 k⁺ ichkariga": ["2 Na⁺ tashqariga va 3 K⁺ ichkariga", "3 Na⁺ ichkariga va 2 K⁺ tashqariga", "1 Na⁺ tashqariga va 1 K⁺ ichkariga"],
    
    # Organs
    "qizil suyak ko‘migida": ["Sariq suyak ko'migida", "Taloqda", "Jigarda"],
    "qizil suyak ko'migida": ["Sariq suyak ko'migida", "Taloqda", "Jigarda"],
    "buyraklar": ["Jigar", "Taloq", "Oshqozon osti bezi"],
    "jigarda": ["Buyraklarda", "Taloqda", "Suyak ko'migida"],
    "uzunchoq miyada": ["Miyachada", "Gipotalamusda", "Orqa miyada"],
    "uzunchoq miya va ko‘prikda": ["Miyacha va o'rta miyada", "Gipotalamus va talamusda", "Orqa miya bo'yin qismida"],
    
    # Blood & Cells
    "qon plazmasi": ["Qon zardobi", "Limfa suyuqligi", "To'qima suyuqligi"],
    "suv": ["Oqsillar", "Glukoza", "Lipidlar"],
    "albuminlar": ["Globulinlar", "Fibrinogen", "Geparin"],
    "globin": ["Gem", "Albumin", "Ferritin"],
    "gem guruhi": ["Globin oqsili", "Lipid qavati", "Uglevod zanjiri"],
    "ikki valentli holatda": ["Uch valentli holatda", "Erkin ion holatida", "Oksidlangan ferrat holatida"],
    "ikki tomoni botiq disk": ["Shar shaklida", "Yassi plastinka", "Botiq-qavariq disksimon"],
    "taxminan 120 kun": ["Taxminan 7-10 kun", "Taxminan 30 kun", "Taxminan 1 yil"],
    "7,35–7,45": ["7,00–7,20", "7,50–7,70", "6,80–7,10"],
    "bikarbonat bufer tizimi": ["Fosfat bufer tizimi", "Oqsil bufer tizimi", "Gemoglobin bufer tizimi"],
    "oksigemoglobin": ["Karboksigemoglobin", "Karbaminohemoglobin", "Metgemoglobin"],
    "karboksigemoglobin": ["Oksigemoglobin", "Deoksigemoglobin", "Metgemoglobin"],
    "karbaminohemoglobin": ["Oksigemoglobin", "Karboksigemoglobin", "Metgemoglobin"],
    "s-simon shaklga": ["To'g'ri chiziqli shaklga", "Giperbolik shaklga", "Parabolik shaklga"],
    "eritropoetin": ["Trombopoetin", "Insulin", "Tiroksin"],
    "gazlarni tashish": ["Oziqlantirish", "Qon ivishini ta'minlash", "Gormonlarni tashish"],
    "yadrosining mavjud emasligi": ["Mitoxondriyalarning ko'pligi", "Ribosomalarning faolligi", "Ikki yadroliligi"],
    
    # Leukocytes
    "neytrofillar": ["Eozinofillar", "Bazofillar", "Limfotsitlar"],
    "eozinofillar": ["Neytrofillar", "Bazofillar", "Monotsitlar"],
    "bazofillar": ["Neytrofillar", "Eozinofillar", "Limfotsitlar"],
    "monotsit": ["Neytrofil", "Limfotsit", "Eritrotsit"],
    "makrofag": ["Fibroblast", "Plazmotsit", "Mastotsit"],
    "t-limfotsitlar": ["B-limfotsitlar", "Tabiiy killerlar", "Plazmotsitlar"],
    "b-limfotsitlar": ["T-limfotsitlar", "Monotsitlar", "Makrofaglar"],
    "gistamin va geparin": ["Serotonin va dofamin", "Adrenalin va noradrenalin", "Insulin va glyukagon"],
    "a antigeni": ["B antigeni", "D antigeni", "H antigeni"],
    "a va b antigenlari": ["Faqat A antigeni", "Faqat B antigeni", "Antigenlar mavjud emas"],
    "a va b antigenlari mavjud emas": ["Faqat A antigeni mavjud", "Faqat B antigeni mavjud", "A va B antigenlari mavjud"],
    "a antigeniga qarshi antitana": ["B antigeniga qarshi antitana", "D antigeniga qarshi antitana", "Antitanalar mavjud emas"],
    "rezus d antigenining mavjudligi": ["C antigenining mavjudligi", "E antigenining mavjudligi", "Antigenlarning yo'qligi"],
    
    # Muscles
    "troponin": ["Tropomiozin", "Kalmodulin", "Titina"],
    "kalmodulin": ["Troponin", "Miozin", "Aktin"],
    "sarkomer": ["Miofibrilla", "Sarkoplazma", "T-naycha"],
    "z chiziqlari": ["M chiziqlari", "H zonalari", "A disklari"],
    "qo‘zg‘aluvchanlik": ["O'tkazuvchanlik", "Qisqaruvchanlik", "Avtomatiya"],
    "yashirin davr": ["Qisqarish davri", "Bo'shashish davri", "Refrakter davr"],
    "bo‘shashish davri": ["Qisqarish davri", "Yashirin davr", "Tetanus davri"],
    "summatsiya": ["Akkomodatsiya", "Refrakterlik", "Adaptatsiya"],
    "to‘liq tetanus": ["Tishsimon tetanus", "Yakka qisqarish", "Muskul tonusi"],
    "to‘liq bo‘lmagan tetanus": ["To'liq tetanus", "Yakka qisqarish", "Izometrik qisqarish"],
    "miograf": ["Elektrokardiograf", "Spirometr", "Tonometr"],
    "sarkoplazmatik retikulum": ["Mitoxondriya", "Golji apparati", "Lizosoma"],
    "ko‘prikcha": ["Desmosoma", "Neksus", "Sinaps"],
    "uzunligi": ["Tarangligi", "Diametri", "Hajmi"],
    "uzunlik o‘zgaradi": ["Taranglik o'zgaradi", "Uzunlik doimiy qoladi", "Hajm keskin oshadi"],
    "izometrik qisqarish": ["Izotonik qisqarish", "Auksotonik qisqarish", "Eksentrik qisqarish"],
    "izotonik qisqarish": ["Izometrik qisqarish", "Tetanik qisqarish", "Tonik qisqarish"],
    
    # Heart
    "sinus tuguni": ["Atrioventrikulyar tugun", "Gis tutami", "Purkinye tolalari"],
    "sinus tugunidan": ["Atrioventrikulyar tugundan", "Gis tutamidan", "Purkinye tolalaridan"],
    "qisqaruvchanlik": ["Qo'zg'aluvchanlik", "O'tkazuvchanlik", "Avtomatiya"],
    "qorinchalar sistolasi": ["Qorinchalar diastolasi", "Bo'lmachalar diastolasi", "Umumiy pauza"],
    "qorinchalar diastolasi": ["Qorinchalar sistolasi", "Bo'lmachalar sistolasi", "Izovolumetrik qisqarish"],
    "izovolumetrik qisqarish bosqichi": ["Tez haydash bosqichi", "Sekin haydash bosqichi", "Izovolumetrik bo'shashish"],
    "izovolumetrik bo‘shashish bosqichi": ["Izovolumetrik qisqarish", "Tez to'lish bosqichi", "Sekin to'lish bosqichi"],
    
    # Respiration
    "diafragma": ["Tashqi qovurg'alararo mushaklar", "Ichki qovurg'alararo mushaklar", "Qorin to'g'ri mushagi"],
    "karbonat angidraza": ["Katalaza", "Peroksidaza", "Amilaza"],
    "gering–breyer refleksi": ["Dagnini-Ashner refleksi", "Golts refleksi", "Beynbridj refleksi"],
    "ortadi": ["Kamayadi", "O'zgarmaydi", "Dastlab kamayadi, so'ng ortadi"],
    "kamayadi": ["Ortadi", "O'zgarmaydi", "Keskin tebranadi"],
    
    # Vessels
    "arteriolalar": ["Kapillyarlar", "Venulalar", "Aorta"],
    "arteriyalarda": ["Kapillyarlarda", "Venalarda", "Venulalarda"],
    "vazokonstriksiya": ["Vazodilatatsiya", "Bronxokonstriksiya", "Kardiokonstriksiya"],
    "vazodilatatsiya": ["Vazokonstriksiya", "Bronxodilatatsiya", "Kardiodilatatsiya"],
    "60 millimetr simob ustuni": ["40 mm simob ustuni", "50 mm simob ustuni", "90 mm simob ustuni"],
    "40 millimetr simob ustuni": ["60 mm simob ustuni", "50 mm simob ustuni", "80 mm simob ustuni"],
    "taxminan 16 marta ortadi": ["Taxminan 4 marta ortadi", "Taxminan 8 marta ortadi", "Taxminan 2 marta ortadi"],
    "taxminan 16 marta kamayadi": ["Taxminan 4 marta kamayadi", "Taxminan 8 marta kamayadi", "Taxminan 2 marta kamayadi"],
}

# Manual answer shortening dictionary for long answers (>90 chars)
SHORTEN_ANSWERS = {
    "normal funksiyalar haqidagi bilimlarning klinik jarayonlarni tushuntirishga xizmat qilishiga":
        "Normal funksiyalar bilimi klinik jarayonlarni tushuntirishga xizmat qilishiga",
        
    "ionlarning notekis taqsimlanishini saqlab, membrana potensialining yuzaga kelishini ta'minlaydi":
        "Ionlar notekis taqsimlanishini saqlab, membrana potensialini ta'minlaydi",
        
    "qo'zg'alish yuzaga kelishi uchun ta'sir kuchi va davomiyligi o'rtasidagi bog'liqlikni ko'rsatadi":
        "Qo'zg'alish uchun ta'sir kuchi va davomiyligi bog'liqligini ko'rsatadi",
        
    "na⁺/k⁺-atfaza susayadi → ion gradienti kamayadi → membrana potensiali pasayadi → qo'zg'aluvchanlik buziladi":
        "ATFaza susayishi → gradient kamayishi → potensial pasayishi → qo'zg'aluvchanlik buzilishi",
        
    "membrana potensiali keskin kamayadi, chunki ion gradientining elektr ifodalanishi yo'qoladi":
        "Membrana potensiali kamayadi, chunki gradientning elektr ifodasi yo'qoladi",
        
    "membrananing elektr izolyatsiyasini kuchaytirib, tokning samarali tarqalishiga yordam beradi":
        "Membrana izolyatsiyasini kuchaytirib, tokning tez tarqalishini ta'minlaydi",
        
    "nerv tolasi bo‘ylab qo‘zg‘alish ikki tomonga, kimyoviy sinapsda esa funksional ravishda bir tomonga tarqalishi mumkin":
        "Nerv tolasida ikki tomonga, kimyoviy sinapsda bir tomonga tarqaladi",
        
    "miyelin elektr izolyatsiyani kuchaytiradi va qo‘zg‘alish ranvye tugunlari orasida saltator tarqaladi":
        "Miyelin izolyatsiyani ta'minlaydi va saltator impuls tarqaladi",
        
    "tomir osti biriktiruvchi to‘qimasi ochilib, yopishishni ta’minlovchi molekulalar faollashadi":
        "Subendoteliy ochilib, yopishishni ta'minlovchi omillar faollashadi",
        
    "qon ivishining nazoratsiz tarqalishi sog‘lom tomirlarda tromb hosil bo‘lishiga olib kelishi mumkin":
        "Sog'lom tomirlarda nazoratsiz tromb hosil bo'lishining oldini olish uchun",
        
    "asetilxolin sinus tugunidagi hujayralarning diastolik depolyarizatsiyasini sekinlashtiradi":
        "Asetilxolin sinus tugunida diastolik depolyarizatsiyani sekinlashtiradi",
        
    "ekstrakardial boshqaruvda yurakdan tashqaridagi nerv markazlari va nerv yo‘llari qatnashadi":
        "Yurakdan tashqaridagi vegetativ nerv markazlari va yo'llari qatnashadi",
        
    "sinus tuguni parasimpatik nerv tolalari bilan boy ta’minlanganligi sababli ta’sir kuchli bo‘ladi":
        "Sinus tuguni parasimpatik tolalar bilan boy ta'minlanganligi sababli",
        
    "arterial retseptorlar faollashib, yurak faoliyatini susaytiruvchi vegetativ javobni kuchaytiradi":
        "Arterial retseptorlar faollashib, susaytiruvchi vegetativ javobni oshiradi",
        
    "nerv ta’siri yurakning o‘z avtomatik faolligini asosan o‘zgartiradi, lekin uni hosil qilmaydi":
        "Nerv ta'siri yurak avtomatiyasini modulyatsiya qiladi, hosil qilmaydi",
        
    "mahalliy nerv zanjirlari orqali bir yurak bo‘limidagi o‘zgarish boshqa bo‘lim faoliyatini o‘zgartirishi mumkin":
        "Intrakardial zanjirlar orqali boshqa bo'lim faoliyatini o'zgartirishi mumkin",
        
    "har bir yurak sikliga mos arterial bosim to‘lqinlarining periferik namoyonini baholashga yordam beradi":
        "Arterial bosim to'lqinlarining periferik namoyonini baholashga xizmat qiladi",
        
    "yurak faoliyatini arterial bosim va venoz qaytishdagi o‘zgarishlarga moslashtirish imkonini beradi":
        "Faoliyatni bosim va venoz qaytish o'zgarishlariga moslashtirish imkonini beradi",
        
    "markaziy boshqaruv yuqori nerv markazlarini, periferik boshqaruv esa mahalliy nerv tuzilmalarini o‘z ichiga oladi":
        "Markaziy boshqaruv MNT ni, periferik esa mahalliy tuzilmalarni o'z ichiga oladi",
        
    "parasimpatik ta’sir sinus tugunining avtomatik faolligini va yurak chastotasini kamaytirdi":
        "Parasimpatik ta'sir sinus tuguni avtomatiyasi va chastotasini kamaytiradi",
        
    "bo‘lmachalar cho‘zilishiga javoban yurak urishlarini tezlashtiruvchi refleks bilan bog‘liq":
        "Bo'lmachalar cho'zilishiga javob beruvchi tezlashtiruvchi refleks bilan bog'liq",
        
    "yurakning elektr qo‘zg‘alishi saqlangan bo‘lsa ham, mexanik chiqarish samaradorligi pasaygan bo‘lishi mumkin":
        "Elektr qo'zg'alish saqlangan, ammo mexanik chiqarish samaradorligi pasaygan",
        
    "qorinchalar qisqarishi boshlanishida atrioventrikulyar klapanlarning yopilishi bilan bog‘liq":
        "Qorinchalar sistolasi boshida AV-klapanlarning yopilishi bilan bog'liq",
        
    "intrakardial nerv tizimi yurak bo‘limlari faoliyatini mahalliy muvofiqlashtirishda qatnashadi":
        "Intrakardial nerv tizimi bo'limlar faoliyatini mahalliy muvofiqlashtiradi",
        
    "ayrim yurak qo‘zg‘alishlari samarali mexanik qisqarish bilan yakunlanmayotgan bo‘lishi mumkin":
        "Ayrim elektr impulslar mexanik qisqarish bilan yakunlanmayotgan bo'lishi mumkin",
        
    "bo‘lmachalar va qorinchalar qo‘zg‘alishi orasidagi vaqtni uzaytirib, ularning ketma-ket ishlashiga yordam beradi":
        "Bo'lmacha va qorinchalarning ketma-ket muvofiq ishlashini ta'minlaydi",
        
    "retseptor, afferent yo‘l yoki markaziy reflektor mexanizm faoliyatining buzilishi javobni susaytiradi":
        "Refleks yoyining tarkibiy qismlari faoliyati buzilganligi sababli",
        
    "ventilyatsiya qilingan alveolalarda qonning gazlar bilan samarali almashinuvini ta’minlaydi":
        "Ventilyatsiya qilingan alveolalarda qonning gazlar almashinuvini ta'minlaydi",
        
    "qorinchalar mushagining qisqarishi va qonning arteriyalarga haydalishi":
        "Qorinchalar mushagining qisqarishi va qonning haydalishi",
        
    "sog‘lom odamda funksiyaning moslashuvchan o‘zgarish oralig‘ini":
        "Sog'lom organizmda moslashuvchan o'zgarish oralig'ini",
}

print("Loaded dictionaries and constants successfully.")
