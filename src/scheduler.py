"""
スケジューラー

予約公開日時に基づいて自動実行を管理する
"""

import asyncio
import logging
import os
import schedule
import time
from datetime import datetime, timedelta
from threading import Thread

from src.scraper import AirReserveScraper
from src.booker import AirReserveBooker
from src.notifier import NotificationManager


class Scheduler:
    """スケジューラークラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.notifier = NotificationManager()
        
        # 予約公開日時の設定
        release_datetime_str = os.getenv("NEXT_RELEASE_DATETIME", "2024-11-01 09:30:00")
        self.release_datetime = datetime.strptime(release_datetime_str, "%Y-%m-%d %H:%M:%S")
        
        self.monitoring_active = False
        
    def start(self):
        """スケジューラーを開始"""
        self.logger.info("スケジューラーを開始します")
        
        # 予約公開日時の3秒前から監視を開始するジョブをスケジュール
        monitor_time = self.release_datetime - timedelta(seconds=3)
        
        # 毎日同じ時刻にチェック（実際の公開日時は月1回なので、その日のみ実行される）
        schedule.every().day.at(monitor_time.strftime("%H:%M:%S")).do(self._start_monitoring_job)
        
        self.logger.info(f"監視開始時刻をスケジュール: {monitor_time}")
        
        # スケジューラーループを開始
        self._run_scheduler()
        
    def _run_scheduler(self):
        """スケジューラーのメインループ"""
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("スケジューラーが中断されました")
                break
            except Exception as e:
                self.logger.error(f"スケジューラーエラー: {e}")
                time.sleep(5)
                
    def _start_monitoring_job(self):
        """監視ジョブを開始"""
        if self.monitoring_active:
            self.logger.warning("既に監視が実行中です")
            return
            
        self.logger.info("監視ジョブを開始します")
        self.notifier.notify_monitoring_start(self.release_datetime.strftime("%Y-%m-%d %H:%M:%S"))
        
        # 非同期タスクを別スレッドで実行
        thread = Thread(target=self._run_monitoring_task)
        thread.daemon = True
        thread.start()
        
    def _run_monitoring_task(self):
        """監視タスクを実行"""
        try:
            self.monitoring_active = True
            
            # 非同期イベントループを作成
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 監視を実行
            loop.run_until_complete(self._monitor_and_book())
            
        except Exception as e:
            self.logger.error(f"監視タスクエラー: {e}")
        finally:
            self.monitoring_active = False
            self.notifier.notify_monitoring_end()
            
    async def _monitor_and_book(self):
        """監視と予約を実行"""
        scraper = AirReserveScraper()
        booker = AirReserveBooker()
        
        async with scraper:
            # カレンダーページを読み込み
            if not await scraper.load_calendar_page():
                self.logger.error("カレンダーページの読み込みに失敗しました")
                return
                
            # 監視期間の計算
            monitor_start = self.release_datetime - timedelta(seconds=3)
            monitor_end = self.release_datetime + timedelta(minutes=int(os.getenv("MONITOR_DURATION_MINUTES", "10")))
            
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
            booking_attempted = False
            
            while datetime.now() < monitor_end:
                try:
                    # 予約可能枠を取得
                    current_slots = await scraper.get_available_slots()
                    
                    # 新規枠を検出
                    new_slots = []
                    for slot in current_slots:
                        if slot not in last_slots:
                            new_slots.append(slot)
                            
                    if new_slots:
                        self.notifier.notify_new_slot_detected(new_slots[0])
                        
                        # 希望条件に合致する枠があれば予約を試行
                        for slot in new_slots:
                            if booker.is_preferred_slot(slot) and not booking_attempted:
                                self.logger.info(f"希望条件に合致する枠を発見: {slot['text']}")
                                
                                # 予約を実行
                                success = await booker.execute_booking(slot, scraper.page)
                                
                                if success:
                                    self.notifier.notify_booking_success(slot)
                                    booking_attempted = True
                                    break
                                else:
                                    self.notifier.notify_booking_failure(slot, "予約実行に失敗")
                                    
                    last_slots = current_slots
                    
                    # 次のチェックまで待機
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.error(f"監視中にエラーが発生: {e}")
                    await asyncio.sleep(check_interval)
                    
            self.logger.info("監視期間が終了しました")
            
            # スクリーンショットを撮影
            await scraper.take_screenshot()
