#!/usr/bin/env python3
"""
Airリザーブ予約フォームフィールド調査スクリプト

本番サイトのサンプルURLを使用してフォームフィールドを調査
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


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def inspect_booking_form_fields():
    """予約フォームのフィールドを調査"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    load_dotenv()
    
    # 本番サイトのサンプルURL（確認画面に直接アクセス）
    # 実際のURLは手動で取得したもの
    test_urls = [
        # テストサイトの予約受付期間外の枠を使う場合
        "https://airrsv.net/platkokoro2020/calendar",
        # 本番サイトのサンプル（必要な場合）
        "https://airrsv.net/kokoroto-azukari/calendar",
    ]
    
    logger.info("予約フォームフィールドの調査を開始します")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # カレンダーページを読み込む
            logger.info(f"カレンダーページを読み込み中: {test_urls[0]}")
            await page.goto(test_urls[0], wait_until="networkidle", timeout=30000)
            
            # 詳細なフォーム構造を取得するため、すべてのinput要素を調査
            logger.info("ページ内のすべてのinput要素を調査中...")
            
            # JavaScriptでフォーム構造を詳細に取得
            form_elements = await page.evaluate('''() => {
                const result = {
                    visible_inputs: [],
                    hidden_inputs: [],
                    selects: [],
                    buttons: []
                };
                
                // すべてのinput要素を取得
                const inputs = document.querySelectorAll('input');
                inputs.forEach((input, idx) => {
                    const info = {
                        index: idx,
                        tag: input.tagName,
                        type: input.type,
                        name: input.name,
                        id: input.id,
                        class: input.className,
                        placeholder: input.placeholder,
                        value: input.value,
                        required: input.required
                    };
                    
                    // ラベルを取得
                    if (input.id) {
                        const label = document.querySelector(`label[for="${input.id}"]`);
                        if (label) {
                            info.label = label.innerText.trim();
                        }
                    }
                    
                    // 親要素内のラベルを探す
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
                    
                    if (input.type === 'hidden') {
                        result.hidden_inputs.push(info);
                    } else {
                        result.visible_inputs.push(info);
                    }
                });
                
                // すべてのselect要素を取得
                const selects = document.querySelectorAll('select');
                selects.forEach((select, idx) => {
                    const info = {
                        index: idx,
                        tag: select.tagName,
                        name: select.name,
                        id: select.id,
                        class: select.className,
                        options: []
                    };
                    
                    select.querySelectorAll('option').forEach((option) => {
                        info.options.push({
                            value: option.value,
                            text: option.innerText.trim()
                        });
                    });
                    
                    // ラベルを取得
                    if (select.id) {
                        const label = document.querySelector(`label[for="${select.id}"]`);
                        if (label) {
                            info.label = label.innerText.trim();
                        }
                    }
                    
                    result.selects.push(info);
                });
                
                // すべてのbutton要素を取得
                const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"]');
                buttons.forEach((btn, idx) => {
                    result.buttons.push({
                        index: idx,
                        tag: btn.tagName,
                        type: btn.type,
                        id: btn.id,
                        class: btn.className,
                        text: btn.innerText.trim(),
                        value: btn.value || ''
                    });
                });
                
                return result;
            }''')
            
            logger.info("=" * 80)
            logger.info("可視フィールド (visible_inputs)")
            logger.info("=" * 80)
            for inp in form_elements['visible_inputs']:
                logger.info(f"  [{inp['index']}] type={inp['type']}, name='{inp['name']}', id='{inp['id']}', label='{inp.get('label', 'N/A')}'")
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("セレクトボックス (selects)")
            logger.info("=" * 80)
            for sel in form_elements['selects']:
                logger.info(f"  [{sel['index']}] name='{sel['name']}', id='{sel['id']}', label='{sel.get('label', 'N/A')}', options={len(sel['options'])}")
                for opt in sel['options'][:5]:  # 最初の5つだけ表示
                    logger.info(f"      - value='{opt['value']}', text='{opt['text']}'")
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("ボタン (buttons)")
            logger.info("=" * 80)
            for btn in form_elements['buttons']:
                logger.info(f"  [{btn['index']}] type={btn['type']}, id='{btn['id']}', text='{btn['text']}'")
            
            # 結果をJSONファイルに保存
            output_file = Path("docs/booking_form_fields.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(form_elements, f, ensure_ascii=False, indent=2)
            
            logger.info("")
            logger.info(f"調査結果を保存しました: {output_file}")
            logger.info("30秒待機します（ブラウザを確認してください）")
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"調査中にエラーが発生: {e}", exc_info=True)
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_booking_form_fields())

