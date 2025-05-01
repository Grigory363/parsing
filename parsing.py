from fileinput import filename
import os
import random
from shlex import join
import time
import requests
import json
import lxml
from bs4 import BeautifulSoup

BASE_URL = "https://www.globus.ru"
CATEGORY_URL = f"{BASE_URL}/catalog/chay-kofe-kakao/kofe/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
}
HTML_DIR = "html_pages"

def fetch_page(url, timeout=10 ):
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None

def get_total_pages(html):
    soup = BeautifulSoup(html, "lxml")
    pages = soup.select("a.js-navigation__page[data-page]")
    if not pages:
        return 1
    page_numbers = [int(p['data-page']) for p in pages if p['data-page'].isdigit()]
    return max(page_numbers) if page_numbers else 1

def download_all_pages():
    os.makedirs(HTML_DIR, exist_ok=True)

    print("Загружаем первую страницу...")
    first_html = fetch_page(CATEGORY_URL)
    if not first_html:
        print("Не удалось загрузить первую страницу.")
        return
    
    total_pages = get_total_pages(first_html)
    print(f"Всего страниц для загрузки: {total_pages}")

    for page in range(1, total_pages + 1):
        url = f"{CATEGORY_URL}?page={page}"
        print(f"→ Скачиваем страницу {page}: {url}")
        html = fetch_page(url)
        if html:
            with open(f"{HTML_DIR}/page_{page}.html", "w", encoding="utf-8") as f:
                f.write(html)
        else:
            print(print(f"⚠️ Не удалось скачать страницу {page}"))
        time.sleep(random.uniform(1, 2))

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
                "Ссылка на товар": link
            })
    return items

def parse_saved_pages():
    all_items = []
    for filename in sorted(os.listdir(HTML_DIR)):
        if filename.endswith(".html"):
            filepath = os.path.join(HTML_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()
        items = parse_items(html)
        print(f"Распарсено из {filename}: {len(items)} товаров")
        all_items.extend(items)

    print(f"Итого собрано товаров: {len(all_items)}")
    save_to_json(all_items)

def save_to_json(date, filename="products.json"):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(date, file, ensure_ascii=False, indent=4)
    print(f"✅ Данные сохранены в {filename}")

def cleanup_html():
    for filename in os.listdir(HTML_DIR):
        os.remove(os.path.join(HTML_DIR, filename))
    os.rmdir(HTML_DIR)
    print("🧹 HTML-файлы удалены")

if __name__=='__main__':
    download_all_pages()
    parse_saved_pages()
    cleanup_html()

    # def main():
    # print("Загружаем первую страницу...")
    # first_page_html = fetch_page(CATEGORY_URL)
    # if not first_page_html:
    #     print("Не удалось загрузить первую страницу.")
    #     return
    # total_pages = get_total_pages(first_page_html)
    # print(f"Всего страниц: {total_pages}")

    # all_items = []

    # for page in range(1, total_pages + 1):
    #     url = f"{CATEGORY_URL}?page={page}"
    #     print(f"Парсим страницу {page}: {url}")
    #     html = fetch_page(url)
    #     if not html:
    #         print(f"Не удалось загрузить страницу {page}. Пропускаем.")
    #         continue
    #     items = parse_items(html)
    #     if not items:
    #         print(f"На странице {page} нет товаров.")
    #         continue
    #     all_items.extend(items)
    #     time.sleep(random.uniform(1, 2))

    # print(f"Собрано товаров: {len(all_items)}")
    # save_to_json(all_items)