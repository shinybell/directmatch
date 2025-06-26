"""
データベースのマイグレーションを管理するモジュール
"""
import os
import sqlite3
import json
from sqlalchemy import create_engine, Column, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect

import config
from src.utils.common import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

def migrate_add_data_sources_column():
    """
    data_sourcesカラムを追加するマイグレーションを実行する関数
    既存のテーブルに新しいカラムを追加し、データソース情報を設定する
    """
    logger.info("マイグレーション実行: data_sourcesカラム追加")

    try:
        # SQLiteに直接接続
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()

        # カラムが既に存在するか確認
        cursor.execute("PRAGMA table_info(persons)")
        columns = [col[1] for col in cursor.fetchall()]

        if "data_sources" not in columns:
            # カラムを追加
            cursor.execute("ALTER TABLE persons ADD COLUMN data_sources TEXT")
            logger.info("data_sourcesカラムを追加しました")

            # 既存のデータからデータソース情報を設定
            cursor.execute("SELECT id, github_username, qiita_id, orcid_id, raw_github_data, raw_qiita_data, raw_openalex_data, raw_kaken_data FROM persons")
            rows = cursor.fetchall()

            for row in cursor.fetchall():
                id, github_username, qiita_id, orcid_id, raw_github_data, raw_qiita_data, raw_openalex_data, raw_kaken_data = row

                # データソースを特定
                sources = []
                if github_username or raw_github_data:
                    sources.append("github")
                if qiita_id or raw_qiita_data:
                    sources.append("qiita")
                if orcid_id or raw_openalex_data:
                    sources.append("openalex")
                if raw_kaken_data:
                    sources.append("kaken")

                # データソース情報を更新
                sources_json = json.dumps(sources)
                cursor.execute("UPDATE persons SET data_sources = ? WHERE id = ?", (sources_json, id))

            conn.commit()
            logger.info(f"{len(rows)}件のレコードにデータソース情報を設定しました")
        else:
            logger.info("data_sourcesカラムは既に存在しています")

        conn.close()

    except Exception as e:
        logger.error(f"マイグレーション中にエラーが発生: {e}", exc_info=True)
        raise

def run_migrations():
    """
    全てのマイグレーションを実行する関数
    """
    logger.info("データベースマイグレーション開始")

    try:
        # マイグレーションを順に実行
        migrate_add_data_sources_column()

        logger.info("データベースマイグレーション完了")
    except Exception as e:
        logger.error(f"マイグレーション実行中にエラーが発生: {e}", exc_info=True)
        raise
