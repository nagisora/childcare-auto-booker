"""
Schedulerのテスト
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from src.scheduler import Scheduler


class TestScheduler:
    """Schedulerクラスのテスト"""
    
    def test_init(self):
        """初期化のテスト"""
        scheduler = Scheduler()
        assert scheduler.notifier is not None
        assert isinstance(scheduler.release_datetime, datetime)
        assert scheduler.monitoring_active is False
        
    @patch('src.scheduler.schedule')
    def test_start_scheduling(self, mock_schedule):
        """スケジュール開始のテスト"""
        scheduler = Scheduler()
        
        # run_schedulerをモック化してすぐに終了させる
        with patch.object(scheduler, '_run_scheduler') as mock_run:
            scheduler.start()
            
        # スケジュールが設定されたことを確認
        mock_schedule.every().day.at.assert_called_once()
