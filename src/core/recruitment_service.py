"""
リクルートメントサービスのコアロジックを提供するモジュール
データ収集、NLP処理、データベース操作を連携させ、採用活動の主要機能を実装
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from src.database.db_manager import get_db, init_db
from src.database.crud import (
    get_all_persons, get_person_by_id, search_persons,
    update_match_scores
)
from src.database.models import Person
from src.data_collection.collector import DataCollector
from src.nlp_processing.matcher import match_requirements
from src.utils.common import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

class RecruitmentService:
    """
    採用活動の主要サービスを提供するクラス
    """
    def __init__(self):
        """
        リクルートメントサービスを初期化
        """
        # データベースの初期化
        init_db()

        # データコレクタの初期化
        self.collector = DataCollector()

    def get_all_persons(self, skip: int = 0, limit: int = 100) -> List[Person]:
        """
        すべての候補者を取得

        Args:
            skip: スキップする件数
            limit: 取得する最大件数

        Returns:
            候補者オブジェクトのリスト
        """
        db = get_db()
        try:
            return get_all_persons(db, skip, limit)
        finally:
            db.close()

    def get_person_by_id(self, person_id: str) -> Optional[Person]:
        """
        IDで候補者を検索

        Args:
            person_id: 候補者ID

        Returns:
            候補者オブジェクトまたはNone（見つからない場合）
        """
        db = get_db()
        try:
            return get_person_by_id(db, person_id)
        finally:
            db.close()

    def search_persons_by_keyword(self, persons: List[Person], keyword: str) -> List[Person]:
        """
        キーワードで候補者をフィルタリング
        既に取得済みの候補者リストから検索する場合に使用

        Args:
            persons: 検索対象の候補者リスト
            keyword: 検索キーワード

        Returns:
            キーワードにマッチする候補者のリスト
        """
        if not keyword:
            return persons

        # 小文字化してマッチングの精度を上げる
        keyword = keyword.lower()

        # 候補者のテキストデータを検索
        filtered_persons = []
        for person in persons:
            # 検索対象のテキストフィールドを結合
            search_text = " ".join(filter(None, [
                person.full_name,
                person.current_affiliation,
                person.experience_summary
            ])).lower()

            if keyword in search_text:
                filtered_persons.append(person)

        return filtered_persons

    def search_persons_in_db(self, keyword: str) -> List[Person]:
        """
        キーワードでデータベース内の候補者を検索

        Args:
            keyword: 検索キーワード

        Returns:
            キーワードにマッチする候補者のリスト
        """
        db = get_db()
        try:
            return search_persons(db, keyword)
        finally:
            db.close()

    def match_requirements_with_persons(self, requirements: str) -> List[Tuple[str, float]]:
        """
        人材要件に基づいて候補者とのマッチングを行う

        Args:
            requirements: 人材要件のテキスト

        Returns:
            (候補者ID, マッチングスコア)のタプルのリスト（スコア降順）
        """
        db = get_db()
        try:
            # 全候補者の取得
            all_persons = get_all_persons(db)

            # マッチングの実行
            match_results = match_requirements(requirements, all_persons)

            # マッチングスコアをデータベースに保存
            score_dict = {person_id: score for person_id, score in match_results}
            update_match_scores(db, score_dict)

            return match_results
        finally:
            db.close()

    def collect_data(self, source_configs: Optional[Dict[str, Dict[str, Any]]] = None,
                     keywords: Optional[List[str]] = None, sources: Optional[Dict[str, bool]] = None,
                     max_results_per_source: int = 10) -> int:
        """
        指定されたキーワードと情報源からデータを収集

        Args:
            source_configs: ソースごとの設定辞書
                例: {
                    "github": {"keywords": ["python", "machine learning"], "max_results": 20},
                    "qiita": {"keywords": ["AI", "深層学習"], "max_results": 15},
                    "openalex": {"keywords": ["natural language processing"], "max_results": 10},
                    "kaken": {"keywords": ["人工知能"], "max_results": 5}
                }
            keywords: 検索キーワードのリスト（後方互換性のため）
            sources: 使用するデータソースのフラグ辞書 {"github": True, "qiita": True, "openalex": True, "kaken": True}（後方互換性のため）
            max_results_per_source: 各ソース・各キーワードあたりの最大結果数（後方互換性のため）

        Returns:
            収集された候補者の総数
        """
        db = get_db()
        try:
            total_collected = self.collector.collect_data(
                source_configs=source_configs,
                keywords=keywords,
                sources=sources,
                max_results_per_source=max_results_per_source,
                db_session=db
            )
            return total_collected
        finally:
            db.close()

    def collect_data_parallel(self, source_configs: Optional[Dict[str, Dict[str, Any]]] = None,
                            keywords: Optional[List[str]] = None, sources: Optional[Dict[str, bool]] = None,
                            max_results_per_source: int = 10) -> int:
        """
        指定されたキーワードと情報源からデータを並列収集

        Args:
            source_configs: ソースごとの設定辞書
                例: {
                    "github": {"keywords": ["python", "machine learning"], "max_results": 20},
                    "qiita": {"keywords": ["AI", "深層学習"], "max_results": 15},
                    "openalex": {"keywords": ["natural language processing"], "max_results": 10},
                    "kaken": {"keywords": ["人工知能"], "max_results": 5}
                }
            keywords: 検索キーワードのリスト（後方互換性のため）
            sources: 使用するデータソースのフラグ辞書 {"github": True, "qiita": True, "openalex": True, "kaken": True}（後方互換性のため）
            max_results_per_source: 各ソース・各キーワードあたりの最大結果数（後方互換性のため）

        Returns:
            収集された候補者の総数
        """
        db = get_db()
        try:
            total_collected = self.collector.collect_data_parallel(
                source_configs=source_configs,
                keywords=keywords,
                sources=sources,
                max_results_per_source=max_results_per_source,
                db_session=db
            )
            return total_collected
        finally:
            db.close()

    def reset_database(self):
        """
        データベース内の人材リストをリセット（全データ削除）

        Returns:
            削除された候補者の数
        """
        from src.database.crud import delete_all_persons
        db = get_db()
        try:
            deleted_count = delete_all_persons(db)
            return deleted_count
        finally:
            db.close()
