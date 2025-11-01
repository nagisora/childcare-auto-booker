#!/usr/bin/env python3
"""
Airリザーブフォーム構造調査スクリプト

テストサイトで実際のフォーム構造を調査し、フィールド名、ID、セレクターを特定する
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from playwright.async_api import async_playwright

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.scraper import AirReserveScraper
from src.booker import AirReserveBooker


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def inspect_form_structure():
    """フォーム構造を調査"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 環境変数読み込み
    load_dotenv()
    
    # テストサイトモードを有効化
    os.environ["TEST_SITE_MODE"] = "true"
    os.environ["HEADLESS"] = "false"  # ブラウザを表示
    os.environ["DEBUG"] = "true"
    
    # テストサイトのURL
    test_url = "https://airrsv.net/platkokoro2020/calendar"
    
    logger.info("フォーム構造の調査を開始します")
    logger.info(f"テストサイトURL: {test_url}")
    
    scraper = AirReserveScraper()
    scraper.target_url = test_url
    scraper.test_site_mode = True
    scraper.headless = False
    scraper.debug = True
    
    async with scraper:
        try:
            # カレンダーページを読み込み
            if not await scraper.load_calendar_page():
                logger.error("カレンダーページの読み込みに失敗しました")
                return
            
            # 予約可能枠を取得
            logger.info("予約可能枠を検索中...")
            available_slots = await scraper.get_available_slots(max_weeks=1)
            
            skip_navigation = False  # ページ遷移をスキップするフラグ
            
            # 予約可能枠が見つからない場合、すべての枠（予約期間外も含む）を取得
            if not available_slots:
                logger.warning("予約可能枠が見つかりませんでした")
                logger.info("すべての枠を検索します（予約期間外も含む）...")
                
                # すべてのdataLinkBox要素を取得
                all_elements = await scraper.page.query_selector_all('.dataLinkBox.js-dataLinkBox')
                logger.info(f"{len(all_elements)}件のイベント要素を発見")
                
                if not all_elements:
                    logger.error("イベント要素が見つかりませんでした")
                    return
                
                # 最初の要素からリンクを取得
                first_element = all_elements[0]
                
                # リンク要素を探す（複数の方法を試行）
                link_element = await first_element.query_selector('a')
                
                # aタグがない場合、dataLinkBox要素自体がクリック可能か確認
                if not link_element:
                    # dataLinkBox要素自体にhref属性があるか確認
                    href = await first_element.get_attribute('href')
                    if not href:
                        # data属性を確認
                        data_href = await first_element.get_attribute('data-href')
                        if data_href:
                            href = data_href
                        else:
                            # onclick属性を確認
                            onclick = await first_element.get_attribute('onclick')
                            if onclick and 'href' in onclick:
                                # onclickからURLを抽出（簡易版）
                                import re
                                match = re.search(r"['\"]([^'\"]+)['\"]", onclick)
                                if match:
                                    href = match.group(1)
                    
                    if not href:
                        # JavaScriptでクリックイベントを取得してURLを特定
                        logger.info("リンク要素が見つかりません。JavaScriptでURLを取得します...")
                        try:
                            # dataLinkBox要素のクリックイベントハンドラからURLを取得
                            click_handler = await first_element.evaluate('''el => {
                                // クリックイベントをシミュレートしてURLを取得
                                // またはdata属性からURLを取得
                                if (el.dataset && el.dataset.url) {
                                    return el.dataset.url;
                                }
                                if (el.onclick) {
                                    return el.onclick.toString();
                                }
                                // 親要素を確認
                                let parent = el.parentElement;
                                while (parent) {
                                    if (parent.href) {
                                        return parent.href;
                                    }
                                    if (parent.dataset && parent.dataset.url) {
                                        return parent.dataset.url;
                                    }
                                    parent = parent.parentElement;
                                }
                                return null;
                            }''')
                            
                            if click_handler:
                                href = click_handler
                        except Exception as e:
                            logger.debug(f"JavaScriptでのURL取得に失敗: {e}")
                        
                        if not href:
                            # dataLinkBox要素を直接クリックしてページ遷移を試みる
                            logger.info("dataLinkBox要素を直接クリックしてページ遷移を試みます...")
                            try:
                                # ページ遷移前にすべての属性を取得
                                text = await first_element.inner_text()
                                element_class = await first_element.get_attribute('class')
                                await first_element.click()
                                await asyncio.sleep(2)  # ページ遷移待機
                                current_url = scraper.page.url
                                if current_url != test_url:
                                    href = current_url
                                    logger.info(f"クリック後のURL: {href}")
                                    
                                    # first_slot辞書を作成（ページ遷移後も使える情報のみ）
                                    first_slot = {
                                        'text': text.strip(),
                                        'href': href,
                                        'class': element_class,
                                        'selector': '.dataLinkBox.js-dataLinkBox',
                                        'timestamp': datetime.now(),
                                        'clicked': True  # クリックでページ遷移したことを示すフラグ
                                    }
                                    logger.info(f"調査対象の枠（予約期間外の可能性あり）: {first_slot['text']}")
                                    # クリックでページ遷移したので、既に予約ページにいる
                                    # 後続の処理をスキップして直接フォーム構造調査に進む
                                    skip_navigation = True
                            except Exception as e:
                                logger.error(f"クリックに失敗: {e}")
                                html = await first_element.inner_html()
                                logger.debug(f"要素のHTML: {html[:500]}")
                                return
                else:
                    href = await link_element.get_attribute('href')
                    text = await first_element.inner_text()
                    
                    # 相対URLの場合は絶対URLに変換
                    if href and href.startswith('/'):
                        base_url = test_url.rstrip('/calendar')
                        href = base_url + href
                    
                    # ページ遷移前にすべての属性を取得
                    element_class = await first_element.get_attribute('class')
                    
                    first_slot = {
                        'text': text.strip(),
                        'href': href,
                        'class': element_class,
                        'selector': '.dataLinkBox.js-dataLinkBox',
                        'timestamp': datetime.now()
                    }
                    logger.info(f"調査対象の枠（予約期間外の可能性あり）: {first_slot['text']}")
            else:
                logger.info(f"{len(available_slots)}件の予約可能枠を発見")
                # 最初の予約可能枠を選択
                first_slot = available_slots[0]
            
            # first_slotがまだ定義されていない場合（クリックでページ遷移した場合）
            if 'first_slot' not in locals():
                logger.error("first_slotが定義されていません")
                return
                
            logger.info(f"調査対象の枠: {first_slot['text']}")
            logger.info(f"リンク: {first_slot['href']}")
            
            # 予約ページに移動（クリックで既に移動している場合はスキップ）
            booker = AirReserveBooker()
            skip_navigation = first_slot.get('clicked', False)
            
            if not skip_navigation:
                # hrefが直接URLの場合はgoto、そうでない場合は要素をクリック
                if first_slot.get('href') and first_slot['href'].startswith('http'):
                    # URLが取得できている場合は直接移動
                    logger.info(f"予約ページに移動: {first_slot['href']}")
                    response = await scraper.page.goto(first_slot['href'], wait_until="networkidle", timeout=30000)
                    if not response or response.status != 200:
                        logger.error(f"予約ページ読み込み失敗: {response.status if response else 'No response'}")
                        return
                else:
                    # hrefが取得できていない場合は、dataLinkBox要素を直接クリック
                    logger.info("dataLinkBox要素を直接クリックして予約ページに移動します...")
                    # カレンダーページに戻る必要がある（クリックでページ遷移しているため）
                    await scraper.load_calendar_page()
                    all_elements = await scraper.page.query_selector_all('.dataLinkBox.js-dataLinkBox')
                    if all_elements:
                        await all_elements[0].click()
                        await asyncio.sleep(3)  # ページ遷移待機
                        logger.info(f"クリック後のURL: {scraper.page.url}")
                    else:
                        logger.error("dataLinkBox要素が見つかりませんでした")
                        return
            else:
                logger.info("既に予約ページに移動済みです")
            
            # エラーメッセージのチェック
            is_available = await booker._check_reservation_availability(scraper.page)
            if not is_available:
                logger.warning("この予約枠は予約受付期間外です。フォーム構造の調査は続行します...")
            
            # 各ステップでフォーム構造を調査
            form_structure = {
                'url': scraper.page.url,
                'title': await scraper.page.title(),
                'steps': []
            }
            
            # Step 1: ページ初期状態
            logger.info("=" * 60)
            logger.info("Step 1: 予約ページ初期状態の調査")
            logger.info("=" * 60)
            
            step1 = await inspect_page_structure(scraper.page, "initial")
            form_structure['steps'].append(step1)
            
            # Step 2: メニュー選択後の状態
            logger.info("=" * 60)
            logger.info("Step 2: メニュー選択後の状態の調査")
            logger.info("=" * 60)
            
            menu_selected = await booker._select_menu(scraper.page)
            if menu_selected:
                await asyncio.sleep(2)  # ページ遷移待機
                step2 = await inspect_page_structure(scraper.page, "after_menu_selection")
                form_structure['steps'].append(step2)
            
            # Step 3: 日時選択後の状態
            logger.info("=" * 60)
            logger.info("Step 3: 日時選択後の状態の調査")
            logger.info("=" * 60)
            
            datetime_selected = await booker._select_datetime(scraper.page)
            if datetime_selected:
                await asyncio.sleep(2)  # ページ遷移待機
                step3 = await inspect_page_structure(scraper.page, "after_datetime_selection")
                form_structure['steps'].append(step3)
            
            # Step 4: メニュー詳細フォーム送信
            logger.info("=" * 60)
            logger.info("Step 4: メニュー詳細フォーム送信")
            logger.info("=" * 60)
            
            menu_submitted = await booker._submit_menu_detail_form(scraper.page)
            if menu_submitted:
                logger.info("メニュー詳細フォーム送信成功")
                await asyncio.sleep(2)  # ページ遷移待機
            
            # Step 5: フォーム入力画面の状態
            logger.info("=" * 60)
            logger.info("Step 5: フォーム入力画面の状態の調査")
            logger.info("=" * 60)
            
            step5 = await inspect_page_structure(scraper.page, "form_input")
            form_structure['steps'].append(step5)
            
            # 結果をJSONファイルに保存
            output_file = Path("docs/form_structure_analysis.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(form_structure, f, ensure_ascii=False, indent=2)
            
            logger.info(f"調査結果を保存しました: {output_file}")
            
            # スクリーンショットも保存
            screenshot_path = await scraper.take_screenshot(f"screenshots/form_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            logger.info(f"スクリーンショットを保存しました: {screenshot_path}")
            
            logger.info("フォーム構造の調査が完了しました")
            logger.info("30秒待機します（ブラウザを確認してください）")
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"調査中にエラーが発生: {e}", exc_info=True)


async def inspect_page_structure(page, step_name: str):
    """ページ構造を調査"""
    logger = logging.getLogger(__name__)
    
    structure = {
        'step': step_name,
        'url': page.url,
        'title': await page.title(),
        'forms': [],
        'inputs': [],
        'selects': [],
        'buttons': [],
        'text_content': None
    }
    
    # フォーム要素を取得
    forms = await page.query_selector_all('form')
    for form in forms:
        form_info = {
            'id': await form.get_attribute('id'),
            'name': await form.get_attribute('name'),
            'class': await form.get_attribute('class'),
            'action': await form.get_attribute('action'),
            'method': await form.get_attribute('method'),
        }
        structure['forms'].append(form_info)
    
    # 入力フィールドを取得
    inputs = await page.query_selector_all('input, textarea, select')
    for input_elem in inputs:
        tag_name = await input_elem.evaluate('el => el.tagName')
        input_info = {
            'tag': tag_name,
            'type': await input_elem.get_attribute('type'),
            'name': await input_elem.get_attribute('name'),
            'id': await input_elem.get_attribute('id'),
            'class': await input_elem.get_attribute('class'),
            'placeholder': await input_elem.get_attribute('placeholder'),
            'value': await input_elem.get_attribute('value'),
            'required': await input_elem.get_attribute('required'),
            'visible': await input_elem.is_visible(),
            'enabled': await input_elem.is_enabled(),
        }
        
        # ラベルを取得（複数の方法を試行）
        label_text = None
        
        # 方法1: label[for="id"]で紐付けられている場合
        if input_info['id']:
            label = await page.query_selector(f'label[for="{input_info["id"]}"]')
            if label:
                label_text = await label.inner_text()
        
        # 方法2: 親要素内のlabel要素を探す
        if not label_text:
            try:
                parent = await input_elem.evaluate_handle('el => el.parentElement')
                if parent:
                    label_in_parent = await parent.query_selector('label')
                    if label_in_parent:
                        label_text = await label_in_parent.inner_text()
            except:
                pass
        
        # 方法3: 前の兄弟要素がlabelの場合
        if not label_text:
            try:
                prev_sibling = await input_elem.evaluate_handle('el => el.previousElementSibling')
                if prev_sibling:
                    tag = await prev_sibling.evaluate('el => el.tagName')
                    if tag == 'LABEL':
                        label_text = await prev_sibling.inner_text()
            except:
                pass
        
        if label_text:
            input_info['label'] = label_text.strip()
        
        if tag_name == 'SELECT':
            # 選択肢を取得
            options = await input_elem.query_selector_all('option')
            input_info['options'] = []
            for opt in options:
                input_info['options'].append({
                    'value': await opt.get_attribute('value'),
                    'text': await opt.inner_text(),
                })
            structure['selects'].append(input_info)
        else:
            structure['inputs'].append(input_info)
    
    # ボタンを取得
    buttons = await page.query_selector_all('button, input[type="submit"], input[type="button"]')
    for btn in buttons:
        btn_info = {
            'tag': await btn.evaluate('el => el.tagName'),
            'type': await btn.get_attribute('type'),
            'id': await btn.get_attribute('id'),
            'name': await btn.get_attribute('name'),
            'class': await btn.get_attribute('class'),
            'text': await btn.inner_text(),
            'visible': await btn.is_visible(),
            'enabled': await btn.is_enabled(),
        }
        structure['buttons'].append(btn_info)
    
    # ページのテキストコンテンツ（最初の1000文字）
    try:
        body_text = await page.inner_text('body')
        structure['text_content'] = body_text[:1000] + '...' if len(body_text) > 1000 else body_text
    except:
        pass
    
    # ログ出力
    logger.info(f"\n--- {step_name} ---")
    logger.info(f"URL: {structure['url']}")
    logger.info(f"Title: {structure['title']}")
    logger.info(f"フォーム数: {len(structure['forms'])}")
    logger.info(f"入力フィールド数: {len(structure['inputs'])}")
    logger.info(f"セレクトボックス数: {len(structure['selects'])}")
    logger.info(f"ボタン数: {len(structure['buttons'])}")
    
    if structure['inputs']:
        logger.info("\n入力フィールド:")
        for inp in structure['inputs']:
            logger.info(f"  - {inp['tag']} | name='{inp['name']}' | id='{inp['id']}' | type='{inp['type']}' | label='{inp.get('label', 'N/A')}'")
    
    if structure['selects']:
        logger.info("\nセレクトボックス:")
        for sel in structure['selects']:
            logger.info(f"  - name='{sel['name']}' | id='{sel['id']}' | label='{sel.get('label', 'N/A')}'")
    
    if structure['buttons']:
        logger.info("\nボタン:")
        for btn in structure['buttons']:
            logger.info(f"  - {btn['tag']} | id='{btn['id']}' | text='{btn['text']}' | enabled={btn['enabled']}")
    
    return structure


if __name__ == "__main__":
    asyncio.run(inspect_form_structure())

