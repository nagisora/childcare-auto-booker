"""
AirReserveBookerのテスト
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.booker import AirReserveBooker


class TestAirReserveBooker:
    """AirReserveBookerクラスのテスト"""
    
    def test_init(self):
        """初期化のテスト"""
        booker = AirReserveBooker()
        assert booker.dry_run is True
        assert booker.booker_name == "テスト太郎"
        assert booker.booker_email == "test@example.com"
        assert booker.booker_phone == "090-1234-5678"
        assert booker.child_name == "テスト花子"
        assert booker.child_age == "3"
        
    def test_is_preferred_slot_with_day(self, sample_slot_with_preferred_day):
        """希望曜日を含む枠の判定テスト"""
        booker = AirReserveBooker()
        assert booker.is_preferred_slot(sample_slot_with_preferred_day) is True
        
    def test_is_preferred_slot_with_time(self):
        """希望時間帯を含む枠の判定テスト"""
        booker = AirReserveBooker()
        slot = {
            'text': '10:00-12:00',
            'href': '/reserve?id=123'
        }
        assert booker.is_preferred_slot(slot) is True
        
    def test_is_preferred_slot_outside_time(self):
        """希望時間外の枠の判定テスト"""
        booker = AirReserveBooker()
        slot = {
            'text': '18:00-20:00',  # 17:00以降
            'href': '/reserve?id=123'
        }
        assert booker.is_preferred_slot(slot) is False
        
    def test_is_preferred_slot_no_match(self):
        """条件に合わない枠の判定テスト"""
        booker = AirReserveBooker()
        slot = {
            'text': 'No time info',
            'href': '/reserve?id=123'
        }
        # 時間や曜日が見つからない場合はFalse
        assert booker.is_preferred_slot(slot) is False
        
    @pytest.mark.asyncio
    async def test_execute_booking_dry_run(self, sample_slot):
        """DRY_RUNモードでの予約実行テスト"""
        booker = AirReserveBooker()
        mock_page = AsyncMock()
        
        result = await booker.execute_booking(sample_slot, mock_page)
        
        # DRY_RUNモードでは常にTrueを返す
        assert result is True
        
    @pytest.mark.asyncio
    async def test_click_reservation_link_success(self, sample_slot):
        """予約リンククリック成功のテスト"""
        booker = AirReserveBooker()
        mock_page = AsyncMock()
        mock_response = Mock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response
        
        result = await booker._click_reservation_link(sample_slot, mock_page)
        
        assert result is True
        mock_page.goto.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_click_reservation_link_failure(self, sample_slot):
        """予約リンククリック失敗のテスト"""
        booker = AirReserveBooker()
        mock_page = AsyncMock()
        mock_response = Mock()
        mock_response.status = 404
        mock_page.goto.return_value = mock_response
        
        result = await booker._click_reservation_link(sample_slot, mock_page)
        
        assert result is False
        
    @pytest.mark.asyncio
    async def test_fill_booking_form(self):
        """予約フォーム入力のテスト"""
        booker = AirReserveBooker()
        mock_page = AsyncMock()
        
        # 呼び出し履歴を記録するためのリスト
        fill_calls = []
        
        # モック要素を作成
        mock_element = AsyncMock()
        mock_element.is_visible.return_value = True
        mock_element.get_attribute.return_value = 'INPUT'
        
        # fillメソッドをカスタムして呼び出しを記録
        async def mock_fill(value):
            fill_calls.append(value)
        
        mock_element.fill = mock_fill
        
        # すべてのquery_selectorで同じモック要素を返す
        mock_page.query_selector.return_value = mock_element
        
        result = await booker._fill_booking_form(mock_page)
        
        assert result is True
        # fillが複数回呼ばれたことを確認
        assert len(fill_calls) >= 3  # 最低でも名前、メール、電話番号の3つ
        # 予約者名、メール、電話番号が含まれていることを確認
        assert booker.booker_name in fill_calls
        assert booker.booker_email in fill_calls
        assert booker.booker_phone in fill_calls
