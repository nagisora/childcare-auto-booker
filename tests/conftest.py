"""pytest設定とフィクスチャ"""

import os
import sys
from pathlib import Path
import pytest

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# テスト用環境変数を設定
os.environ['TARGET_URL'] = 'https://airrsv.net/kokoroto-azukari/calendar'
os.environ['NEXT_RELEASE_DATETIME'] = '2024-11-01 09:30:00'
os.environ['MONITOR_DURATION_MINUTES'] = '10'
os.environ['HEADLESS'] = 'true'
os.environ['DEBUG'] = 'false'
os.environ['DRY_RUN'] = 'true'
os.environ['BOOKER_NAME'] = 'テスト太郎'
os.environ['BOOKER_EMAIL'] = 'test@example.com'
os.environ['BOOKER_PHONE'] = '090-1234-5678'
os.environ['CHILD_NAME'] = 'テスト花子'
os.environ['CHILD_AGE'] = '3'
os.environ['PREFERRED_DAYS'] = '月,水,金'
os.environ['PREFERRED_TIME_START'] = '09:00'
os.environ['PREFERRED_TIME_END'] = '17:00'
os.environ['NOTIFY_SUCCESS'] = 'true'
os.environ['NOTIFY_FAILURE'] = 'true'


@pytest.fixture
def sample_slot():
    """サンプル予約枠"""
    return {
        'text': '2024-11-15 10:00-12:00',
        'href': '/reserve?id=123',
        'class': 'available',
        'selector': 'a[href*="reserve"]',
        'timestamp': None
    }


@pytest.fixture
def sample_slot_with_preferred_day():
    """希望曜日を含むサンプル予約枠"""
    return {
        'text': '月曜日 10:00-12:00',
        'href': '/reserve?id=456',
        'class': 'available',
        'selector': 'a[href*="reserve"]',
        'timestamp': None
    }
