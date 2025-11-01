#!/usr/bin/env python3
"""
カレンダーの日付情報を取得
"""
import asyncio
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))
from src.config import get_target_url

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = get_target_url()
        print(f"ページ読み込み中: {url}\n")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # ページタイトルやヘッダーから日付を取得
        title = await page.title()
        print(f"ページタイトル: {title}")
        
        # カレンダーのヘッダー部分を探す
        headers = await page.query_selector_all('h1, h2, h3, .calendar-header, [class*="header"]')
        print(f"\nヘッダー要素数: {len(headers)}")
        for header in headers[:10]:
            text = await header.inner_text()
            if text.strip():
                print(f"  - {text.strip()[:100]}")
        
        # 日付を含むテキストを探す
        all_text = await page.evaluate('() => document.body.innerText')
        
        # 日付パターンを探す（例: 2025年10月27日、10/27など）
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{1,2})/(\d{1,2})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
        ]
        
        print("\n日付パターン検索:")
        for pattern in date_patterns:
            matches = re.findall(pattern, all_text[:1000])
            if matches:
                print(f"  パターン {pattern}: {matches[:5]}")
        
        # 週の開始日を探す（カレンダーの最初の日）
        # Airリザーブは週表示なので、週の開始日がどこかにあるはず
        week_info = await page.query_selector('.weekInfo, .calendar-week, [class*="week"]')
        if week_info:
            text = await week_info.inner_text()
            print(f"\n週情報: {text}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())

