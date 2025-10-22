"""
Airリザーブ予約ページのスクレイピング機能

予約可能枠を監視し、新規公開された枠を検出する
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, Page


class AirReserveScraper:
    """Airリザーブ予約ページのスクレイピングクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.target_url = os.getenv("TARGET_URL", "https://airrsv.net/kokoroto-azukari/calendar")
        self.headless = os.getenv("HEADLESS", "true").lower() == "true"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # 予約公開日時の設定
        release_datetime_str = os.getenv("NEXT_RELEASE_DATETIME", "2024-11-01 09:30:00")
        self.release_datetime = datetime.strptime(release_datetime_str, "%Y-%m-%d %H:%M:%S")
        
        # 監視時間（分）
        self.monitor_duration = int(os.getenv("MONITOR_DURATION_MINUTES", "10"))
        
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
            
    async def get_available_slots(self) -> List[Dict]:
        """予約可能枠を取得"""
        try:
            if not self.page:
                self.logger.error("ページが読み込まれていません")
                return []
                
            # 予約可能な日時を検索
            # Airリザーブの一般的なセレクターパターンを試行
            selectors = [
                'a[href*="reserve"]:not([class*="disabled"])',
                '.available, [class*="available"]',
                '.slot-available, [class*="slot-available"]',
                'td:not([class*="disabled"]):not([class*="unavailable"]) a',
                '[data-available="true"]'
            ]
            
            available_slots = []
            
            for selector in selectors:
                elements = await self.page.query_selector_all(selector)
                
                for element in elements:
                    try:
                        # 要素のテキストと属性を取得
                        text = await element.inner_text()
                        href = await element.get_attribute('href')
                        class_name = await element.get_attribute('class')
                        
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
                        
            self.logger.info(f"予約可能枠を {len(available_slots)} 件発見")
            
            if self.debug:
                for slot in available_slots:
                    self.logger.debug(f"発見した枠: {slot}")
                    
            return available_slots
            
        except Exception as e:
            self.logger.error(f"予約枠取得エラー: {e}")
            return []
            
    def _is_available_slot(self, text: str, href: str, class_name: str) -> bool:
        """予約可能枠かどうかを判定"""
        if not text:
            return False
            
        # 除外キーワード
        exclude_keywords = [
            '満員', '満', '受付終了', '終了', 'disabled', 'unavailable',
            '予約不可', '不可', 'close', 'closed'
        ]
        
        # 除外キーワードが含まれている場合は除外
        for keyword in exclude_keywords:
            if keyword in text.lower() or keyword in (class_name or '').lower():
                return False
                
        # 予約可能を示すキーワード
        include_keywords = [
            '残', '空', 'available', '予約可能', '可能', '受付中'
        ]
        
        # いずれかのキーワードが含まれている場合は予約可能
        for keyword in include_keywords:
            if keyword in text.lower():
                return True
                
        # リンクが存在し、除外キーワードが含まれていない場合は予約可能
        if href and not any(keyword in (class_name or '').lower() for keyword in exclude_keywords):
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
            
            # 現在時刻が監視開始時刻より前の場合は待機
            now = datetime.now()
            if now < monitor_start:
                wait_seconds = (monitor_start - now).total_seconds()
                self.logger.info(f"監視開始まで {wait_seconds:.1f} 秒待機します")
                await asyncio.sleep(wait_seconds)
                
            # 監視ループ
            last_slots = []
            check_interval = 1  # 1秒間隔
            
            while datetime.now() < monitor_end:
                try:
                    # 予約可能枠を取得
                    current_slots = await self.get_available_slots()
                    
                    # 新規枠を検出
                    new_slots = []
                    for slot in current_slots:
                        if slot not in last_slots:
                            new_slots.append(slot)
                            
                    if new_slots:
                        self.logger.info(f"新規予約枠を {len(new_slots)} 件発見:")
                        for slot in new_slots:
                            self.logger.info(f"  - {slot['text']} ({slot['href']})")
                            
                    last_slots = current_slots
                    
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
