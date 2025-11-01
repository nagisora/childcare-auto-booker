#!/usr/bin/env python3
"""
イベント日時の抽出テスト
"""
import asyncio
import re
import sys
from datetime import datetime, timedelta
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
        
        # 週表示のヘッダーから日付を取得
        week_headers = await page.query_selector_all('.weekHeader, [class*="weekHeader"], .calendarWeek th')
        print(f"週ヘッダー要素数: {len(week_headers)}")
        
        # カレンダーの日付セルを確認
        date_cells = await page.query_selector_all('td[data-date], .calendarDate, [class*="date"]')
        print(f"日付セル数: {len(date_cells)}")
        
        # イベント要素の親要素を確認
        elements = await page.query_selector_all('.dataLinkBox.js-dataLinkBox')
        print(f"\nイベント要素数: {len(elements)}\n")
        
        for i, elem in enumerate(elements[:3]):
            text = await elem.inner_text()
            print(f"=== イベント {i+1} ===")
            print(f"テキスト: {text[:50].replace(chr(10), ' ')}")
            
            # 親要素の情報を取得
            parent = await elem.evaluate_handle('el => el.parentElement')
            parent_class = await parent.evaluate('el => el.className')
            parent_tag = await parent.evaluate('el => el.tagName')
            print(f"親要素: <{parent_tag}> class=\"{parent_class}\"")
            
            # data-date属性を探す
            td_parent = await elem.evaluate_handle('el => el.closest("td")')
            if td_parent:
                data_date = await td_parent.evaluate('el => el.getAttribute("data-date")')
                print(f"data-date: {data_date}")
            
            # 時刻を抽出
            time_match = re.search(r'(\d{1,2}):(\d{2})', text)
            if time_match:
                hour, minute = time_match.groups()
                print(f"時刻: {hour}:{minute}")
            
            print()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())

