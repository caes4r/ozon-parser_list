import asyncio
import json
import sys
from datetime import datetime
from playwright.async_api import async_playwright

async def get_position(query: str, sku: str, max_positions: int = 100):
    positions_checked = 0
    page_num = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        try:
            while positions_checked < max_positions:
                url = f"https://www.ozon.ru/search/?text={query}&page={page_num}"
                await page.goto(url, wait_until='networkidle')
                await asyncio.sleep(2)  # небольшая задержка

                # Ищем карточки товаров по атрибуту data-sku
                cards = await page.query_selector_all('div[data-sku]')
                if not cards:
                    # запасной вариант: возможно, карточки в a[data-sku]
                    cards = await page.query_selector_all('a[data-sku]')

                for card in cards:
                    positions_checked += 1
                    sku_attr = await card.get_attribute('data-sku')
                    if sku_attr == str(sku):
                        return {
                            "query": query,
                            "sku": sku,
                            "position": positions_checked,
                            "page": page_num,
                            "total_checked": positions_checked,
                            "timestamp": datetime.now().isoformat()
                        }

                # Проверяем наличие следующей страницы
                next_button = await page.query_selector('a[rel="next"]')
                if not next_button:
                    break
                page_num += 1

            # Если не нашли
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