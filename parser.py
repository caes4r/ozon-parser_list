import asyncio
import json
import sys
import re
import random
import os
from datetime import datetime
from playwright.async_api import async_playwright

USER_AGENTS = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
]

COOKIES_FILE = 'cookies.json'

async def get_position(query: str, sku: str, max_positions: int = 100):
    positions_checked = 0
    page_num = 1
    retries = 2

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # для скринкаста оставляем False
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
            ]
        )

        headers = {
            'Accept-Language': random.choice(['ru-RU,ru;q=0.9', 'ru;q=0.8,en;q=0.7', 'en-US,en;q=0.9']),
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': random.choice(['https://www.google.com/', 'https://yandex.ru/', '']),
            'DNT': '1',
        }

        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1280, 'height': 800},
            extra_http_headers=headers,
            locale='ru-RU',
            timezone_id='Europe/Moscow',
            color_scheme='light',
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False,
        )

        # Загрузка cookies
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)

        page = await context.new_page()

        # Ручная маскировка признаков автоматизации
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru'] });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        """)

        try:
            while positions_checked < max_positions:
                url = f"https://www.ozon.ru/search/?text={query}&page={page_num}"
                for attempt in range(retries):
                    try:
                        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                        break
                    except Exception as e:
                        if attempt == retries - 1:
                            raise
                        await asyncio.sleep(2 ** attempt)

                await asyncio.sleep(random.uniform(3, 6))

                title = await page.title()
                if 'Antibot' in title or 'Доступ ограничен' in title:
                    return {
                        "query": query,
                        "sku": sku,
                        "position": "captcha",
                        "page": page_num,
                        "total_checked": positions_checked,
                        "timestamp": datetime.now().isoformat()
                    }

                try:
                    await page.wait_for_selector('a[href*="/product/"]', timeout=5000)
                except:
                    break

                product_links = await page.query_selector_all('a[href*="/product/"]')
                if not product_links:
                    break

                for link in product_links:
                    if positions_checked >= max_positions:
                        break
                    positions_checked += 1
                    href = await link.get_attribute('href')
                    match = re.search(r'/(\d+)/\?', href)
                    if match:
                        art = match.group(1)
                    else:
                        digits = re.findall(r'\d+', href)
                        art = digits[0] if digits else None
                    if art and art == str(sku):
                        return {
                            "query": query,
                            "sku": sku,
                            "position": positions_checked,
                            "page": page_num,
                            "total_checked": positions_checked,
                            "timestamp": datetime.now().isoformat()
                        }

                page_num += 1
                await asyncio.sleep(random.uniform(5, 10))

            return {
                "query": query,
                "sku": sku,
                "position": "not_found",
                "page": None,
                "total_checked": positions_checked,
                "timestamp": datetime.now().isoformat()
            }

        finally:
            cookies = await context.cookies()
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f)
            await browser.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python parser.py <query> <sku>")
        sys.exit(1)

    query = sys.argv[1]
    sku = sys.argv[2]

    result = asyncio.run(get_position(query, sku))
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()