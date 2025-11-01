"""
Airリザーブ予約フロー自動化機能

検出された予約可能枠に対して自動で予約を実行する
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from playwright.async_api import Page


class AirReserveBooker:
    """Airリザーブ予約実行クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        self.stop_before_submit = os.getenv("STOP_BEFORE_SUBMIT", "true").lower() == "true"
        self.require_manual_confirmation = os.getenv("REQUIRE_MANUAL_CONFIRMATION", "false").lower() == "true"
        
        # 予約者情報
        self.booker_name = os.getenv("BOOKER_NAME", "")
        self.booker_name_kana = os.getenv("BOOKER_NAME_KANA", "")  # フリガナ（セイ）
        self.booker_name_kana_mei = os.getenv("BOOKER_NAME_KANA_MEI", "")  # フリガナ（メイ）
        self.booker_email = os.getenv("BOOKER_EMAIL", "")
        self.booker_phone = os.getenv("BOOKER_PHONE", "")
        self.child_name = os.getenv("CHILD_NAME", "")
        self.child_age = os.getenv("CHILD_AGE", "")
        
        # 希望条件
        self.preferred_days = os.getenv("PREFERRED_DAYS", "").split(",")
        self.preferred_time_start = os.getenv("PREFERRED_TIME_START", "09:00")
        self.preferred_time_end = os.getenv("PREFERRED_TIME_END", "17:00")
        
        self.logger.info(f"予約実行クラス初期化完了 (DRY_RUN: {self.dry_run}, STOP_BEFORE_SUBMIT: {self.stop_before_submit})")
    
    async def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0, operation_name: str = "操作"):
        """指数バックオフによるリトライ機能
        
        Args:
            func: 実行する非同期関数（Trueを返すと成功、Falseまたは例外で失敗）
            max_retries: 最大リトライ回数
            base_delay: 基本待機時間（秒）
            operation_name: 操作名（ログ用）
        
        Returns:
            関数の戻り値（成功時、True）
        
        Raises:
            最後の試行で発生した例外、またはすべてのリトライが失敗した場合にFalseを返す
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                result = await func()
                if result:
                    return result
                # Falseが返された場合もリトライ
                attempt_num = attempt + 1
                if attempt_num < max_retries:
                    delay = base_delay * (2 ** attempt)
                    self.logger.warning(
                        f"{operation_name}が失敗しました (試行 {attempt_num}/{max_retries}): Falseが返されました"
                    )
                    self.logger.info(f"{delay:.1f}秒後にリトライします...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"{operation_name}が{max_retries}回試行後も失敗しました"
                    )
                    return False
            except Exception as e:
                last_exception = e
                attempt_num = attempt + 1
                
                if attempt_num < max_retries:
                    # 指数バックオフ: 1秒, 2秒, 4秒, ...
                    delay = base_delay * (2 ** attempt)
                    self.logger.warning(
                        f"{operation_name}が失敗しました (試行 {attempt_num}/{max_retries}): {e}"
                    )
                    self.logger.info(f"{delay:.1f}秒後にリトライします...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"{operation_name}が{max_retries}回試行後も失敗しました: {e}"
                    )
                    raise last_exception
        
        # すべてのリトライが失敗した場合（Falseが返された場合）
        return False
        
    async def execute_booking(self, slot_info: Dict, page: Page) -> bool:
        """予約を実行"""
        try:
            self.logger.info(f"予約実行開始: {slot_info['text']}")
            
            if self.dry_run:
                self.logger.info("DRY_RUNモード: 実際の予約は実行しません")
                return True
                
            # 1. 予約リンクをクリック（リトライ付き）
            async def click_link():
                return await self._click_reservation_link(slot_info, page)
            
            if not await self._retry_with_backoff(click_link, max_retries=3, operation_name="予約リンククリック"):
                return False
                
            # 2. メニュー選択（リトライ付き）
            async def select_menu():
                return await self._select_menu(page)
            
            if not await self._retry_with_backoff(select_menu, max_retries=2, operation_name="メニュー選択"):
                return False
                
            # 3. 日時選択（リトライ付き）
            async def select_datetime():
                return await self._select_datetime(page)
            
            if not await self._retry_with_backoff(select_datetime, max_retries=2, operation_name="日時選択"):
                return False
                
            # 4. メニュー詳細ページの送信（確認画面へ遷移、リトライ付き）
            async def submit_form():
                return await self._submit_menu_detail_form(page)
            
            if not await self._retry_with_backoff(submit_form, max_retries=3, operation_name="フォーム送信"):
                return False
            
            # 5. 予約者情報入力（リトライ付き）
            async def fill_form():
                return await self._fill_booking_form(page)
            
            if not await self._retry_with_backoff(fill_form, max_retries=2, operation_name="フォーム入力"):
                return False
            
            # 6. 確認・予約完了（リトライ付き）
            async def confirm():
                return await self._confirm_booking(page)
            
            if not await self._retry_with_backoff(confirm, max_retries=3, operation_name="予約確認"):
                return False
                
            self.logger.info("予約が正常に完了しました")
            return True
            
        except Exception as e:
            self.logger.error(f"予約実行エラー: {e}")
            return False
            
    async def _click_reservation_link(self, slot_info: Dict, page: Page) -> bool:
        """予約リンクをクリック"""
        try:
            href = slot_info.get('href')
            if not href:
                self.logger.error("予約リンクが見つかりません")
                return False
            
            # 疑似href（dataLinkBox:で始まる）の場合は要素を再検索してクリック
            if href.startswith('dataLinkBox:'):
                # 疑似hrefから元のテキストを抽出
                display_text = href.replace('dataLinkBox:', '').strip()
                
                # slot_infoに保存されている情報を取得
                week_number = slot_info.get('week_number')  # 検出時点の週番号
                week_start_date = slot_info.get('week_start_date')  # 検出時点の週開始日
                week_url = slot_info.get('week_url')  # 検出時点のページURL
                
                # 週番号がある場合、その週まで移動する
                if week_number:
                    self.logger.info(f"週{week_number}に移動します... (週開始日: {week_start_date})")
                    target_url = os.getenv("TARGET_URL", "https://airrsv.net/kokoroto-azukari/calendar")
                    await page.goto(target_url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(1)
                    
                    # 指定された週まで「次週」ボタンをクリック
                    for i in range(week_number - 1):
                        next_button = await page.query_selector('.ctlListItem.listNext')
                        if next_button:
                            await next_button.click()
                            await asyncio.sleep(0.5)
                            self.logger.debug(f"週{i + 2}に移動しました")
                        else:
                            self.logger.warning(f"週{week_number}まで移動できませんでした（次週ボタンが見つかりません）")
                            break
                elif week_url:
                    # 週番号がない場合、URLで移動
                    self.logger.info(f"検出時点のページに戻ります: {week_url}")
                    await page.goto(week_url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(1)
                
                self.logger.info(f"dataLinkBox要素を検索してクリックします... (テキスト: {display_text[:50]}...)")
                try:
                    # 現在のページで対応するdataLinkBox要素を検索
                    elements = await page.query_selector_all('.dataLinkBox.js-dataLinkBox')
                    
                    clicked = False
                    matched_elements = []
                    for element in elements:
                        element_text = await element.inner_text()
                        # テキストが一致する要素を記録
                        if display_text in element_text or element_text in display_text:
                            matched_elements.append((element, element_text))
                    
                    # 週開始日がある場合、さらに絞り込み（オプション）
                    if week_start_date and matched_elements:
                        self.logger.debug(f"週開始日 {week_start_date} に基づいて要素を選択します")
                    
                    # 最初に一致した要素をクリック
                    if matched_elements:
                        element, element_text = matched_elements[0]
                        await element.click()
                        await asyncio.sleep(2)  # ページ遷移待機
                        self.logger.info(f"クリック後のURL: {page.url}")
                        clicked = True
                    
                    if not clicked:
                        self.logger.error(f"対応するdataLinkBox要素が見つかりませんでした (検索対象: {len(elements)}個の要素)")
                        return False
                except Exception as e:
                    self.logger.error(f"dataLinkBox要素のクリックに失敗: {e}")
                    return False
            else:
                # 通常のhrefの場合
                # 相対URLの場合は絶対URLに変換
                if href.startswith('/'):
                    base_url = os.getenv("TARGET_URL", "https://airrsv.net/kokoroto-azukari/calendar")
                    href = base_url.rstrip('/') + href
                    
                self.logger.info(f"予約ページに移動: {href}")
                
                # 予約ページに移動
                response = await page.goto(href, wait_until="networkidle", timeout=30000)
                
                if not response or response.status != 200:
                    self.logger.error(f"予約ページ読み込み失敗: {response.status if response else 'No response'}")
                    return False
                
            # エラーメッセージのチェック（予約受付期間外かどうか）
            is_available = await self._check_reservation_availability(page)
            if not is_available:
                self.logger.warning("この予約枠は予約受付期間外です")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"予約リンククリックエラー: {e}")
            return False
            
    async def _check_reservation_availability(self, page: Page) -> bool:
        """予約ページでエラーメッセージをチェックし、予約可能かを判定"""
        try:
            # ページのコンテンツを取得
            page_content = await page.content()
            page_text = await page.inner_text('body')
            
            # エラーメッセージのパターン
            error_patterns = [
                '予約受付期間外です',
                '別の時間帯をお探しください',
                '受付期間外',
                '予約できません',
                'このサービスはご利用いただけません',
                'ご予約いただけません'
            ]
            
            # エラーメッセージのチェック
            for pattern in error_patterns:
                if pattern in page_text:
                    self.logger.debug(f"エラーメッセージを検出: {pattern}")
                    return False
            
            # 成功メッセージまたはフォーム要素のチェック
            # 予約フォームが表示されている場合は予約可能
            form_indicators = [
                'name="name"',  # 名前入力欄
                'name="email"',  # メール入力欄
                'type="submit"',  # 送信ボタン
                '予約',  # 予約関連のテキスト
                'メニュー',  # メニュー選択
            ]
            
            # HTMLコンテンツでチェック
            for indicator in form_indicators:
                if indicator in page_content:
                    self.logger.debug(f"予約可能な状態を確認: {indicator}")
                    return True
            
            # デフォルトは予約可能として扱う
            self.logger.debug("エラーメッセージが見つかりませんでした。予約可能とみなします。")
            return True
            
        except Exception as e:
            self.logger.error(f"予約可否チェックエラー: {e}")
            # エラー時は予約可能として扱う（安全側に倒す）
            return True
    
    async def _select_menu(self, page: Page) -> bool:
        """メニューを選択（メニュー詳細ページでは参加人数を設定）"""
        try:
            # メニュー詳細ページの場合、参加人数フィールドを確認
            # 調査結果: name="lessonEntryPaxCnt", id="lessonEntryPaxCnt"
            lesson_entry_field = await page.query_selector('#lessonEntryPaxCnt, input[name="lessonEntryPaxCnt"]')
            if lesson_entry_field and await lesson_entry_field.is_visible():
                # 参加人数が既に設定されているか確認
                current_value = await lesson_entry_field.input_value()
                if not current_value or current_value == "0":
                    await lesson_entry_field.fill("1")  # デフォルトで1人
                    self.logger.info("参加人数を1に設定しました")
                else:
                    self.logger.info(f"参加人数は既に設定されています: {current_value}")
                await asyncio.sleep(0.5)
                return True
            
            # メニュー選択の一般的なパターンを試行
            menu_selectors = [
                'input[type="radio"][name*="menu"]',
                'select[name*="menu"]',
                '.menu-item input[type="radio"]',
                '[data-menu]'
            ]
            
            for selector in menu_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    # 最初の選択可能なメニューを選択
                    for element in elements:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            await element.click()
                            self.logger.info(f"メニューを選択: {selector}")
                            await asyncio.sleep(1)
                            return True
                            
            self.logger.warning("メニューが見つかりません（スキップ）")
            return True  # メニュー選択が不要な場合もある
            
        except Exception as e:
            self.logger.error(f"メニュー選択エラー: {e}")
            return False
            
    async def _select_datetime(self, page: Page) -> bool:
        """日時を選択"""
        try:
            # 日時選択の一般的なパターンを試行
            datetime_selectors = [
                'input[type="radio"][name*="datetime"]',
                'input[type="radio"][name*="time"]',
                '.time-slot input[type="radio"]',
                '[data-datetime]'
            ]
            
            for selector in datetime_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    # 最初の選択可能な日時を選択
                    for element in elements:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            await element.click()
                            self.logger.info(f"日時を選択: {selector}")
                            await asyncio.sleep(1)
                            return True
                            
            self.logger.warning("日時選択が見つかりません（スキップ）")
            return True  # 日時選択が不要な場合もある
            
        except Exception as e:
            self.logger.error(f"日時選択エラー: {e}")
            return False
            
    async def _submit_menu_detail_form(self, page: Page) -> bool:
        """メニュー詳細フォームを送信して確認画面へ遷移"""
        try:
            # フォームIDを確認（調査結果: id="menuDetailForm"）
            form = await page.query_selector('#menuDetailForm, form[action*="confirm"]')
            if not form:
                self.logger.warning("メニュー詳細フォームが見つかりません（スキップ）")
                return True  # フォームが存在しない場合はスキップ
            
            # 送信ボタンを探す（複数のパターンを試行）
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("確認")',
                'button:has-text("次へ")',
                'button:has-text("予約")',
                'form button',
                '.submit-button',
                '.confirm-button'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                button = await page.query_selector(selector)
                if button and await button.is_visible() and await button.is_enabled():
                    submit_button = button
                    self.logger.info(f"送信ボタンを見つけました: {selector}")
                    break
            
            if not submit_button:
                # ボタンが見つからない場合、フォームを直接送信
                self.logger.info("送信ボタンが見つかりません。フォームを直接送信します...")
                await form.evaluate('form => form.submit()')
                await asyncio.sleep(2)
            else:
                await submit_button.click()
                await asyncio.sleep(2)  # ページ遷移待機
            
            # ページ遷移を待機
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # 確認画面に遷移したか確認
            current_url = page.url
            if "confirm" in current_url.lower():
                self.logger.info("確認画面に遷移しました")
                return True
            else:
                self.logger.warning(f"確認画面への遷移が確認できませんでした。現在のURL: {current_url}")
                return True  # エラーでも続行（予約期間外などの可能性）
            
        except Exception as e:
            self.logger.error(f"メニュー詳細フォーム送信エラー: {e}")
            return False
    
    async def _fill_booking_form(self, page: Page) -> bool:
        """予約フォームに入力（確認画面での予約者情報入力）"""
        try:
            # フォーム入力ページまたは確認画面にいるか確認
            current_url = page.url
            # フォーム入力ページのURLパターン: /booking/lesson/visitor/regist/ または confirm を含む
            is_form_page = "/booking/" in current_url or "visitor/regist" in current_url or "confirm" in current_url.lower()
            if not is_form_page:
                self.logger.warning(f"フォーム入力ページではないため、フォーム入力をスキップします (URL: {current_url})")
                return True
            
            self.logger.info(f"フォーム入力ページを検出しました: {current_url}")
            
            # 名前入力（複数のパターンを試行）
            name_selectors = [
                'input[name*="name"]',
                'input[name*="姓名"]',
                'input[name*="氏名"]',
                'input[name*="予約者"]',
                'input[name*="保護者"]',
                'input[id*="name"]',
                'input[id*="Name"]',
                'input[placeholder*="氏名"]',
                'input[placeholder*="名前"]',
                'input[placeholder*="姓名"]',
                'label:has-text("氏名") + input',
                'label:has-text("名前") + input',
                'label:has-text("予約者") + input',
                '#name, #fullname, #bookerName'
            ]
            
            name_filled = False
            for selector in name_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        if is_visible and is_enabled:
                            await element.fill(self.booker_name)
                            self.logger.info(f"名前を入力: {self.booker_name} (selector: {selector})")
                            name_filled = True
                            break
                        else:
                            self.logger.debug(f"名前フィールドが見つかりましたが、visible={is_visible}, enabled={is_enabled}: {selector}")
                    else:
                        self.logger.debug(f"名前フィールドが見つかりませんでした: {selector}")
                except Exception as e:
                    self.logger.debug(f"名前フィールド検索エラー ({selector}): {e}")
                    continue
            
            if not name_filled:
                # Airリザーブのフォームは姓（lastNm）と名（firstNm）に分かれている
                self.logger.debug("標準的な名前フィールドが見つかりませんでした。姓・名フィールドを試行します...")
                
                # 姓と名に分割（スペースまたは中点で分割、または全体を姓または名として扱う）
                name_parts = self.booker_name.replace('・', ' ').split(' ', 1)
                last_name = name_parts[0] if len(name_parts) > 0 else self.booker_name
                first_name = name_parts[1] if len(name_parts) > 1 else self.booker_name
                
                # 姓フィールド（lastNm）
                last_name_field = await page.query_selector('input[name="lastNm"]')
                if last_name_field and await last_name_field.is_visible() and await last_name_field.is_enabled():
                    await last_name_field.fill(last_name)
                    self.logger.info(f"姓を入力: {last_name}")
                    name_filled = True
                
                # 名フィールド（firstNm）
                first_name_field = await page.query_selector('input[name="firstNm"]')
                if first_name_field and await first_name_field.is_visible() and await first_name_field.is_enabled():
                    await first_name_field.fill(first_name)
                    self.logger.info(f"名を入力: {first_name}")
                    name_filled = True
                
                # フリガナ（セイ）フィールド（lastNmKn）
                if self.booker_name_kana:
                    last_nm_kn_field = await page.query_selector('input[name="lastNmKn"]')
                    if last_nm_kn_field and await last_nm_kn_field.is_visible() and await last_nm_kn_field.is_enabled():
                        await last_nm_kn_field.fill(self.booker_name_kana)
                        self.logger.info(f"フリガナ（セイ）を入力: {self.booker_name_kana}")
                else:
                    self.logger.warning("フリガナ（セイ）が設定されていません")
                
                # フリガナ（メイ）フィールド（firstNmKn）
                if self.booker_name_kana_mei:
                    first_nm_kn_field = await page.query_selector('input[name="firstNmKn"]')
                    if first_nm_kn_field and await first_nm_kn_field.is_visible() and await first_nm_kn_field.is_enabled():
                        await first_nm_kn_field.fill(self.booker_name_kana_mei)
                        self.logger.info(f"フリガナ（メイ）を入力: {self.booker_name_kana_mei}")
                else:
                    self.logger.warning("フリガナ（メイ）が設定されていません")
                
                if not name_filled:
                    self.logger.warning("名前入力フィールドが見つかりませんでした（全セレクター試行済み）")
                    if self.debug:
                        # すべてのinput要素をリストアップしてデバッグ
                        all_inputs = await page.query_selector_all('input[type="text"], input:not([type])')
                        self.logger.debug(f"ページ内のテキスト入力フィールド数: {len(all_inputs)}")
                        for i, inp in enumerate(all_inputs[:10]):  # 最初の10個だけ
                            try:
                                name_attr = await inp.get_attribute('name')
                                id_attr = await inp.get_attribute('id')
                                placeholder_attr = await inp.get_attribute('placeholder')
                                self.logger.debug(f"入力フィールド {i+1}: name={name_attr}, id={id_attr}, placeholder={placeholder_attr}")
                            except:
                                pass
                    
            # メールアドレス入力
            email_selectors = [
                'input[name*="email"]',
                'input[name*="mail"]',
                'input[name*="メール"]',
                'input[type="email"]',
                'input[id*="email"]',
                'input[id*="mail"]',
                '#email, #mail, #bookerEmail'
            ]
            
            email_filled = False
            for selector in email_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible() and await element.is_enabled():
                    await element.fill(self.booker_email)
                    self.logger.info(f"メールアドレスを入力: {self.booker_email}")
                    email_filled = True
                    break
            
            if not email_filled:
                # Airリザーブのフォーム構造に対応（mailAddress1）
                mail_address1_field = await page.query_selector('input[name="mailAddress1"]')
                if mail_address1_field and await mail_address1_field.is_visible() and await mail_address1_field.is_enabled():
                    await mail_address1_field.fill(self.booker_email)
                    self.logger.info(f"メールアドレスを入力: {self.booker_email}")
                    email_filled = True
            
            # メールアドレス確認用フィールド（mailAddress1ForCnfrm）
            if self.booker_email:
                mail_address1_confirm_field = await page.query_selector('input[name="mailAddress1ForCnfrm"]')
                if mail_address1_confirm_field and await mail_address1_confirm_field.is_visible() and await mail_address1_confirm_field.is_enabled():
                    await mail_address1_confirm_field.fill(self.booker_email)
                    self.logger.info(f"メールアドレス（確認用）を入力: {self.booker_email}")
            
            if not email_filled:
                self.logger.warning("メールアドレス入力フィールドが見つかりませんでした")
                    
            # 電話番号入力
            # 電話番号のフォーマット: 9-17桁の半角数字（ハイフン除去）
            phone_normalized = self.booker_phone.replace('-', '').replace('‐', '').replace('ー', '')
            
            phone_selectors = [
                'input[name*="phone"]',
                'input[name*="tel"]',
                'input[name*="電話"]',
                'input[name*="連絡先"]',
                'input[type="tel"]',
                'input[id*="phone"]',
                'input[id*="tel"]',
                '#phone, #tel, #bookerPhone'
            ]
            
            phone_filled = False
            for selector in phone_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible() and await element.is_enabled():
                    await element.fill(phone_normalized)
                    self.logger.info(f"電話番号を入力: {phone_normalized}")
                    phone_filled = True
                    break
            
            if not phone_filled:
                # Airリザーブのフォーム構造に対応（tel1）
                tel1_field = await page.query_selector('input[name="tel1"]')
                if tel1_field and await tel1_field.is_visible() and await tel1_field.is_enabled():
                    await tel1_field.fill(phone_normalized)
                    self.logger.info(f"電話番号を入力: {phone_normalized}")
                    phone_filled = True
            
            if not phone_filled:
                self.logger.warning("電話番号入力フィールドが見つかりませんでした")
                    
            # お子様の名前入力
            child_name_selectors = [
                'input[name*="child"]',
                'input[name*="子供"]',
                'input[name*="お子様"]',
                'input[name*="子ども"]',
                'input[name*="こども"]',
                'input[id*="child"]',
                'input[placeholder*="お子様"]',
                'input[placeholder*="子供"]',
                'label:has-text("お子様") + input',
                'label:has-text("子供") + input',
                '#child-name, #childName'
            ]
            
            child_name_filled = False
            for selector in child_name_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible() and await element.is_enabled():
                    await element.fill(self.child_name)
                    self.logger.info(f"お子様の名前を入力: {self.child_name}")
                    child_name_filled = True
                    break
            
            if not child_name_filled:
                self.logger.warning("お子様の名前入力フィールドが見つかりませんでした")
                    
            # 年齢入力
            age_selectors = [
                'input[name*="age"]',
                'input[name*="年齢"]',
                'input[name*="月齢"]',
                'select[name*="age"]',
                'select[name*="年齢"]',
                'input[id*="age"]',
                'select[id*="age"]',
                '#age, #childAge'
            ]
            
            age_filled = False
            for selector in age_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible() and await element.is_enabled():
                    tag_name = await element.evaluate('el => el.tagName')
                    if tag_name == 'SELECT':
                        await element.select_option(value=self.child_age)
                    else:
                        await element.fill(self.child_age)
                    self.logger.info(f"年齢を入力: {self.child_age}")
                    age_filled = True
                    break
            
            if not age_filled:
                self.logger.warning("年齢入力フィールドが見つかりませんでした")
            
            # 入力後の待機
            await asyncio.sleep(1)
            
            # 必須フィールドが入力されているか確認
            if not name_filled or not email_filled or not phone_filled:
                self.logger.warning("一部の必須フィールドが入力されていません")
                # スクリーンショットを保存してデバッグ用
                screenshot_path = await self.take_screenshot(page, "form_input_partial")
                self.logger.info(f"デバッグ用スクリーンショットを保存: {screenshot_path}")
            
            # 「確認へ進む」ボタンを押す（フォーム送信ではない、確認画面への遷移）
            self.logger.info("「確認へ進む」ボタンを探しています...")
            next_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("確認")',
                'button:has-text("確認へ進む")',
                'button:has-text("次へ")',
                'button:has-text("進む")',
                '.next-button',
                '.confirm-button'
            ]
            
            next_button_clicked = False
            for selector in next_button_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible() and await button.is_enabled():
                        button_text = await button.inner_text()
                        # 「送信」「予約確定」などの最終送信ボタンは避ける
                        if any(keyword in button_text.lower() for keyword in ['送信', '予約確定', '確定', 'submit']):
                            self.logger.debug(f"最終送信ボタンのためスキップ: {button_text}")
                            continue
                        
                        self.logger.info(f"「確認へ進む」ボタンをクリック: {button_text}")
                        await button.click()
                        await asyncio.sleep(2)  # ページ遷移待機
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        next_button_clicked = True
                        self.logger.info(f"確認画面に遷移しました: {page.url}")
                        break
                except Exception as e:
                    self.logger.debug(f"ボタンクリック試行失敗 ({selector}): {e}")
                    continue
            
            if not next_button_clicked:
                self.logger.warning("「確認へ進む」ボタンが見つかりませんでした（スキップ）")
                # フォーム入力自体は成功として扱う
            
            return True
            
        except Exception as e:
            self.logger.error(f"フォーム入力エラー: {e}")
            screenshot_path = await self.take_screenshot(page, "form_input_error")
            self.logger.info(f"エラー時のスクリーンショットを保存: {screenshot_path}")
            return False
            
    async def _confirm_booking(self, page: Page) -> bool:
        """予約を確認・完了"""
        try:
            # 確認ボタンの一般的なパターンを試行
            confirm_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("確認")',
                'button:has-text("予約")',
                'button:has-text("送信")',
                '.confirm-button',
                '.submit-button'
            ]
            
            confirm_button = None
            used_selector = None
            
            for selector in confirm_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible() and await element.is_enabled():
                    confirm_button = element
                    used_selector = selector
                    break
            
            if not confirm_button:
                self.logger.error("確認ボタンが見つかりません")
                return False
            
            # スクリーンショットを保存（送信前）
            screenshot_path = await self.take_screenshot(page, "before_submit")
            self.logger.info(f"送信前のスクリーンショットを保存: {screenshot_path}")
            
            # STOP_BEFORE_SUBMITチェック
            if self.stop_before_submit:
                self.logger.warning("⚠️ STOP_BEFORE_SUBMIT: 最終送信ボタンを押さずに停止しました")
                self.logger.info(f"確認ボタン: {used_selector}")
                self.logger.info("確認画面のスクリーンショットを確認してください")
                self.logger.info("本番実行する場合は STOP_BEFORE_SUBMIT=false に設定してください")
                return True  # テスト成功として扱う
            
            # 手動確認が必要な場合
            if self.require_manual_confirmation:
                self.logger.warning("⚠️ 手動確認が必要です")
                self.logger.info("確認画面のスクリーンショットを確認してください")
                response = input("予約を実行しますか？ (yes/no): ")
                if response.lower() != "yes":
                    self.logger.info("予約をキャンセルしました")
                    return False
            
            # 確認ボタンをクリック
            await confirm_button.click()
            self.logger.info(f"確認ボタンをクリック: {used_selector}")
            
            # ページの変化を待機
            await asyncio.sleep(3)
            
            # スクリーンショットを保存（送信後）
            screenshot_path = await self.take_screenshot(page, "after_submit")
            self.logger.info(f"送信後のスクリーンショットを保存: {screenshot_path}")
            
            # 成功メッセージの確認
            success_indicators = [
                '予約完了',
                '予約受付',
                '予約確定',
                'success',
                '完了'
            ]
            
            page_content = await page.content()
            for indicator in success_indicators:
                if indicator in page_content:
                    self.logger.info(f"予約成功を確認: {indicator}")
                    return True
                    
            # エラーメッセージの確認
            error_indicators = [
                'エラー',
                'error',
                '失敗',
                '満員',
                '受付終了'
            ]
            
            for indicator in error_indicators:
                if indicator in page_content:
                    self.logger.error(f"予約エラーを検出: {indicator}")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"予約確認エラー: {e}")
            return False
    
    async def take_screenshot(self, page: Page, prefix: str = "booking") -> str:
        """スクリーンショットを保存"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/{prefix}_{timestamp}.png"
            
            # スクリーンショットディレクトリを作成
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            
            await page.screenshot(path=filename, full_page=True)
            return filename
        except Exception as e:
            self.logger.error(f"スクリーンショット保存エラー: {e}")
            return ""
            
    def is_preferred_slot(self, slot_info: Dict) -> bool:
        """希望条件に合致する枠かどうかを判定"""
        try:
            text = slot_info.get('text', '').lower()
            
            # 希望曜日のチェック
            if self.preferred_days and any(day in text for day in self.preferred_days):
                return True
                
            # 希望時間帯のチェック
            # 時間の抽出（簡易版）
            import re
            time_pattern = r'(\d{1,2}):(\d{2})'
            matches = re.findall(time_pattern, text)
            
            if matches:
                for hour_str, minute_str in matches:
                    hour = int(hour_str)
                    minute = int(minute_str)
                    time_minutes = hour * 60 + minute
                    
                    start_minutes = int(self.preferred_time_start.split(':')[0]) * 60 + int(self.preferred_time_start.split(':')[1])
                    end_minutes = int(self.preferred_time_end.split(':')[0]) * 60 + int(self.preferred_time_end.split(':')[1])
                    
                    if start_minutes <= time_minutes <= end_minutes:
                        return True
                        
            return False
            
        except Exception as e:
            self.logger.error(f"希望条件判定エラー: {e}")
            return True  # エラーの場合は予約を試行
