import asyncio
import json
import sys
import re
import random
from datetime import datetime
from playwright.async_api import async_playwright

USER_AGENTS = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
]

async def get_position(query: str, sku: str, max_positions: int = 100):
    positions_checked = 0
    page_num = 1
    retries = 2

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

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

                await asyncio.sleep(random.uniform(2, 4))

                # Проверка на капчу
                title = await page.title()
                if 'Antibot' in title or 'Доступ ограничен' in title:
                    print("Капча, ждём 30 сек", file=sys.stderr)
                    await asyncio.sleep(30)
                    continue

                try:
                    await page.wait_for_selector('a[href*="/product/"]', timeout=5000)
                except:
                    break

                product_links = await page.query_selector_all('a[href*="/product/"]')
                if not product_links:
                    break

                # --- Отладка: выводим первые 10 ссылок и артикулы ---
                print("=== DEBUG: первые 10 ссылок ===", file=sys.stderr)
                for i, link in enumerate(product_links[:10]):
                    href = await link.get_attribute('href')
                    match = re.search(r'/product/(\d+)', href)
                    art = match.group(1) if match else "N/A"
                    print(f"{i+1}. {href} -> артикул: {art}", file=sys.stderr)
                print("=== END DEBUG ===", file=sys.stderr)
                # --------------------------------------------------

                for link in product_links:
                    if positions_checked >= max_positions:
                        break
                    positions_checked += 1
                    href = await link.get_attribute('href')
                    match = re.search(r'/product/(\d+)', href)
                    if match and match.group(1) == str(sku):
                        return {
                            "query": query,
                            "sku": sku,
                            "position": positions_checked,
                            "page": page_num,
                            "total_checked": positions_checked,
                            "timestamp": datetime.now().isoformat()
                        }

                page_num += 1
                await asyncio.sleep(random.uniform(3, 6))

            return {
                "query": query,
                "sku": sku,
                "position": "not_found",
                "page": None,
                "total_checked": positions_checked,
                "timestamp": datetime.now().isoformat()
            }

        finally:
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