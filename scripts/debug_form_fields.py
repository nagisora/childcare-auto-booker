#!/usr/bin/env python3
"""
デバッグ用: フォーム入力ページのフィールド構造を詳細に調査
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

sys.path.append(str(Path(__file__).parent.parent))
from src.scraper import AirReserveScraper
from src.booker import AirReserveBooker


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def debug_form_fields():
    """フォーム入力ページのフィールドを詳細調査"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    load_dotenv()
    
    os.environ["TEST_SITE_MODE"] = "true"
    os.environ["HEADLESS"] = "false"
    os.environ["DEBUG"] = "true"
    
    scraper = AirReserveScraper()
    scraper.target_url = "https://airrsv.net/platkokoro2020/calendar"
    scraper.test_site_mode = True
    scraper.headless = False
    scraper.debug = True
    
    async with scraper:
        try:
            if not await scraper.load_calendar_page():
                logger.error("カレンダーページの読み込みに失敗")
                return
            
            # 予約可能枠を取得
            available_slots = await scraper.get_available_slots(max_weeks=2)
            logger.info(f"{len(available_slots)}件の枠を発見")
            
            if not available_slots:
                logger.error("予約可能枠が見つかりません")
                return
            
            # 残0枠を探す（フォーム入力テスト用）
            target_slot = None
            for slot in available_slots:
                if '残0' in slot['text']:
                    target_slot = slot
                    logger.info(f"調査対象: {slot['text'][:50]}")
                    break
            
            if not target_slot:
                logger.error("残0枠が見つかりません")
                return
            
            # 予約ページに移動
            booker = AirReserveBooker()
            
            # 週番号から該当週へ移動
            week_number = target_slot.get('week_number')
            if week_number:
                logger.info(f"週{week_number}に移動します...")
                await scraper.page.goto(scraper.target_url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(1)
                
                for i in range(week_number - 1):
                    next_button = await scraper.page.query_selector('.ctlListItem.listNext')
                    if next_button:
                        await next_button.click()
                        await asyncio.sleep(0.5)
            
            # dataLinkBox要素をクリック
            display_text = target_slot['href'].replace('dataLinkBox:', '').strip()
            logger.info(f"dataLinkBox要素をクリック: {display_text[:50]}...")
            
            elements = await scraper.page.query_selector_all('.dataLinkBox.js-dataLinkBox')
            for element in elements:
                element_text = await element.inner_text()
                if display_text in element_text or element_text in display_text:
                    await element.click()
                    await asyncio.sleep(2)
                    break
            
            # メニュー選択とフォーム送信
            await booker._select_menu(scraper.page)
            await asyncio.sleep(1)
            await booker._submit_menu_detail_form(scraper.page)
            await asyncio.sleep(2)
            
            # フォーム入力ページのフィールド構造を詳細に取得
            logger.info("=" * 80)
            logger.info("フォーム入力ページのフィールド構造を調査中...")
            logger.info("=" * 80)
            
            form_data = await scraper.page.evaluate('''() => {
                const result = [];
                
                // すべての入力フィールドを取得
                const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], select, textarea');
                inputs.forEach((input) => {
                    const info = {
                        type: input.type,
                        tag: input.tagName,
                        name: input.name || '',
                        id: input.id || '',
                        placeholder: input.placeholder || '',
                        value: input.value || ''
                    };
                    
                    // ラベルを取得
                    if (input.id) {
                        const label = document.querySelector(`label[for="${input.id}"]`);
                        if (label) {
                            info.label = label.innerText.trim();
                        }
                    }
                    
                    if (!info.label) {
                        let parent = input.parentElement;
                        while (parent && parent.tagName !== 'BODY') {
                            const labelInParent = parent.querySelector('label');
                            if (labelInParent) {
                                info.label = labelInParent.innerText.trim();
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                    
                    // セレクトボックスの選択肢
                    if (input.tagName === 'SELECT') {
                        info.options = [];
                        input.querySelectorAll('option').forEach((option) => {
                            info.options.push({
                                value: option.value,
                                text: option.innerText.trim()
                            });
                        });
                    }
                    
                    result.push(info);
                });
                
                return result;
            }''')
            
            logger.info("\nフィールド一覧:")
            for idx, field in enumerate(form_data, 1):
                logger.info(f"\n[{idx}] {field['tag']} - type={field['type']}")
                logger.info(f"    name='{field['name']}'")
                logger.info(f"    id='{field['id']}'")
                logger.info(f"    placeholder='{field['placeholder']}'")
                logger.info(f"    label='{field.get('label', 'N/A')}'")
                if 'options' in field:
                    logger.info(f"    options={len(field['options'])}個")
                    for opt in field['options'][:5]:
                        logger.info(f"        - value='{opt['value']}', text='{opt['text']}'")
            
            # 結果を保存
            output_file = Path("docs/debug_form_fields.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(form_data, f, ensure_ascii=False, indent=2)
            logger.info(f"\n結果を保存しました: {output_file}")
            
            # スクリーンショット
            screenshot_path = f"screenshots/debug_form_{Path().cwd().name}_form.png"
            await scraper.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"スクリーンショット: {screenshot_path}")
            
            logger.info("\n30秒待機します...")
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"エラー: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(debug_form_fields())

