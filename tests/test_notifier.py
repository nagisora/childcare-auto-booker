"""
NotificationManagerのテスト
"""

import pytest
import logging
from src.notifier import NotificationManager


class TestNotificationManager:
    """NotificationManagerクラスのテスト"""
    
    def test_init(self):
        """初期化のテスト"""
        notifier = NotificationManager()
        assert notifier.notify_success is True
        assert notifier.notify_failure is True
        
    def test_notify_booking_success(self, sample_slot, caplog):
        """予約成功通知のテスト"""
        notifier = NotificationManager()
        
        with caplog.at_level(logging.INFO):
            notifier.notify_booking_success(sample_slot)
            
        assert "予約成功" in caplog.text
        assert sample_slot['text'] in caplog.text
        
    def test_notify_booking_failure(self, sample_slot, caplog):
        """予約失敗通知のテスト"""
        notifier = NotificationManager()
        error_message = "満員です"
        
        with caplog.at_level(logging.ERROR):
            notifier.notify_booking_failure(sample_slot, error_message)
            
        assert "予約失敗" in caplog.text
        assert error_message in caplog.text
        
    def test_notify_new_slot_detected(self, sample_slot, caplog):
        """新規枠検出通知のテスト"""
        notifier = NotificationManager()
        
        with caplog.at_level(logging.INFO):
            notifier.notify_new_slot_detected(sample_slot)
            
        assert "新規予約枠を検出" in caplog.text
        
    def test_notify_monitoring_start(self, caplog):
        """監視開始通知のテスト"""
        notifier = NotificationManager()
        release_datetime = "2024-11-01 09:30:00"
        
        with caplog.at_level(logging.INFO):
            notifier.notify_monitoring_start(release_datetime)
            
        assert "予約枠監視を開始" in caplog.text
        assert release_datetime in caplog.text
        
    def test_notify_monitoring_end(self, caplog):
        """監視終了通知のテスト"""
        notifier = NotificationManager()
        
        with caplog.at_level(logging.INFO):
            notifier.notify_monitoring_end()
            
        assert "予約枠監視を終了" in caplog.text
