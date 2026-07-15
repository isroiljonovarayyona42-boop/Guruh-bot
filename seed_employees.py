"""
46 ta xodimni bazaga qo'shish va har biriga ta'til tayinlash skripti.
Rasmda ko'rsatilgan ma'lumotlar asosida.
"""
import asyncio
import os
import sys
import io

# Windows konsol encoding muammosini hal qilish
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

# Loyiha papkasini PATH ga qo'shish
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db
from database import queries


# Xodimlar ma'lumotlari: (F.I.Sh., tug'ilgan kuni MM-DD, ta'til kuni YYYY-MM-DD)
EMPLOYEES_DATA = [
    ("Babamuradova Sayyora Djurayevna",   "05-23", "2026-07-01"),
    ("Maxmudova Dilnoza sharobiddinovi",   "11-17", "2026-07-21"),
    ("Yursunova dilfuza Yuldash qizi",     "08-04", "2026-09-11"),
    ("Abulfayziyev El'yor Rashidovich",    "04-24", "2026-12-01"),
    ("Yulyaxshiyev Sherzod Narzullayevich","04-27", "2026-12-01"),
    ("Xudashova surayyo Ixtiyor qizi",     "04-10", "2026-09-08"),
    ("Kukanova Sayyora Abatovna",          "09-06", "2026-05-18"),
    ("Kiranova Dilfuza Umirzakovna",       "03-01", "2026-08-25"),
    ("Egilikova lola Keldiyarovna",        "10-22", "2026-07-15"),
    ("Batirova dilnoza Baxodir qizi",      "06-22", "2026-04-02"),
    ("Ravshanova gulzoda Malikovna",       "03-01", "2026-06-02"),
    ("Kushakova Feruza Minullayevna",      "08-05", "2026-06-02"),
    ("Fayziyeva Laylo Ruzimurod qizi",     "01-12", "2026-07-22"),
    ("Safarova gulmira Muxiddin qizi",     "09-04", "2026-07-03"),
    ("Bazarbayeva Shaxnoza Userbayevna",   "01-24", "2026-07-22"),
    ("Tangriyeva Sarvinoz Ulug'bek qizi",  "10-25", "2026-07-06"),
    ("Kukanova dilnoza Mamaraimovna",      "01-14", "2026-09-08"),
    ("Kushakova Nasiba Ummatovna",         "09-15", "2026-09-08"),
    ("Akbaraliyeva Mariya Raxmanovna",     "12-18", "2026-07-01"),
    ("Xujiyev Nuriddin Narboy o'g'li",     "06-14", "2026-06-03"),
    ("Bazarova Gulhayo Baxrom qizi",       "09-11", "2026-09-09"),
    ("Turapova Saodat Tinchlikovna",       "03-02", "2026-12-01"),
    ("Islomova Iroda Amirovna",            "10-22", "2026-10-13"),
    ("Sattorova gulnora Alisher qizi",     "09-03", "2026-11-01"),
    ("Jurayeva Nigora Shavkatovna",        "08-20", "2026-08-01"),
    ("Jalgashova Xolida Sabirjanovna",     "12-15", "2026-09-02"),
    ("Umarova Jamila Musabekovna",         "11-07", "2026-08-05"),
    ("Baymiyeva Sayyora Berdikulovna",     "08-09", "2026-09-08"),
    ("Ravshanova Farida Raximjon qizi",    "02-22", "2026-12-12"),
    ("Norqulova Feruza Murodimovna",       "06-15", "2026-11-03"),
    ("Ubaydullayeva Mavjuda Akbar qizi",   "01-10", "2026-10-13"),
    ("Xudasheva Nafisa Rustamovna",        "01-10", "2026-10-13"),
    ("Bobomuratova Zulfiya Xayitboy qizi", "01-29", "2026-10-13"),
    ("Xudoyberdiyeva Farangiz Shuxrat qizi","08-08","2026-07-07"),
    ("Abdualimova Nilufar Po'lat qizi",    "10-15", "2026-12-01"),
    ("Dehqonova Malika Kabilovna",         "09-22", "2026-09-08"),
    ("Ravshanova Xolida Kurashbayevna",    "08-05", "2026-10-13"),
    ("Xurbayeva Nasiba Musurmonovna",      "06-06", "2026-11-03"),
    ("Jamambayeva Xafiza Ismoilovna",      "01-04", "2026-01-19"),
    ("Eshbabyeva Xikoyat Omanovna",        "01-27", "2026-07-25"),
    ("Bababekova Shoxida To'lqin qizi",    "07-17", "2026-10-01"),
    ("Beknazarova Nilufar Samarboyevna",   "07-15", "2026-10-02"),
    ("Xalikov Toshpulat Rejepovich",       "10-22", "2026-10-01"),
    ("Bobomurodov Kamol Ismoilovich",      "11-03", "2026-09-03"),
    ("Eshankulov Ismanjon Mashrabovich",   "05-05", "2026-09-08"),
    ("Qarshiyeva Mahsuda Norbek qizi",     "02-14", "2026-12-01"),
]



async def seed():
    """Bazani xodimlar va ta'tillar bilan to'ldiradi."""
    # Bazani yaratish
    await init_db()

    # Mavjud xodimlarni tekshirish
    existing = await queries.get_all_employees()
    if existing:
        print(f"[!] Bazada allaqachon {len(existing)} ta xodim mavjud.")
        answer = input("Davom etsinmi? Yangi xodimlar qo'shiladi (y/n): ").strip().lower()
        if answer != "y":
            print("Bekor qilindi.")
            return



    added_count = 0
    vacation_count = 0

    for full_name, birth_mm_dd, vacation_date_str in EMPLOYEES_DATA:
        # Xodim qo'shish
        emp_id = await queries.add_employee(
            full_name=full_name,
            username=None,
            birth_date=birth_mm_dd,
        )
        added_count += 1

        # Ta'til qo'shish (faqat 1 kun — rasmda ko'rsatilgan sana)
        await queries.add_vacation(
            employee_id=emp_id,
            start_date=vacation_date_str,
            end_date=vacation_date_str,
        )
        vacation_count += 1

        print(f"  [+] {added_count:2d}. {full_name} | BD: {birth_mm_dd} | Tatil: {vacation_date_str}")

    print(f"\nJami {added_count} ta xodim va {vacation_count} ta ta'til qo'shildi!")


if __name__ == "__main__":
    asyncio.run(seed())
