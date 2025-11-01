"""
設定管理モジュール

環境変数から設定を取得し、デフォルト値を提供する
URL管理を一元化
"""

import os


# デフォルトURL定数
DEFAULT_PRODUCTION_URL = "https://airrsv.net/kokoroto-azukari/calendar"
DEFAULT_TEST_URL = "https://airrsv.net/platkokoro2020/calendar"


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

