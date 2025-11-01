#!/usr/bin/env python3
"""
14日前チェックのテスト
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
        
        now = datetime.now()
        
        # 週情報を取得（class="ctlListItem listDate"）
        week_info_elems = await page.query_selector_all('.ctlListItem.listDate')
        print(f"週情報要素数: {len(week_info_elems)}")
        
        if week_info_elems and len(week_info_elems) > 0:
            first_elem = week_info_elems[0]
            week_text = await first_elem.inner_text()
            print(f"週情報: {week_text}")
            
            # 日付を抽出（例: "2025/10/27(月)"）
            match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', week_text)
            if match:
                year, month, day = map(int, match.groups())
                week_date = datetime(year, month, day)
            else:
                # 年なしの場合
                match = re.search(r'(\d{1,2})/(\d{1,2})', week_text)
                if match:
                    month, day = map(int, match.groups())
                    year = now.year
                    week_date = datetime(year, month, day)
                    
                    if week_date < now - timedelta(days=30):
                        week_date = datetime(year + 1, month, day)
                else:
                    week_date = None
            
            if week_date:
                print(f"\n週開始日: {week_date.strftime('%Y-%m-%d')}")
                
                # 14日前チェック
                days_until = (week_date - now).days
                print(f"今日から{days_until}日後")
                print(f"14日以内: {days_until <= 14}")
        else:
            print("週情報が見つかりません")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())

