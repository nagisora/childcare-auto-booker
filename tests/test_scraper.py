"""
AirReserveScraperのテスト
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.scraper import AirReserveScraper


class TestAirReserveScraper:
    """AirReserveScraperクラスのテスト"""
    
    def test_init(self):
        """初期化のテスト"""
        scraper = AirReserveScraper()
        assert scraper.target_url == "https://airrsv.net/kokoroto-azukari/calendar"
        assert scraper.headless is True
        assert scraper.debug is False
        assert scraper.monitor_duration == 10
        
    def test_is_available_slot_with_available_keyword(self):
        """予約可能キーワードを含む枠の判定テスト"""
        scraper = AirReserveScraper()
        
        # "空"キーワードを含む
        assert scraper._is_available_slot("残り3枠", "http://example.com", "slot") is True
        
        # "available"キーワードを含む
        assert scraper._is_available_slot("available", "http://example.com", "slot") is True
        
    def test_is_available_slot_with_exclude_keyword(self):
        """除外キーワードを含む枠の判定テスト"""
        scraper = AirReserveScraper()
        
        # "満員"キーワードを含む
        assert scraper._is_available_slot("満員", "http://example.com", "slot") is False
        
        # "disabled"クラスを含む
        assert scraper._is_available_slot("予約", "http://example.com", "disabled") is False
        
    def test_is_available_slot_with_href_only(self):
        """リンクのみの枠の判定テスト"""
        scraper = AirReserveScraper()
        
        # リンクがあり、除外キーワードがない
        assert scraper._is_available_slot("予約する", "http://example.com/reserve", "slot-item") is True
        
    def test_is_available_slot_empty_text(self):
        """テキストが空の枠の判定テスト"""
        scraper = AirReserveScraper()
        
        # テキストが空
        assert scraper._is_available_slot("", "http://example.com", "slot") is False
        
    @pytest.mark.asyncio
    async def test_load_calendar_page_success(self):
        """カレンダーページ読み込み成功のテスト"""
        scraper = AirReserveScraper()
        
        # モックページとレスポンスを作成
        mock_page = AsyncMock()
        mock_response = Mock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response
        mock_page.title.return_value = "予約カレンダー"
        mock_page.query_selector.return_value = Mock()  # カレンダー要素が存在
        
        scraper.page = mock_page
        
        result = await scraper.load_calendar_page()
        
        assert result is True
        mock_page.goto.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_load_calendar_page_failure(self):
        """カレンダーページ読み込み失敗のテスト"""
        scraper = AirReserveScraper()
        
        # モックページとレスポンスを作成
        mock_page = AsyncMock()
        mock_response = Mock()
        mock_response.status = 404
        mock_page.goto.return_value = mock_response
        
        scraper.page = mock_page
        
        result = await scraper.load_calendar_page()
        
        assert result is False
        
    @pytest.mark.asyncio
    async def test_get_available_slots(self):
        """予約可能枠取得のテスト"""
        scraper = AirReserveScraper()
        
        # モック要素を作成
        mock_element = AsyncMock()
        mock_element.inner_text.return_value = "残り3枠 10:00-12:00"
        mock_element.get_attribute.side_effect = lambda attr: {
            'href': '/reserve?id=123',
            'class': 'available'
        }.get(attr)
        
        # モックページを作成
        mock_page = AsyncMock()
        mock_page.query_selector_all.return_value = [mock_element]
        
        scraper.page = mock_page
        
        result = await scraper.get_available_slots()
        
        assert len(result) > 0
        assert result[0]['text'] == "残り3枠 10:00-12:00"
        assert result[0]['href'] == '/reserve?id=123'
        
    @pytest.mark.asyncio
    async def test_get_available_slots_empty(self):
        """予約可能枠が空の場合のテスト"""
        scraper = AirReserveScraper()
        
        # モックページを作成（要素なし）
        mock_page = AsyncMock()
        mock_page.query_selector_all.return_value = []
        
        scraper.page = mock_page
        
        result = await scraper.get_available_slots()
        
        assert len(result) == 0
        
    @pytest.mark.asyncio
    async def test_take_screenshot_success(self):
        """スクリーンショット撮影成功のテスト"""
        scraper = AirReserveScraper()
        
        # モックページを作成
        mock_page = AsyncMock()
        mock_page.screenshot.return_value = None
        
        scraper.page = mock_page
        
        result = await scraper.take_screenshot("test.png")
        
        assert result == "test.png"
        mock_page.screenshot.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_take_screenshot_no_page(self):
        """ページがない場合のスクリーンショットテスト"""
        scraper = AirReserveScraper()
        scraper.page = None
        
        result = await scraper.take_screenshot()
        
        assert result is None
