import asyncio
import json
import random
import re
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Set
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

BASE = "https://mysakura.ru"

CATALOG_PATH = "/catalog/dvigatel"
CATALOG_URL = urljoin(BASE, CATALOG_PATH)

PRODUCT_URL_RE = re.compile(r"^/product/\d+/?$")

PRICE_NEAR_RUB_RE = re.compile(r"(\d[\d \xa0]{2,}\d)\s*(₽|руб)", re.IGNORECASE)

YACLOUD_PREFIX = "https://storage.yandexcloud.net/mysakura/"
IMG_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp)(\?|$)", re.I)

# Если знаешь точный файл-заглушку, добавь сюда кусок имени (например 'no_photo', 'placeholder' и т.п.)
PLACEHOLDER_HINTS = ("placeholder", "no_photo", "no-photo", "nophoto", "stub")


@dataclass
class EngineItem:
    source: str
    source_url: str
    product_id: Optional[int]
    title: Optional[str]
    make: Optional[str]
    model: Optional[str]
    year: Optional[str]
    engine_code: Optional[str]
    engine_type: Optional[str]  # можно будет вывести позже (petrol/diesel/unknown)
    price: Optional[int]        # в рублях, если указано цифрами
    currency: str
    stock_text: Optional[str]
    oem: Optional[str]
    description: Optional[str]
    images: List[str]


def clean_int(s: str) -> Optional[int]:
    s = s.replace(" ", "").replace("\xa0", "")
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else None


def guess_engine_type(engine_code: Optional[str], title: Optional[str]) -> Optional[str]:
    # Заглушка: у mysakura тип топлива не всегда явно есть.
    # Позже можно расширить правилами (по словам "дизель", "diesel", "d4d" и т.п.)
    text = f"{engine_code or ''} {title or ''}".lower()
    if "диз" in text or "diesel" in text:
        return "diesel"
    if "бенз" in text or "petrol" in text:
        return "petrol"
    return "unknown"


async def fetch_text(client: httpx.AsyncClient, url: str) -> str:
    r = await client.get(url, follow_redirects=True)
    r.raise_for_status()
    return r.text


def extract_product_links(html: str) -> Set[str]:
    soup = BeautifulSoup(html, "lxml")
    links: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if PRODUCT_URL_RE.match(href):
            links.add(urljoin(BASE, href))
    return links


def extract_pagination_links(html: str) -> Set[str]:
    # Вариант попроще: собираем все ссылки каталога с ?page=
    soup = BeautifulSoup(html, "lxml")
    pages: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(CATALOG_PATH) and "page=" in href:
            pages.add(urljoin(BASE, href))
    return pages


def extract_field_from_specs(soup: BeautifulSoup, label_ru: str) -> Optional[str]:
    """
    На карточке есть блок 'Характеристики товара' и далее пары:
    'Марка:' -> 'Audi', 'Модель:' -> 'A6', 'Год:' -> '03.2011', ...
    Мы ищем текст метки и берем ближайшее "значение" рядом в DOM.
    """
    label = label_ru.strip().rstrip(":")
    # Находим элемент, где встречается 'Марка:' как текст
    node = soup.find(string=re.compile(rf"^{re.escape(label)}\s*:\s*$"))
    if not node:
        # иногда может быть без двоеточия в узле — подстраховка
        node = soup.find(string=re.compile(rf"^{re.escape(label)}\s*:?$"))
    if not node:
        return None

    # Часто значение идет в следующем элементе
    el = node.parent
    # пробуем next elements
    for _ in range(10):
        el = el.find_next()
        if el and el.get_text(strip=True):
            val = el.get_text(" ", strip=True)
            # отсекаем если случайно снова метка
            if val.endswith(":"):
                continue
            return val
    return None


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(" ", strip=True)
    return None


def extract_description(soup: BeautifulSoup) -> Optional[str]:
    # На карточке перед табами/комментарием есть большой текст (пробег/комплектность)
    # Берем первый крупный текстовый блок после заголовка — эвристика:
    text = soup.get_text("\n", strip=True)
    # ограничим до разумного: ищем строку со словом "Пробег" как в примере
    m = re.search(r"(Пробег.*?)(?:Характеристики товара|Отзывы о товаре|##|$)", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def extract_price(soup: BeautifulSoup) -> Optional[int]:
    text = soup.get_text(" ", strip=True)
    # На карточке встречается цена "120 000" и "120000" рядом :contentReference[oaicite:8]{index=8}
    # Возьмем первую "разумную" цену: 4-7 цифр
    m = re.search(r"\b(\d[\d \xa0]{2,}\d)\b", text)
    if not m:
        return None
    return clean_int(m.group(1))


def extract_product_id(url: str) -> Optional[int]:
    m = re.search(r"/product/(\d+)", url)
    return int(m.group(1)) if m else None


def _add_from_srcset(urls: set[str], srcset: str):
    # srcset: "url1 1x, url2 2x"
    for part in srcset.split(","):
        u = part.strip().split(" ")[0]
        if u:
            urls.add(u)

def extract_images_from_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")

    # 1) Вырезаем блоки, где точно НЕ фото текущего товара
    # (в твоём HTML был slider_additional_parts — это “вам может понадобиться”)
    for bad in soup.select(".slider_additional_parts, .additional_parts, .product__wrapper .row.slider_additional_parts"):
        bad.decompose()

    urls: set[str] = set()

    # 2) Собираем кандидаты из img-тегов
    for img in soup.find_all("img"):
        for attr in ("src", "data-src", "data-original", "data-lazy", "data-srcset"):
            v = img.get(attr)
            if not v:
                continue
            v = str(v).strip()
            if attr in ("data-srcset",):
                _add_from_srcset(urls, v)
            else:
                urls.add(v)

        srcset = img.get("srcset")
        if srcset:
            _add_from_srcset(urls, str(srcset))

    # 3) Фильтрация: берём только mysakura в yandexcloud + форматы картинок + убираем заглушки
    clean = []
    for u in urls:
        if not u.startswith(YACLOUD_PREFIX):
            continue
        if not IMG_EXT_RE.search(u):
            continue
        low = u.lower()
        if any(h in low for h in PLACEHOLDER_HINTS):
            continue
        clean.append(u)

    # 4) Стабильный порядок
    clean = sorted(set(clean))
    return clean


async def scrape_product(client: httpx.AsyncClient, url: str) -> EngineItem:
    html = await fetch_text(client, url)
    soup = BeautifulSoup(html, "lxml")

    title = extract_title(soup)

    make = extract_field_from_specs(soup, "Марка")
    model = extract_field_from_specs(soup, "Модель")
    year = extract_field_from_specs(soup, "Год")
    engine_code = extract_field_from_specs(soup, "Двигатель")
    oem = extract_field_from_specs(soup, "OEM")
    stock_text = extract_field_from_specs(soup, "Наличие")

    description = extract_description(soup)
    price = extract_price(soup)

    images = extract_images_from_html(html)

    return EngineItem(
        source="mysakura",
        source_url=url,
        product_id=extract_product_id(url),
        title=title,
        make=make,
        model=model,
        year=year,
        engine_code=engine_code,
        engine_type=guess_engine_type(engine_code, title),
        price=price,
        currency="RUB",
        stock_text=stock_text,
        oem=oem,
        description=description,
        images=images,
    )


async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (educational scraper; contact: you@example.com)"
    }

    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        # 1) собираем все страницы пагинации (BFS)
        to_visit = [CATALOG_URL]
        visited_pages: Set[str] = set()

        product_links: Set[str] = set()

        while to_visit:
            page_url = to_visit.pop()
            if page_url in visited_pages:
                continue
            visited_pages.add(page_url)

            html = await fetch_text(client, page_url)

            product_links |= extract_product_links(html)
            new_pages = extract_pagination_links(html)

            for p in new_pages:
                if p not in visited_pages:
                    to_visit.append(p)

            await asyncio.sleep(random.uniform(0.6, 1.2))  # бережно

        print(f"Found products: {len(product_links)}")
        links_sorted = sorted(product_links)

        # 2) парсим карточки (по очереди — надежнее)
        results: List[Dict] = []
        for i, url in enumerate(links_sorted, 1):
            try:
                item = await scrape_product(client, url)
                results.append(asdict(item))
                print(f"[{i}/{len(links_sorted)}] OK {url}")
            except Exception as e:
                print(f"[{i}/{len(links_sorted)}] FAIL {url}: {e}")

            await asyncio.sleep(random.uniform(0.8, 1.5))

        with open("engines_mysakura_new.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("Saved: engines_mysakura_new.json")


if __name__ == "__main__":
    asyncio.run(main())
