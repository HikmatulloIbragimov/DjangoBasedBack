import os
import django
import pandas as pd

# 1. Настройка Django — укажи свой путь к настройкам
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bek.settings')
django.setup()

from app.models import Merchandise

def clean_text(s):
    return s.strip() if isinstance(s, str) else ''

def import_merchandise_from_excel(path='doc.xlsx'):
    # Читаем Excel без заголовков, чтобы корректно задать заголовки вручную
    df_raw = pd.read_excel(path, header=None)

    # Заголовки у тебя на 4-й строке (индекс 3)
    header_row_index = 3

    headers = df_raw.iloc[header_row_index].tolist()
    data = df_raw.iloc[header_row_index + 1:].copy()
    data.columns = headers
    data.reset_index(drop=True, inplace=True)

    print("Колонки из Excel:", data.columns.tolist())
    print("Первые 5 строк:")
    print(data.head())

    game_slug = 'mobile-legends-global'  # жестко указываем игру

    count = 0
    for _, row in data.iterrows():
        slug = clean_text(str(row.get('id', '')))
        if not slug or slug.lower() == 'nan':
            continue  # пропускаем пустые или некорректные строки

        name = clean_text(str(row.get('name', '')))
        name_ru = clean_text(str(row.get('name_ru', '')))
        name_en = clean_text(str(row.get('name_en', '')))
        price = clean_text(str(row.get('price', '')))
        currency = clean_text(str(row.get('currency', '')))
        currency_ru = clean_text(str(row.get('currency_ru', '')))
        currency_en = clean_text(str(row.get('currency_en', '')))
        category = clean_text(str(row.get('category', '')))
        server = clean_text(str(row.get('server', '')))
        tags = clean_text(str(row.get('tags', '')))
        enabled = True
        reseller_id = clean_text(str(row.get('reseller_id', '')))
        reseller_category = clean_text(str(row.get('reseller_category', '')))
        slug = clean_text(str(row.get('slug', '')))

        merch, created = Merchandise.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'name_ru': name_ru,
                'name_en': name_en,
                'price': price,
                'currency': currency,
                'currency_ru': currency_ru,
                'currency_en': currency_en,
                'game': game_slug,
                'category': category,
                'server': server,
                'tags': tags,
                'enabled': enabled,
                'reseller_id': reseller_id,
                'reseller_category': reseller_category,
            }
        )
        print(f"{'Создан' if created else 'Обновлен'} товар: {slug}")
        count += 1

    print(f"Импортировано/обновлено {count} товаров.")

if __name__ == '__main__':
    import_merchandise_from_excel()
