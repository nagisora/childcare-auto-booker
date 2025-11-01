"""
通知機能

予約成功・失敗の通知を管理する
"""

import logging
from typing import Optional

from src.config import get_notify_success, get_notify_failure


class NotificationManager:
    """通知管理クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.notify_success = get_notify_success()
        self.notify_failure = get_notify_failure()
        
    def notify_booking_success(self, slot_info: dict):
        """予約成功の通知"""
        if not self.notify_success:
            return
            
        message = f"✅ 予約成功: {slot_info.get('text', 'Unknown')}"
        self.logger.info(message)
        
        # 将来的にメール通知やSlack通知を追加可能
        # self._send_email(message)
        # self._send_slack(message)
        
    def notify_booking_failure(self, slot_info: dict, error: str):
        """予約失敗の通知"""
        if not self.notify_failure:
            return
            
        message = f"❌ 予約失敗: {slot_info.get('text', 'Unknown')} - {error}"
        self.logger.error(message)
        
        # 将来的にメール通知やSlack通知を追加可能
        # self._send_email(message)
        # self._send_slack(message)
        
    def notify_new_slot_detected(self, slot_info: dict):
        """新規枠検出の通知"""
        message = f"🔍 新規予約枠を検出: {slot_info.get('text', 'Unknown')}"
        self.logger.info(message)
        
    def notify_monitoring_start(self, release_datetime: str):
        """監視開始の通知"""
        message = f"👀 予約枠監視を開始: {release_datetime}"
        self.logger.info(message)
        
    def notify_monitoring_end(self):
        """監視終了の通知"""
        message = "⏹️ 予約枠監視を終了"
        self.logger.info(message)
