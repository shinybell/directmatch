"""
データ収集を統合するモジュール
複数のAPI（GitHub, Qiita, OpenAlex, KAKEN）からのデータ収集と同一人物特定を管理
"""
from typing import Dict, List, Any, Optional, Set
import concurrent.futures
from sqlalchemy.orm import Session

from src.data_collection.github_client import GitHubClient
from src.data_collection.qiita_client import QiitaClient
from src.data_collection.openalex_client import OpenAlexClient
from src.data_collection.kaken_client import KakenClient
from src.database.crud import create_person, find_person_by_identifiers, update_person
from src.utils.common import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

class DataCollector:
    """
    複数のデータソースからのデータ収集と統合を担うクラス
    """
    def __init__(self):
        """
        データコレクタを初期化し、各APIクライアントを準備
        """
        self.github_client = GitHubClient()
        self.qiita_client = QiitaClient()
        self.openalex_client = OpenAlexClient()
        self.kaken_client = KakenClient()

    def collect_from_github(self, keyword: str, max_results: int = 10, db_session: Session = None) -> List[Dict[str, Any]]:
        """
        GitHubからデータを収集し、データベースに保存

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数
            db_session: データベースセッション

        Returns:
            収集された候補者データのリスト
        """
        logger.info(f"GitHubから '{keyword}' で候補者データ収集開始")
        collected_data = []

        try:
            # ユーザー検索
            users = self.github_client.search_users(keyword, max_results)

            for user in users:
                username = user.get("login")
                if not username:
                    continue

                # ユーザー詳細取得
                user_details = self.github_client.get_user_details(username)
                if not user_details:
                    continue

                # リポジトリ情報取得
                repos = self.github_client.get_user_repositories(username)

                # 候補者データに変換
                person_data = self.github_client.extract_person_data(user_details, repos)
                collected_data.append(person_data)

                # データベースに保存（セッションが提供されている場合）
                if db_session:
                    self._save_person_to_db(person_data, db_session)

            logger.info(f"GitHubから{len(collected_data)}人の候補者データを収集しました")
            return collected_data

        except Exception as e:
            logger.error(f"GitHubからのデータ収集中にエラーが発生: {e}", exc_info=True)
            return collected_data

    def collect_from_qiita(self, keyword: str, max_results: int = 10, db_session: Session = None) -> List[Dict[str, Any]]:
        """
        Qiitaからデータを収集し、データベースに保存

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数
            db_session: データベースセッション

        Returns:
            収集された候補者データのリスト
        """
        logger.info(f"Qiitaから '{keyword}' で候補者データ収集開始")
        collected_data = []

        try:
            # 記事検索
            items = self.qiita_client.search_items(keyword, max_results)

            # 重複を避けるため、ユーザーIDの集合を作成
            user_ids = set()
            for item in items:
                user = item.get("user", {})
                user_id = user.get("id")
                if user_id and user_id not in user_ids:
                    user_ids.add(user_id)

            # 各ユーザーの詳細情報を取得
            for user_id in list(user_ids)[:max_results]:
                # ユーザー詳細取得
                user_details = self.qiita_client.get_user_details(user_id)
                if not user_details:
                    continue

                # ユーザーの記事取得
                user_items = self.qiita_client.get_user_items(user_id)

                # 候補者データに変換
                person_data = self.qiita_client.extract_person_data(user_details, user_items)
                collected_data.append(person_data)

                # データベースに保存（セッションが提供されている場合）
                if db_session:
                    self._save_person_to_db(person_data, db_session)

            logger.info(f"Qiitaから{len(collected_data)}人の候補者データを収集しました")
            return collected_data

        except Exception as e:
            logger.error(f"Qiitaからのデータ収集中にエラーが発生: {e}", exc_info=True)
            return collected_data

    def collect_from_openalex(self, keyword: str, max_results: int = 10, db_session: Session = None) -> List[Dict[str, Any]]:
        """
        OpenAlexからデータを収集し、データベースに保存

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数
            db_session: データベースセッション

        Returns:
            収集された候補者データのリスト
        """
        logger.info(f"OpenAlexから '{keyword}' で候補者データ収集開始")
        collected_data = []

        try:
            # 著者検索
            authors = self.openalex_client.search_authors(keyword, max_results)

            for author in authors:
                author_id = author.get("id")
                if not author_id:
                    continue

                # 著者詳細取得（基本的に検索結果に詳細が含まれているため再取得は不要な場合もある）
                author_details = author

                # 論文情報取得
                works = self.openalex_client.get_author_works(author_id)

                # 候補者データに変換
                person_data = self.openalex_client.extract_person_data(author_details, works)
                collected_data.append(person_data)

                # データベースに保存（セッションが提供されている場合）
                if db_session:
                    self._save_person_to_db(person_data, db_session)

            logger.info(f"OpenAlexから{len(collected_data)}人の候補者データを収集しました")
            return collected_data

        except Exception as e:
            logger.error(f"OpenAlexからのデータ収集中にエラーが発生: {e}", exc_info=True)
            return collected_data

    def collect_from_kaken(self, keyword: str, max_results: int = 10, db_session: Session = None) -> List[Dict[str, Any]]:
        """
        KAKENからデータを収集し、データベースに保存

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数
            db_session: データベースセッション

        Returns:
            収集された候補者データのリスト
        """
        logger.info(f"KAKENから '{keyword}' で候補者データ収集開始")
        collected_data = []

        try:
            # 研究者検索
            researchers = self.kaken_client.search_researchers(keyword, max_results)

            for researcher in researchers:
                researcher_id = researcher.get("id")
                if not researcher_id:
                    continue

                # 研究者詳細は検索結果に含まれているため再取得は不要
                researcher_details = researcher

                # プロジェクト情報取得
                projects = self.kaken_client.get_researcher_projects(researcher_id)

                # 候補者データに変換
                person_data = self.kaken_client.extract_person_data(researcher_details, projects)
                collected_data.append(person_data)

                # データベースに保存（セッションが提供されている場合）
                if db_session:
                    self._save_person_to_db(person_data, db_session)

            logger.info(f"KAKENから{len(collected_data)}人の候補者データを収集しました")
            return collected_data

        except Exception as e:
            logger.error(f"KAKENからのデータ収集中にエラーが発生: {e}", exc_info=True)
            return collected_data

    def _save_person_to_db(self, person_data: Dict[str, Any], db_session: Session) -> Optional[str]:
        """
        候補者データをデータベースに保存
        R006に従って同一人物の特定と情報統合を行う

        Args:
            person_data: 候補者データ
            db_session: データベースセッション

        Returns:
            保存された候補者のID（同一人物が特定された場合は既存のID）
        """
        try:
            # 同一人物特定のための識別子を準備
            identifiers = {
                "email": person_data.get("email"),
                "orcid_id": person_data.get("orcid_id"),
                "github_username": person_data.get("github_username"),
                "full_name": person_data.get("full_name"),
                "current_affiliation": person_data.get("current_affiliation")
            }

            # 同一人物を検索
            existing_person = find_person_by_identifiers(db_session, identifiers)

            if existing_person:
                # 既存の候補者情報を更新
                logger.info(f"同一人物が特定されました: {existing_person.id} ({existing_person.full_name})")

                # experience_summaryを結合
                if person_data.get("experience_summary") and existing_person.experience_summary:
                    person_data["experience_summary"] = existing_person.experience_summary + "\n\n" + person_data["experience_summary"]

                # 各フラグの統合（どちらかがTrueならTrue）
                if existing_person.is_engineer:
                    person_data["is_engineer"] = True
                if existing_person.is_researcher:
                    person_data["is_researcher"] = True

                # 生データの取り込み
                for key, value in person_data.items():
                    if key.startswith("raw_") and value is not None:
                        setattr(existing_person, key, value)

                # 更新
                updated_person = update_person(db_session, existing_person.id, person_data)
                return updated_person.id if updated_person else None
            else:
                # 新規の候補者として登録
                new_person = create_person(db_session, person_data)
                logger.info(f"新規候補者を登録しました: {new_person.id} ({new_person.full_name})")
                return new_person.id

        except Exception as e:
            logger.error(f"候補者データ保存中にエラーが発生: {e}", exc_info=True)
            db_session.rollback()
            return None

    def collect_data(self, keywords: List[str], sources: Dict[str, bool], max_results_per_source: int = 10,
                     db_session: Session = None) -> int:
        """
        複数のデータソースから複数のキーワードでデータを収集

        Args:
            keywords: 検索キーワードのリスト
            sources: 使用するデータソースのフラグ辞書 {"github": True, "qiita": True, "openalex": True, "kaken": True}
            max_results_per_source: 各ソース・各キーワードあたりの最大結果数
            db_session: データベースセッション

        Returns:
            収集された候補者の総数
        """
        total_collected = 0

        for keyword in keywords:
            # 各キーワードごとに各データソースから収集
            if sources.get("github", False):
                github_data = self.collect_from_github(keyword, max_results_per_source, db_session)
                total_collected += len(github_data)

            if sources.get("qiita", False):
                qiita_data = self.collect_from_qiita(keyword, max_results_per_source, db_session)
                total_collected += len(qiita_data)

            if sources.get("openalex", False):
                openalex_data = self.collect_from_openalex(keyword, max_results_per_source, db_session)
                total_collected += len(openalex_data)

            if sources.get("kaken", False):
                kaken_data = self.collect_from_kaken(keyword, max_results_per_source, db_session)
                total_collected += len(kaken_data)

        return total_collected

    def collect_data_parallel(self, keywords: List[str], sources: Dict[str, bool], max_results_per_source: int = 10,
                              db_session: Session = None) -> int:
        """
        複数のデータソースから並行してデータを収集（実験的実装）
        注意: データベースへの書き込みが競合する可能性があるため、DBセッションの扱いに注意が必要

        Args:
            keywords: 検索キーワードのリスト
            sources: 使用するデータソースのフラグ辞書 {"github": True, "qiita": True, "openalex": True, "kaken": True}
            max_results_per_source: 各ソース・各キーワードあたりの最大結果数
            db_session: データベースセッション

        Returns:
            収集された候補者の総数
        """
        total_collected = 0
        tasks = []

        # 収集タスクを準備
        for keyword in keywords:
            if sources.get("github", False):
                tasks.append(("github", keyword, max_results_per_source))

            if sources.get("qiita", False):
                tasks.append(("qiita", keyword, max_results_per_source))

            if sources.get("openalex", False):
                tasks.append(("openalex", keyword, max_results_per_source))

            if sources.get("kaken", False):
                tasks.append(("kaken", keyword, max_results_per_source))

        # 並列実行（収集タスクが4つ以上ある場合のみ）
        if len(tasks) >= 4:
            collected_data = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_to_task = {
                    executor.submit(self._collect_data_from_source, source, keyword, max_results): (source, keyword)
                    for source, keyword, max_results in tasks
                }

                for future in concurrent.futures.as_completed(future_to_task):
                    source, keyword = future_to_task[future]
                    try:
                        data = future.result()
                        collected_data.extend(data)
                        logger.info(f"{source}から '{keyword}' の検索で{len(data)}件のデータを収集しました")
                    except Exception as e:
                        logger.error(f"{source}からのデータ収集中にエラーが発生: {e}", exc_info=True)

            # データをデータベースに保存
            if db_session:
                for person_data in collected_data:
                    self._save_person_to_db(person_data, db_session)

            total_collected = len(collected_data)

        else:
            # 少ない場合は順次実行
            total_collected = self.collect_data(keywords, sources, max_results_per_source, db_session)

        return total_collected

    def _collect_data_from_source(self, source: str, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """
        指定されたソースから指定されたキーワードでデータを収集

        Args:
            source: データソース名
            keyword: 検索キーワード
            max_results: 最大結果数

        Returns:
            収集されたデータリスト
        """
        if source == "github":
            return self.collect_from_github(keyword, max_results)
        elif source == "qiita":
            return self.collect_from_qiita(keyword, max_results)
        elif source == "openalex":
            return self.collect_from_openalex(keyword, max_results)
        elif source == "kaken":
            return self.collect_from_kaken(keyword, max_results)
        else:
            return []
