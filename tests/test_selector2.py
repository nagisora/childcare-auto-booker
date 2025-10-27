#!/usr/bin/env python3
"""
セレクターと判定ロジックのテスト
"""
import asyncio
from playwright.async_api import async_playwright

def is_available_slot(text: str, href: str) -> bool:
    """予約可能枠かどうかを判定（テスト用）"""
    if not text or not href:
        return False
        
    exclude_keywords = [
        '満員', '満', '受付終了', '終了', 'disabled', 'unavailable',
        '予約不可', '不可', 'close', 'closed', '残0'
    ]
    
    text_lower = text.lower()
    for keyword in exclude_keywords:
        if keyword in text_lower:
            return False
            
    include_keywords = [
        '残', '仮', 'available', '予約可能', '可能', '受付中', '待'
    ]
    
    for keyword in include_keywords:
        if keyword in text_lower:
            return True
            
    return False

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://airrsv.net/platkokoro2020/calendar"
        print(f"ページ読み込み中: {url}\n")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # 7週分チェック
        all_slots = []
        for week in range(7):
            print(f"=== 週 {week + 1}/7 ===")
            
            selector = '.dataLinkBox.js-dataLinkBox'
            elements = await page.query_selector_all(selector)
            print(f"要素数: {len(elements)}")
            
            for elem in elements:
                text = await elem.inner_text()
                link_elem = await elem.query_selector('a')
                href = await link_elem.get_attribute('href') if link_elem else None
                
                available = is_available_slot(text, href)
                status = "✓ 予約可能" if available else "✗ 予約不可"
                
                print(f"{status}: {text[:60].replace(chr(10), ' ')}")
                if href:
                    print(f"  URL: {href}")
                
                if available:
                    all_slots.append({'text': text, 'href': href, 'week': week + 1})
            
            # 次週へ
            if week < 6:
                next_button = await page.query_selector('.ctlListItem.listNext')
                if next_button:
                    await next_button.click()
                    await asyncio.sleep(0.5)
                else:
                    print("次週ボタンなし")
                    break
            print()
        
        print(f"\n=== 結果 ===")
        print(f"合計予約可能枠: {len(all_slots)} 件")
        for slot in all_slots:
            print(f"  週{slot['week']}: {slot['text'][:40].replace(chr(10), ' ')}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())

