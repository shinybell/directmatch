"""
アプリケーション全体で使用される共通のユーティリティ関数
"""
import os
import uuid
import logging
import logging.handlers
from datetime import datetime
import config

# ロガーの設定
def setup_logger(name, level=None, log_to_file=True):
    """
    指定された名前のロガーを設定し、返します

    Args:
        name: ロガーの名前
        level: ログレベル（指定がない場合はconfigから取得）
        log_to_file: ファイルへの出力を行うかどうか

    Returns:
        設定されたロガーインスタンス
    """
    if level is None:
        level = getattr(logging, config.LOG_LEVEL, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # すでにハンドラが設定されている場合は追加しない
    if not logger.handlers:
        # コンソール出力用ハンドラ
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(config.LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # ファイル出力用ハンドラ（設定されている場合）
        if log_to_file and config.LOG_TO_FILE:
            # ログディレクトリの作成
            if not os.path.exists(config.LOG_DIR):
                os.makedirs(config.LOG_DIR)

            # 通常ログ用ファイルハンドラ（日付別）
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(config.LOG_DIR, f"{today}_{name}.log")

            # RotatingFileHandlerを使用してログファイルサイズを管理
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=config.LOG_MAX_SIZE,
                backupCount=config.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(config.LOG_FILE_FORMAT)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # エラーログ専用ハンドラ（オプション）
            if config.LOG_ERRORS_SEPARATELY:
                error_log_file = os.path.join(config.LOG_DIR, f"{today}_{name}_error.log")
                error_handler = logging.handlers.RotatingFileHandler(
                    error_log_file,
                    maxBytes=config.LOG_MAX_SIZE,
                    backupCount=config.LOG_BACKUP_COUNT,
                    encoding='utf-8'
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(file_formatter)
                logger.addHandler(error_handler)

    return logger

# ユニークID生成
def generate_id():
    """
    UUIDベースのユニークなIDを生成します
    """
    return str(uuid.uuid4())

# エラーハンドリング
def safe_api_call(func, *args, **kwargs):
    """
    API呼び出しを安全に行うためのラッパー関数
    例外が発生した場合はログを記録しNoneを返します
    """
    logger = setup_logger('api')
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"APIコール中にエラーが発生: {e}", exc_info=True)
        return None
