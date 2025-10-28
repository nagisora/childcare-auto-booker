"""
Airリザーブ予約ページのスクレイピング機能

予約可能枠を監視し、新規公開された枠を検出する
"""

import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, Page


class AirReserveScraper:
    """Airリザーブ予約ページのスクレイピングクラス"""
    
    def __init__(self, booker=None):
        self.logger = logging.getLogger(__name__)
        self.target_url = os.getenv("TARGET_URL", "https://airrsv.net/kokoroto-azukari/calendar")
        self.headless = os.getenv("HEADLESS", "true").lower() == "true"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # テストサイトモード（14日前の13時から受付開始）
        self.test_site_mode = os.getenv("TEST_SITE_MODE", "false").lower() == "true"
        
        # 予約公開日時の設定
        release_datetime_str = os.getenv("NEXT_RELEASE_DATETIME", "2024-11-01 09:30:00")
        self.release_datetime = datetime.strptime(release_datetime_str, "%Y-%m-%d %H:%M:%S")
        
        # 監視時間（分）
        self.monitor_duration = int(os.getenv("MONITOR_DURATION_MINUTES", "10"))
        
        # bookerへの参照（エラーチェック用）
        self.booker = booker
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリ"""
        await self.start_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーのエグジット"""
        await self.close_browser()
        
    async def start_browser(self):
        """ブラウザを起動"""
        self.playwright = await async_playwright().start()
        
        # Ubuntu 24.04対応のChromium起動
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        self.page = await self.browser.new_page()
        
        # ユーザーエージェント設定
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.logger.info("ブラウザを起動しました")
        
    async def close_browser(self):
        """ブラウザを終了"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        self.logger.info("ブラウザを終了しました")
        
    async def load_calendar_page(self) -> bool:
        """カレンダーページを読み込み"""
        try:
            self.logger.info(f"カレンダーページを読み込み中: {self.target_url}")
            
            # ページ読み込み
            response = await self.page.goto(self.target_url, wait_until="networkidle", timeout=30000)
            
            if not response or response.status != 200:
                self.logger.error(f"ページ読み込み失敗: {response.status if response else 'No response'}")
                return False
                
            # ページタイトルの確認
            title = await self.page.title()
            self.logger.info(f"ページタイトル: {title}")
            
            # カレンダー要素の存在確認
            calendar_element = await self.page.query_selector('.calendar, [class*="calendar"], [id*="calendar"]')
            if not calendar_element:
                self.logger.warning("カレンダー要素が見つかりません")
                
            return True
            
        except Exception as e:
            self.logger.error(f"ページ読み込みエラー: {e}")
            return False
            
    async def get_available_slots(self, max_weeks: int = 7) -> List[Dict]:
        """予約可能枠を取得（複数週にわたって確認）
        
        Args:
            max_weeks: 確認する最大週数（デフォルト: 7週 = 約1.5ヶ月）
        """
        try:
            if not self.page:
                self.logger.error("ページが読み込まれていません")
                return []
                
            all_available_slots = []
            
            # 最初のページから開始
            for week_num in range(max_weeks):
                self.logger.info(f"週 {week_num + 1}/{max_weeks} を確認中...")
                
                # 現在のページで予約可能枠を検索
                slots = await self._get_slots_from_current_page()
                all_available_slots.extend(slots)
                
                # 次週へ移動（最後の週でない場合）
                if week_num < max_weeks - 1:
                    next_button = await self.page.query_selector('.ctlListItem.listNext')
                    if next_button:
                        await next_button.click()
                        await asyncio.sleep(0.5)  # ページ遷移待機
                    else:
                        self.logger.info("次週ボタンが見つかりません。確認を終了します")
                        break
            
            self.logger.info(f"合計 {len(all_available_slots)} 件の予約可能枠を発見")
            return all_available_slots
            
        except Exception as e:
            self.logger.error(f"予約枠取得エラー: {e}")
            return []
    
    async def _get_week_start_date(self) -> Optional[datetime]:
        """現在表示されている週の開始日を取得"""
        try:
            # 週情報を取得（class="ctlListItem listDate"）
            week_info_elems = await self.page.query_selector_all('.ctlListItem.listDate')
            if not week_info_elems or len(week_info_elems) == 0:
                self.logger.debug("週情報要素が見つかりません")
                return None
            
            # 最初の日付要素を取得
            first_date_elem = week_info_elems[0]
            week_text = await first_date_elem.inner_text()
            
            self.logger.debug(f"週情報テキスト: {week_text}")
            
            # 日付を抽出（例: "2025/10/27(月)"）
            match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', week_text)
            if match:
                year, month, day = map(int, match.groups())
                week_date = datetime(year, month, day)
            else:
                # 年なしの場合（例: "10/27(月)"）
                match = re.search(r'(\d{1,2})/(\d{1,2})', week_text)
                if not match:
                    self.logger.debug("日付パターンが見つかりません")
                    return None
                
                month, day = map(int, match.groups())
                now = datetime.now()
                year = now.year
                week_date = datetime(year, month, day)
                
                # 過去の日付の場合は翌年
                if week_date < now - timedelta(days=30):
                    week_date = datetime(year + 1, month, day)
            
            return week_date
            
        except Exception as e:
            self.logger.error(f"週開始日の取得エラー: {e}")
            return None
    
    def _is_within_14_days(self, event_date: datetime) -> bool:
        """イベント日が14日以内かどうかを判定"""
        now = datetime.now()
        days_until_event = (event_date - now).days
        return days_until_event <= 14
    
    async def _get_slots_from_current_page(self) -> List[Dict]:
        """現在のページから予約可能枠を取得"""
        try:
            # テストサイトモードの場合、週の開始日を取得
            week_start_date = None
            if self.test_site_mode:
                week_start_date = await self._get_week_start_date()
                if week_start_date:
                    self.logger.debug(f"週開始日: {week_start_date.strftime('%Y-%m-%d')}")
            
            # Airリザーブのカレンダー構造に特化したセレクター
            # class="dataLinkBox js-dataLinkBox" が予約リンクを含む
            selector = '.dataLinkBox.js-dataLinkBox'
            
            available_slots = []
            elements = await self.page.query_selector_all(selector)
            
            if self.debug:
                self.logger.debug(f"{selector} で {len(elements)} 個の要素を発見")
                # ページのHTML構造をログに出力（デバッグ用）
                if len(elements) == 0:
                    # 代替セレクターを試行
                    all_links = await self.page.query_selector_all('a')
                    self.logger.debug(f"ページ内の全リンク数: {len(all_links)}")
                    dataLinkBoxes = await self.page.query_selector_all('[class*="dataLinkBox"]')
                    self.logger.debug(f"dataLinkBoxを含むクラスの要素数: {len(dataLinkBoxes)}")
            
            for idx, element in enumerate(elements):
                try:
                    # 要素のテキストと属性を取得
                    text = await element.inner_text()
                    
                    # リンク要素を探す（dataLinkBox内のa要素）
                    link_element = await element.query_selector('a')
                    if not link_element:
                        continue
                        
                    href = await link_element.get_attribute('href')
                    class_name = await element.get_attribute('class')
                    
                    # テストサイトモードの場合、14日前チェック
                    if self.test_site_mode and week_start_date:
                        # イベントの曜日を推定（週の何日目か）
                        # カレンダーは週表示で、各日に複数イベントがある
                        # 簡易的に、週の開始日から6日以内と仮定
                        event_date = week_start_date + timedelta(days=min(idx, 6))
                        
                        if not self._is_within_14_days(event_date):
                            self.logger.debug(f"14日前より先のイベントをスキップ: {event_date.strftime('%Y-%m-%d')}")
                            continue
                    
                    # 予約可能な要素かチェック
                    if self._is_available_slot(text, href, class_name):
                        slot_info = {
                            'text': text.strip(),
                            'href': href,
                            'class': class_name,
                            'selector': selector,
                            'timestamp': datetime.now()
                        }
                        available_slots.append(slot_info)
                        
                except Exception as e:
                    self.logger.debug(f"要素解析エラー: {e}")
                    continue
            
            if self.debug and available_slots:
                for slot in available_slots:
                    self.logger.debug(f"発見した枠: {slot}")
                    
            return available_slots
            
        except Exception as e:
            self.logger.error(f"ページ内の予約枠取得エラー: {e}")
            return []
            
    def _is_available_slot(self, text: str, href: str, class_name: str) -> bool:
        """予約可能枠かどうかを判定"""
        if not text:
            return False
            
        # hrefが存在しない場合は予約不可
        if not href:
            return False
            
        text_lower = text.lower()
        
        # LINE予約はAirリザーブから予約できないため除外
        if 'line予約' in text_lower or 'ここはline' in text_lower:
            return False
        
        # 明確な除外キーワード（残0は先にチェック）
        if '残0' in text_lower:
            return False
            
        # その他の除外キーワード
        exclude_keywords = [
            '満員', '受付終了', '終了', 'disabled', 'unavailable',
            '予約不可', '不可', 'close', 'closed'
        ]
        
        for keyword in exclude_keywords:
            if keyword in text_lower or keyword in (class_name or '').lower():
                return False
                
        # 予約可能を示すキーワード（残○、仮予約など）
        # 「待」はキャンセル待ちを示すが、リンクがあれば予約可能な場合もある
        include_keywords = [
            '残', '仮', 'available', '予約可能', '可能', '受付中', '待'
        ]
        
        # いずれかのキーワードが含まれている場合は予約可能
        for keyword in include_keywords:
            if keyword in text_lower:
                return True
                
        return False
        
    async def start_monitoring(self):
        """予約枠の監視を開始"""
        self.logger.info("予約枠監視を開始します")
        
        # ブラウザ起動
        await self.start_browser()
        
        try:
            # カレンダーページ読み込み
            if not await self.load_calendar_page():
                self.logger.error("カレンダーページの読み込みに失敗しました")
                return
                
            # 監視開始時刻の計算
            monitor_start = self.release_datetime - timedelta(seconds=3)
            monitor_end = self.release_datetime + timedelta(minutes=self.monitor_duration)
            
            self.logger.info(f"監視期間: {monitor_start} ～ {monitor_end}")
            
            # スクリーンショットを撮影（デバッグ用）
            await self.take_screenshot("screenshots/calendar_initial.png")
            
            # 現在時刻が監視開始時刻より前の場合は待機
            now = datetime.now()
            if now < monitor_start:
                wait_seconds = (monitor_start - now).total_seconds()
                self.logger.info(f"監視開始まで {wait_seconds:.1f} 秒待機します")
                await asyncio.sleep(wait_seconds)
                
            # 監視ループ
            last_slots = []
            check_interval = 1  # 1秒間隔
            check_count = 0
            max_checks = int(self.monitor_duration * 60)  # 監視時間（分）を秒に変換
            
            while datetime.now() < monitor_end and check_count < max_checks:
                try:
                    check_count += 1
                    self.logger.info(f"チェック {check_count}/{max_checks}")
                    
                    # 予約可能枠を取得（1.5ヶ月先まで、7週分）
                    current_slots = await self.get_available_slots(max_weeks=7)
                    
                    # 新規枠を検出
                    last_hrefs = {slot.get('href', '') for slot in last_slots}
                    new_slots = []
                    for slot in current_slots:
                        href = slot.get('href', '')
                        if href and href not in last_hrefs:
                            new_slots.append(slot)
                            
                    if new_slots:
                        self.logger.info(f"新規予約枠を {len(new_slots)} 件発見:")
                        for slot in new_slots:
                            self.logger.info(f"  - {slot['text']} ({slot['href']})")
                            
                    last_slots = current_slots
                    
                    # 最初のページに戻る
                    await self.page.goto(self.target_url, wait_until="networkidle", timeout=30000)
                    
                    # 次のチェックまで待機
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.error(f"監視中にエラーが発生: {e}")
                    await asyncio.sleep(check_interval)
                    
            self.logger.info("監視期間が終了しました")
            
        finally:
            await self.close_browser()
            
    async def take_screenshot(self, filename: str = None):
        """スクリーンショットを撮影"""
        if not self.page:
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/calendar_{timestamp}.png"
            
        # スクリーンショットディレクトリを作成
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            await self.page.screenshot(path=filename, full_page=True)
            self.logger.info(f"スクリーンショットを保存: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"スクリーンショット撮影エラー: {e}")
            return None
