#!/usr/bin/env python3
"""
Airリザーブ自動予約システム - メインエントリーポイント

使用方法:
    python main.py --mode monitor    # 監視モード
    python main.py --mode book       # 予約実行モード
    python main.py --mode schedule   # 定期実行モード
"""

import argparse
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


def setup_logging():
    """ログ設定を初期化"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f"auto-booker-{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """メイン関数"""
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
    
    logger.info(f"Airリザーブ自動予約システム開始 - モード: {args.mode}")
    
    try:
        if args.mode == "monitor":
            # 監視モード
            scraper = AirReserveScraper()
            scraper.start_monitoring()
            
        elif args.mode == "book":
            # 予約実行モード
            booker = AirReserveBooker()
            booker.execute_booking()
            
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


if __name__ == "__main__":
    main()
