import asyncio
import sys
from playwright.async_api import async_playwright

async def main():
    if len(sys.argv) != 3:
        print("Usage: python parser.py <query> <sku>")
        sys.exit(1)

    query = sys.argv[1]
    sku = sys.argv[2]

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

        url = f"https://www.ozon.ru/search/?text={query}"
        print(f"Открываем: {url}")
        await page.goto(url, wait_until='networkidle')

        title = await page.title()
        print(f"Заголовок страницы: {title}")

        await asyncio.sleep(2)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())