"""
アプリケーション全体で使用される共通のユーティリティ関数
"""
import uuid
import logging
import config

# ロガーの設定
def setup_logger(name, level=None):
    """
    指定された名前のロガーを設定し、返します
    """
    if level is None:
        level = config.LOG_LEVEL

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # ハンドラが既に設定されていなければ追加
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(config.LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

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
