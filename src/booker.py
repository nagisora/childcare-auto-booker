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
        self.booker_email = os.getenv("BOOKER_EMAIL", "")
        self.booker_phone = os.getenv("BOOKER_PHONE", "")
        self.child_name = os.getenv("CHILD_NAME", "")
        self.child_age = os.getenv("CHILD_AGE", "")
        
        # 希望条件
        self.preferred_days = os.getenv("PREFERRED_DAYS", "").split(",")
        self.preferred_time_start = os.getenv("PREFERRED_TIME_START", "09:00")
        self.preferred_time_end = os.getenv("PREFERRED_TIME_END", "17:00")
        
        self.logger.info(f"予約実行クラス初期化完了 (DRY_RUN: {self.dry_run}, STOP_BEFORE_SUBMIT: {self.stop_before_submit})")
        
    async def execute_booking(self, slot_info: Dict, page: Page) -> bool:
        """予約を実行"""
        try:
            self.logger.info(f"予約実行開始: {slot_info['text']}")
            
            if self.dry_run:
                self.logger.info("DRY_RUNモード: 実際の予約は実行しません")
                return True
                
            # 1. 予約リンクをクリック
            if not await self._click_reservation_link(slot_info, page):
                return False
                
            # 2. メニュー選択
            if not await self._select_menu(page):
                return False
                
            # 3. 日時選択
            if not await self._select_datetime(page):
                return False
                
            # 4. 予約者情報入力
            if not await self._fill_booking_form(page):
                return False
                
            # 5. 確認・予約完了
            if not await self._confirm_booking(page):
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
        """メニューを選択"""
        try:
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
            
    async def _fill_booking_form(self, page: Page) -> bool:
        """予約フォームに入力"""
        try:
            # 名前入力
            name_selectors = [
                'input[name*="name"]',
                'input[name*="姓名"]',
                'input[name*="氏名"]',
                '#name, #fullname'
            ]
            
            for selector in name_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    await element.fill(self.booker_name)
                    self.logger.info(f"名前を入力: {self.booker_name}")
                    break
                    
            # メールアドレス入力
            email_selectors = [
                'input[name*="email"]',
                'input[name*="mail"]',
                'input[type="email"]',
                '#email, #mail'
            ]
            
            for selector in email_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    await element.fill(self.booker_email)
                    self.logger.info(f"メールアドレスを入力: {self.booker_email}")
                    break
                    
            # 電話番号入力
            phone_selectors = [
                'input[name*="phone"]',
                'input[name*="tel"]',
                'input[name*="電話"]',
                '#phone, #tel'
            ]
            
            for selector in phone_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    await element.fill(self.booker_phone)
                    self.logger.info(f"電話番号を入力: {self.booker_phone}")
                    break
                    
            # お子様の名前入力
            child_name_selectors = [
                'input[name*="child"]',
                'input[name*="子供"]',
                'input[name*="お子様"]',
                '#child-name'
            ]
            
            for selector in child_name_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    await element.fill(self.child_name)
                    self.logger.info(f"お子様の名前を入力: {self.child_name}")
                    break
                    
            # 年齢入力
            age_selectors = [
                'input[name*="age"]',
                'input[name*="年齢"]',
                'select[name*="age"]',
                '#age'
            ]
            
            for selector in age_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    if await element.get_attribute('tagName') == 'SELECT':
                        await element.select_option(value=self.child_age)
                    else:
                        await element.fill(self.child_age)
                    self.logger.info(f"年齢を入力: {self.child_age}")
                    break
                    
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            self.logger.error(f"フォーム入力エラー: {e}")
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
