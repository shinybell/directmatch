"""
データベース接続と操作を管理するモジュール
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

import config
from src.utils.common import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

# SQLAlchemyのベースクラス
Base = declarative_base()

# データベースディレクトリの作成（存在しない場合）
os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)

# SQLiteエンジンの作成
engine = create_engine(
    config.DB_URL,
    connect_args={"check_same_thread": False},  # SQLiteは複数スレッドから安全に操作するための設定
    echo=False  # SQLクエリのロギングを無効（本番環境では通常False）
)

# セッションファクトリの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# スレッド固有のセッションを提供するためのセッションスコープ
db_session = scoped_session(SessionLocal)

def get_db():
    """
    データベースセッションを取得するためのヘルパー関数
    使用例：
        db = get_db()
        try:
            # DBを操作するコード
            ...
            db.commit()  # 変更を保存
        except Exception as e:
            db.rollback()  # エラー時はロールバック
            raise e
        finally:
            db.close()  # セッションを閉じる
    """
    db = db_session()
    try:
        return db
    finally:
        db.close()

def init_db():
    """
    データベースの初期化とテーブル作成を行う関数
    """
    logger.info("データベース初期化開始")
    try:
        # models.pyからのインポートは循環参照を避けるためにここで行う
        from src.database.models import Person

        # テーブル作成
        Base.metadata.create_all(bind=engine)
        logger.info("データベーステーブル作成完了")
    except Exception as e:
        logger.error(f"データベース初期化中にエラーが発生: {e}", exc_info=True)
        raise
