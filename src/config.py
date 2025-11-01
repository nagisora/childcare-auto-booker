"""
設定管理モジュール

環境変数から設定を取得し、デフォルト値を提供する
URL管理を一元化し、設定値のバリデーションを行う
"""

import os
from datetime import datetime
from typing import List, Optional


# デフォルトURL定数
DEFAULT_PRODUCTION_URL = "https://airrsv.net/kokoroto-azukari/calendar"
DEFAULT_TEST_URL = "https://airrsv.net/platkokoro2020/calendar"


class ConfigError(Exception):
    """設定エラー"""
    pass


def get_target_url() -> str:
    """ターゲットURLを取得
    
    優先順位:
    1. TARGET_URL環境変数が設定されている場合（最優先）
    2. SITE_MODE環境変数が設定されている場合
       - SITE_MODE=test → テストURL
       - SITE_MODE=production または未設定 → 本番URL
    3. デフォルトとして本番URL
    
    Returns:
        str: ターゲットURL
    """
    # 1. TARGET_URLが直接指定されている場合は優先
    target_url = os.getenv("TARGET_URL")
    if target_url:
        return target_url
    
    # 2. SITE_MODEで切り替え
    site_mode = os.getenv("SITE_MODE", "production").lower()
    if site_mode == "test":
        return DEFAULT_TEST_URL
    
    # 3. デフォルトは本番URL
    return DEFAULT_PRODUCTION_URL


def get_bool_env(key: str, default: bool = False) -> bool:
    """ブール値環境変数を取得
    
    Args:
        key: 環境変数名
        default: デフォルト値
    
    Returns:
        bool: 環境変数の値
    """
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() == "true"


def get_int_env(key: str, default: int) -> int:
    """整数環境変数を取得
    
    Args:
        key: 環境変数名
        default: デフォルト値
    
    Returns:
        int: 環境変数の値
    
    Raises:
        ConfigError: 値が整数として解釈できない場合
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{key} must be an integer, got: {value}")


def get_str_env(key: str, default: str = "") -> str:
    """文字列環境変数を取得
    
    Args:
        key: 環境変数名
        default: デフォルト値
    
    Returns:
        str: 環境変数の値
    """
    return os.getenv(key, default)


def get_datetime_env(key: str, default: str) -> datetime:
    """日時環境変数を取得
    
    Args:
        key: 環境変数名
        default: デフォルト値（YYYY-MM-DD HH:MM:SS形式）
    
    Returns:
        datetime: 環境変数の値
    
    Raises:
        ConfigError: 値が日時形式として解釈できない場合
    """
    value = os.getenv(key, default)
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ConfigError(f"{key} must be in format 'YYYY-MM-DD HH:MM:SS', got: {value}")


def get_list_env(key: str, separator: str = ",", default: Optional[List[str]] = None) -> List[str]:
    """リスト環境変数を取得
    
    Args:
        key: 環境変数名
        separator: 区切り文字
        default: デフォルト値
    
    Returns:
        List[str]: 環境変数の値のリスト
    """
    if default is None:
        default = []
    value = os.getenv(key)
    if not value:
        return default
    return [item.strip() for item in value.split(separator) if item.strip()]


# スクレイパー設定
def get_headless() -> bool:
    """ヘッドレスモードを取得"""
    return get_bool_env("HEADLESS", True)


def get_debug() -> bool:
    """デバッグモードを取得"""
    return get_bool_env("DEBUG", False)


def get_test_site_mode() -> bool:
    """テストサイトモードを取得"""
    return get_bool_env("TEST_SITE_MODE", False)


def get_next_release_datetime() -> datetime:
    """次回予約公開日時を取得"""
    return get_datetime_env("NEXT_RELEASE_DATETIME", "2024-11-01 09:30:00")


def get_monitor_duration_minutes() -> int:
    """監視時間（分）を取得"""
    duration = get_int_env("MONITOR_DURATION_MINUTES", 10)
    if duration < 1:
        raise ConfigError("MONITOR_DURATION_MINUTES must be at least 1")
    return duration


# ブッカー設定
def get_dry_run() -> bool:
    """DRY_RUNモードを取得"""
    return get_bool_env("DRY_RUN", False)


def get_stop_before_submit() -> bool:
    """STOP_BEFORE_SUBMITを取得"""
    return get_bool_env("STOP_BEFORE_SUBMIT", True)


def get_require_manual_confirmation() -> bool:
    """REQUIRE_MANUAL_CONFIRMATIONを取得"""
    return get_bool_env("REQUIRE_MANUAL_CONFIRMATION", False)


def get_booker_name() -> str:
    """予約者氏名を取得"""
    return get_str_env("BOOKER_NAME")


def get_booker_name_kana() -> str:
    """予約者フリガナ（セイ）を取得"""
    return get_str_env("BOOKER_NAME_KANA")


def get_booker_name_kana_mei() -> str:
    """予約者フリガナ（メイ）を取得"""
    return get_str_env("BOOKER_NAME_KANA_MEI")


def get_booker_email() -> str:
    """予約者メールアドレスを取得"""
    return get_str_env("BOOKER_EMAIL")


def get_booker_phone() -> str:
    """予約者電話番号を取得"""
    return get_str_env("BOOKER_PHONE")


def get_child_name() -> str:
    """お子様の氏名を取得"""
    return get_str_env("CHILD_NAME")


def get_child_age() -> str:
    """お子様の年齢を取得"""
    return get_str_env("CHILD_AGE")


def get_preferred_days() -> List[str]:
    """希望曜日を取得"""
    return get_list_env("PREFERRED_DAYS", separator=",")


def get_preferred_time_start() -> str:
    """希望開始時間を取得"""
    return get_str_env("PREFERRED_TIME_START", "09:00")


def get_preferred_time_end() -> str:
    """希望終了時間を取得"""
    return get_str_env("PREFERRED_TIME_END", "17:00")


# 通知設定
def get_notify_success() -> bool:
    """予約成功通知を有効にするか"""
    return get_bool_env("NOTIFY_SUCCESS", True)


def get_notify_failure() -> bool:
    """予約失敗通知を有効にするか"""
    return get_bool_env("NOTIFY_FAILURE", True)


def validate_required_config() -> None:
    """必須設定項目のバリデーション
    
    Raises:
        ConfigError: 必須項目が不足している場合
    """
    required_vars = [
        ("BOOKER_NAME", get_booker_name()),
        ("BOOKER_EMAIL", get_booker_email()),
        ("BOOKER_PHONE", get_booker_phone()),
        ("CHILD_NAME", get_child_name()),
        ("CHILD_AGE", get_child_age()),
    ]
    
    missing = []
    for var_name, value in required_vars:
        if not value:
            missing.append(var_name)
    
    if missing:
        raise ConfigError(f"Required configuration variables are missing: {', '.join(missing)}")
