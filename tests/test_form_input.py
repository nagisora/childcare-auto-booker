#!/usr/bin/env python3
"""
フォーム入力テスト: 予約フォーム入力フローのテスト

- 残0枠でも処理を続行（フォーム入力テストは可能）
- 確認画面まで進み、最終送信前に停止
- GUI表示モード（WSL環境対応）
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

# ログ設定（初期化）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .envファイルを読み込む
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    logger.debug(f".envファイルを読み込みました: {env_file}")
else:
    logger.warning(f".envファイルが見つかりません: {env_file}")
    logger.info("環境変数が設定されていない場合は、.envファイルを作成するか、環境変数を直接設定してください")

# テストサイトを使用するため、SITE_MODE=testを強制設定
# （TARGET_URLが.envに設定されている場合でも、テストサイトを優先する）
os.environ["SITE_MODE"] = "test"
# TARGET_URLを削除してSITE_MODEを有効にする
if "TARGET_URL" in os.environ:
    logger.info(f"TARGET_URL={os.environ['TARGET_URL']}が設定されていますが、テストサイトモードのため無視します")
    del os.environ["TARGET_URL"]

from src.config import (
    get_target_url,
    get_stop_before_submit,
)
from src.scraper import AirReserveScraper
from src.booker import AirReserveBooker


def is_available_slot_for_test(text: str, href: str) -> bool:
    """予約可能枠かどうかを判定（テスト用: 残0も含む）
    
    フォーム入力テストのため、残0枠も検出対象とする
    
    Args:
        text: 枠のテキスト
        href: リンクURL
        
    Returns:
        bool: フォーム入力テスト可能な枠かどうか
    """
    if not text or not href:
        return False
    
    text_lower = text.lower()
    
    # LINE予約は除外（Airリザーブから予約できない）
    if 'line予約' in text_lower or 'ここはline' in text_lower:
        return False
        
    # 明確に予約不可なキーワードを除外
    exclude_keywords = [
        '満員', '受付終了', '終了', 'disabled', 'unavailable',
        '予約不可', '不可', 'close', 'closed'
    ]
    
    for keyword in exclude_keywords:
        if keyword in text_lower:
            return False
    
    # 残0を含む場合でも、フォーム入力テストは可能なため許可
    # リンクがある場合はフォーム入力テストが可能と判断
    if href and href != '':
        return True
    
    # テキストに予約関連のキーワードが含まれている場合は許可
    include_keywords = [
        '残', '仮', 'available', '予約可能', '可能', '受付中', '待'
    ]
    
    for keyword in include_keywords:
        if keyword in text_lower:
            return True
            
    return False


async def find_test_slot(page, max_weeks: int = 7):
    """テスト用の予約枠を検索（残0を含む）
    
    Args:
        page: PlaywrightのPageオブジェクト
        max_weeks: 検索する最大週数
        
    Returns:
        dict: 見つかった枠の情報、見つからない場合はNone
    """
    url = get_target_url()
    logger.info(f"カレンダーページを読み込み中: {url}")
    await page.goto(url, wait_until="networkidle", timeout=30000)
    
    for week_num in range(max_weeks):
        logger.info(f"週 {week_num + 1}/{max_weeks} を確認中...")
        
        elements = await page.query_selector_all('.dataLinkBox.js-dataLinkBox')
        logger.info(f"要素数: {len(elements)}")
        
        for idx, elem in enumerate(elements):
            try:
                text = await elem.inner_text()
                
                # リンク要素を探す
                href = None
                link_elem = await elem.query_selector('a')
                if link_elem:
                    href = await link_elem.get_attribute('href')
                
                # dataLinkBox要素自体がリンクの場合
                if not href:
                    tag_name = await elem.evaluate('el => el.tagName')
                    if tag_name == 'A':
                        href = await elem.get_attribute('href')
                
                # 疑似hrefを作成
                if not href or href == '':
                    href = 'dataLinkBox:' + text.strip()
                
                # テスト用判定（残0も含む）
                if is_available_slot_for_test(text, href):
                    display_text = text[:70].replace('\n', ' ')
                    logger.info(f"テスト対象の枠を発見: {display_text}")
                    
                    slot_info = {
                        'text': text.strip(),
                        'href': href,
                        'week_number': week_num + 1,
                        'week_url': page.url,
                    }
                    return slot_info
                    
            except Exception as e:
                logger.debug(f"要素解析エラー: {e}")
                continue
        
        # 次週へ移動
        if week_num < max_weeks - 1:
            next_button = await page.query_selector('.ctlListItem.listNext')
            if next_button:
                await next_button.click()
                await asyncio.sleep(0.5)
            else:
                logger.info("次週ボタンが見つかりません。検索を終了します")
                break
    
    logger.warning("テスト対象の枠が見つかりませんでした")
    return None


async def test_form_input():
    """フォーム入力テストのメイン関数"""
    
    # WSL環境でのGUI表示確認
    display = os.getenv('DISPLAY')
    if display:
        logger.info(f"DISPLAY環境変数: {display}")
    else:
        logger.warning("DISPLAY環境変数が設定されていません。X11フォワーディングが必要な場合があります")
    
    # STOP_BEFORE_SUBMITの確認
    stop_before_submit = get_stop_before_submit()
    logger.info(f"STOP_BEFORE_SUBMIT: {stop_before_submit}")
    if not stop_before_submit:
        logger.warning("⚠️ STOP_BEFORE_SUBMITがFalseです。実際に予約が送信される可能性があります")
        logger.info("環境変数 STOP_BEFORE_SUBMIT=true を設定することを推奨します")
    
    async with async_playwright() as p:
        # headless=Falseでブラウザを起動（GUI表示）
        logger.info("ブラウザを起動中（GUI表示モード）...")
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        )
        
        try:
            page = await browser.new_page()
            
            # 予約枠を検索（残0も含む）
            slot_info = await find_test_slot(page, max_weeks=7)
            
            if not slot_info:
                logger.error("テスト対象の枠が見つかりませんでした")
                return
            
            logger.info(f"テスト対象の枠: {slot_info['text'][:100]}")
            logger.info("フォーム入力フローを開始します...")
            
            # テスト用: 直接リンクをクリックして予約受付期間外チェックをスキップ
            href = slot_info.get('href')
            if href and href.startswith('dataLinkBox:'):
                # 疑似hrefの場合は要素を再検索してクリック
                display_text = href.replace('dataLinkBox:', '').strip()
                elements = await page.query_selector_all('.dataLinkBox.js-dataLinkBox')
                clicked = False
                for element in elements:
                    element_text = await element.inner_text()
                    if display_text in element_text or element_text in display_text:
                        await element.click()
                        await asyncio.sleep(2)
                        clicked = True
                        logger.info(f"クリック後のURL: {page.url}")
                        break
                if not clicked:
                    logger.error("対応するdataLinkBox要素が見つかりませんでした")
                    return
            elif href:
                # 通常のhrefの場合
                if href.startswith('/'):
                    base_url = get_target_url()
                    href = base_url.rstrip('/') + href
                logger.info(f"予約ページに移動: {href}")
                await page.goto(href, wait_until="networkidle", timeout=30000)
            
            # AirReserveBookerを使ってフォーム入力フローを実行
            # 予約受付期間外チェックをスキップして、直接フォーム入力に進む
            booker = AirReserveBooker()
            
            # 各ステップを個別に実行（予約受付期間外チェックをスキップ）
            try:
                # 1. メニュー選択
                logger.info("メニュー選択中...")
                if not await booker._select_menu(page):
                    logger.warning("メニュー選択をスキップしました")
                
                # 2. 日時選択
                logger.info("日時選択中...")
                if not await booker._select_datetime(page):
                    logger.warning("日時選択をスキップしました")
                
                # 3. メニュー詳細フォーム送信（確認画面へ遷移）
                logger.info("メニュー詳細フォーム送信中...")
                if not await booker._submit_menu_detail_form(page):
                    logger.warning("メニュー詳細フォーム送信をスキップしました")
                
                # 4. 予約者情報入力
                logger.info("予約者情報入力中...")
                if not await booker._fill_booking_form(page):
                    logger.error("予約者情報入力に失敗しました")
                    return
                
                # 5. 確認画面で停止（STOP_BEFORE_SUBMITがTrueの場合）
                if stop_before_submit:
                    logger.info("✅ 確認画面まで進みました。フォーム入力テストが完了しました")
                    logger.info("確認画面を確認してください。最終送信は行いません（STOP_BEFORE_SUBMIT=true）")
                else:
                    # 確認・予約完了
                    logger.warning("⚠️ STOP_BEFORE_SUBMITがFalseのため、最終確認に進みます...")
                    if await booker._confirm_booking(page):
                        logger.info("✅ フォーム入力テストが正常に完了しました")
                    else:
                        logger.error("❌ 最終確認でエラーが発生しました")
                        
            except Exception as e:
                logger.error(f"フォーム入力フロー中にエラーが発生: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"テスト実行エラー: {e}", exc_info=True)
        finally:
            # 対話的環境かどうかをチェック
            is_interactive = sys.stdin.isatty()
            if is_interactive:
                logger.info("ブラウザを閉じる前に、確認画面を確認してください")
                logger.info("Enterキーを押すとブラウザを閉じます...")
                try:
                    input()
                except (KeyboardInterrupt, EOFError):
                    logger.info("ブラウザを閉じます...")
            else:
                logger.info("非対話的環境のため、10秒後にブラウザを閉じます...")
                await asyncio.sleep(10)
            
            await browser.close()
            logger.info("ブラウザを閉じました")


if __name__ == "__main__":
    asyncio.run(test_form_input())

