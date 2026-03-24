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
        # Запускаем браузер в headless-режиме
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Формируем URL для первой страницы поиска
        url = f"https://www.ozon.ru/search/?text={query}"
        print(f"Открываем: {url}")
        await page.goto(url, wait_until="networkidle")

        # Выводим заголовок страницы для проверки
        title = await page.title()
        print(f"Заголовок страницы: {title}")

        # Небольшая пауза, чтобы убедиться, что всё загрузилось
        await asyncio.sleep(2)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
