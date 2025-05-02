import os
import random
import time
import requests
import json
import shutil
from bs4 import BeautifulSoup

BASE_URL = "https://www.globus.ru"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
}
HTML_DIR = "html_pages"

def choose_category(config_path="config.json"):
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return None

    categories = config.get("categories", {})
    if not categories:
        print("❌ В конфигурации не найдено ни одной категории.")
        return None

    print("Выберите группу категорий:")
    group_names = list(categories.keys())
    for i, group in enumerate(group_names, 1):
        print(f"{i}. {group}")

    try:
        group_choice = int(input("Введите номер группы: "))
        selected_group = group_names[group_choice - 1]
    except (ValueError, IndexError):
        print("❌ Неверный выбор группы.")
        return None

    subcategories = categories[selected_group]
    print(f"\nВы выбрали: {selected_group}")
    print("Выберите категорию:")
    subcat_names = list(subcategories.keys())
    for i, subcat in enumerate(subcat_names, 1):
        print(f"{i}. {subcat}")

    try:
        subcat_choice = int(input("Введите номер категории: "))
        selected_category = subcat_names[subcat_choice - 1]
    except (ValueError, IndexError):
        print("❌ Неверный выбор категории.")
        return None

    url = subcategories[selected_category]
    print(f"\n✅ Вы выбрали категорию: {selected_category}\nСсылка: {url}")
    return url

def fetch_page(url, timeout=10):
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"❌ Ошибка при запросе {url}: {e}")
        return None

def get_total_pages(html):
    soup = BeautifulSoup(html, "lxml")
    pages = soup.select("a.js-navigation__page[data-page]")
    if not pages:
        return 1
    try:
        page_numbers = [int(p["data-page"]) for p in pages if p["data-page"].isdigit()]
        return max(page_numbers)
    except Exception as e:
        print(f"❌ Ошибка при определении количества страниц: {e}")
        return 1

def download_all_pages(category_url):
    if not os.path.exists(HTML_DIR):
        os.makedirs(HTML_DIR)

    print("Загружаем первую страницу...")
    first_html = fetch_page(category_url)
    if not first_html:
        print("❌ Не удалось загрузить первую страницу.")
        return False

    with open(f"{HTML_DIR}/page_1.html", "w", encoding="utf-8") as f:
        f.write(first_html)

    total_pages = get_total_pages(first_html)
    print(f"📄 Всего страниц в категории: {total_pages}")

    for page in range(2, total_pages + 1):
        url = f"{category_url}?page={page}"
        html = fetch_page(url)
        if not html:
            print(f"⚠️ Страница {page} не загружена.")
            continue
        filepath = os.path.join(HTML_DIR, f"page_{page}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Страница {page} сохранена ({len(html)} символов).")
        time.sleep(random.uniform(1, 2))

    return True

def parse_saved_pages():
    if not os.path.exists(HTML_DIR):
        print("❌ Папка с HTML-файлами не найдена.")
        return []

    all_items = []
    for filename in sorted(os.listdir(HTML_DIR)):
        if filename.endswith(".html"):
            with open(os.path.join(HTML_DIR, filename), encoding="utf-8") as f:
                html = f.read()
            items = parse_items(html)
            all_items.extend(items)

    return all_items

def parse_items(html):
    soup = BeautifulSoup(html, "lxml")
    items = []

    products = soup.find_all("a", class_="pim-list__item pim-list__item--standart ga-event")
    for product in products:
        title_tag = product.find("div", class_="pim-list__item-title js-crop-text")
        price_tag = product.find("span", class_="pim-list__item-price-actual-main")
        if title_tag:
            title = title_tag.text.strip()
            price = price_tag.text.strip() + " ₽" if price_tag else "Цена не найдена"
            link = BASE_URL + product.get("href")
            items.append({
                "Название": title,
                "Цена": price,
                "Ссылка": link
            })
    return items

def save_to_json(data, filename="products.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"💾 Данные сохранены в {filename}")

def cleanup_html():
    if os.path.exists(HTML_DIR):
        shutil.rmtree(HTML_DIR)
        print("🧹 Временные HTML-файлы удалены.")

def main():
    category_url = choose_category()
    if not category_url:
        return

    if download_all_pages(category_url):
        all_items = parse_saved_pages()
        print(f"\n📦 Всего собрано товаров: {len(all_items)}")
        save_to_json(all_items)
        cleanup_html()
    else:
        print("❌ Не удалось загрузить страницы.")

if __name__ == "__main__":
    main()