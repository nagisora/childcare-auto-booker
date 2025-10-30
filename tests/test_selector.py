#!/usr/bin/env python3
"""
セレクターテスト用スクリプト
"""
import asyncio
from playwright.async_api import async_playwright

async def test_selectors():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # ページ読み込み
        url = "https://airrsv.net/platkokoro2020/calendar"
        print(f"ページ読み込み中: {url}")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # ページタイトル
        title = await page.title()
        print(f"ページタイトル: {title}")
        
        # スクリーンショット
        await page.screenshot(path="screenshots/test_selector.png", full_page=True)
        print("スクリーンショット保存: screenshots/test_selector.png")
        
        # セレクターテスト
        selectors_to_test = [
            '.dataLinkBox.js-dataLinkBox',
            '.dataLinkBox',
            '.js-dataLinkBox',
            '[class*="dataLinkBox"]',
            '[class*="LinkBox"]',
            '.ctlListItem.listNext',
        ]
        
        for selector in selectors_to_test:
            elements = await page.query_selector_all(selector)
            print(f"{selector}: {len(elements)} 個の要素")
            
            if len(elements) > 0 and len(elements) <= 3:
                for i, elem in enumerate(elements[:3]):
                    text = await elem.inner_text()
                    print(f"  [{i}] テキスト: {text[:50]}")
        
        # 全リンクを確認
        all_links = await page.query_selector_all('a')
        print(f"\n全リンク数: {len(all_links)}")
        
        # 「残」「仮」を含むテキストを検索
        for link in all_links[:20]:  # 最初の20個だけ
            text = await link.inner_text()
            if '残' in text or '仮' in text or '待' in text:
                href = await link.get_attribute('href')
                print(f"  予約関連リンク: {text.strip()} -> {href}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_selectors())

