#!/usr/bin/env python3
"""
Airリザーブ自動予約システム - メインエントリーポイント

使用方法:
    python main.py --mode monitor    # 監視モード
    python main.py --mode book       # 予約実行モード
    python main.py --mode schedule   # 定期実行モード
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from src.scraper import AirReserveScraper
from src.booker import AirReserveBooker
from src.notifier import NotificationManager
from src.config import validate_required_config, ConfigError


def setup_logging():
    """ログ設定を初期化"""
    import os
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # DEBUG環境変数に応じてログレベルを設定
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # ロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # ハンドラーをクリア
    root_logger.handlers.clear()
    
    # フォーマッター
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(log_dir / f"auto-booker-{datetime.now().strftime('%Y%m%d')}.log")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


async def main_async():
    """非同期メイン関数"""
    parser = argparse.ArgumentParser(description="Airリザーブ自動予約システム")
    parser.add_argument(
        "--mode", 
        choices=["monitor", "book", "schedule"], 
        default="schedule",
        help="実行モードを選択"
    )
    parser.add_argument(
        "--config", 
        default=".env",
        help="設定ファイルのパス"
    )
    
    args = parser.parse_args()
    
    # 環境変数読み込み
    load_dotenv(args.config)
    
    # ログ設定
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 設定のバリデーション
    try:
        validate_required_config()
    except ConfigError as e:
        logger.error(f"設定エラー: {e}")
        logger.error("必須設定項目が不足しています。.envファイルを確認してください。")
        sys.exit(1)
    
    logger.info(f"Airリザーブ自動予約システム開始 - モード: {args.mode}")
    
    try:
        if args.mode == "monitor":
            # 監視モード
            booker = AirReserveBooker()
            scraper = AirReserveScraper(booker=booker)  # bookerを設定
            await scraper.start_monitoring()
            
        elif args.mode == "book":
            # 予約実行モード
            logger.info("予約実行モード: 既存の予約可能枠を検出して予約を実行します")
            
            scraper = AirReserveScraper()
            booker = AirReserveBooker()
            scraper.booker = booker  # bookerを設定
            
            async with scraper:
                # カレンダーページを読み込み
                if not await scraper.load_calendar_page():
                    logger.error("カレンダーページの読み込みに失敗しました")
                    return
                
                # 予約可能枠を取得
                logger.info("予約可能枠を検索中...")
                available_slots = await scraper.get_available_slots(max_weeks=7)
                
                if not available_slots:
                    logger.warning("予約可能枠が見つかりませんでした")
                    return
                
                logger.info(f"{len(available_slots)}件の予約可能枠を発見")
                
                # 希望条件に合致する枠を探して予約を実行
                booking_success = False
                for slot in available_slots:
                    if booker.is_preferred_slot(slot):
                        logger.info(f"希望条件に合致する枠を発見: {slot['text']}")
                        logger.info("予約を実行します...")
                        
                        # 予約を実行
                        success = await booker.execute_booking(slot, scraper.page)
                        
                        if success:
                            logger.info(f"予約が成功しました: {slot['text']}")
                            booking_success = True
                            break  # 最初の成功で終了
                        else:
                            logger.warning(f"予約が失敗しました: {slot['text']}")
                
                if not booking_success:
                    logger.warning("希望条件に合致する枠の予約に失敗しました")
            
        elif args.mode == "schedule":
            # 定期実行モード
            from src.scheduler import Scheduler
            scheduler = Scheduler()
            scheduler.start()
            
    except KeyboardInterrupt:
        logger.info("プログラムが中断されました")
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        sys.exit(1)


def main():
    """メイン関数（非同期関数を実行）"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
