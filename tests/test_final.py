#!/usr/bin/env python3
"""
最終テスト: 修正後の判定ロジック確認
"""
import asyncio
from playwright.async_api import async_playwright

def is_available_slot(text: str, href: str) -> bool:
    """予約可能枠かどうかを判定（修正版）"""
    if not text or not href:
        return False
    
    text_lower = text.lower()
    
    # LINE予約は除外
    if 'line予約' in text_lower or 'ここはline' in text_lower:
        return False
    
    # 残0は除外
    if '残0' in text_lower:
        return False
        
    exclude_keywords = [
        '満員', '受付終了', '終了', 'disabled', 'unavailable',
        '予約不可', '不可', 'close', 'closed'
    ]
    
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
        
        all_slots = []
        for week in range(7):
            print(f"=== 週 {week + 1}/7 ===")
            
            elements = await page.query_selector_all('.dataLinkBox.js-dataLinkBox')
            print(f"要素数: {len(elements)}")
            
            for elem in elements:
                text = await elem.inner_text()
                link_elem = await elem.query_selector('a')
                href = await link_elem.get_attribute('href') if link_elem else None
                
                available = is_available_slot(text, href)
                status = "✓ 予約可能" if available else "✗ 予約不可"
                
                # テキストを1行にまとめて表示
                display_text = text[:70].replace('\n', ' ')
                print(f"{status}: {display_text}")
                
                if available:
                    all_slots.append({'text': text, 'href': href, 'week': week + 1})
            
            if week < 6:
                next_button = await page.query_selector('.ctlListItem.listNext')
                if next_button:
                    await next_button.click()
                    await asyncio.sleep(0.5)
                else:
                    break
            print()
        
        print(f"\n{'='*60}")
        print(f"合計予約可能枠: {len(all_slots)} 件")
        print(f"{'='*60}")
        for slot in all_slots:
            display_text = slot['text'][:50].replace('\n', ' ')
            print(f"  週{slot['week']}: {display_text}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())

