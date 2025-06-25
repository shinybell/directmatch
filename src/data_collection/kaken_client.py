"""
KAKEN APIクライアントモジュール
KAKEN APIを使用して研究者情報や研究課題情報を収集します
"""
import time
import requests
from typing import Dict, List, Any, Optional

import config
from src.utils.common import setup_logger, safe_api_call

# ロガーの設定
logger = setup_logger(__name__)

class KakenClient:
    """
    KAKEN APIとの通信を担当するクライアントクラス
    """
    def __init__(self):
        """
        KAKENクライアントを初期化します
        """
        self.base_url = config.KAKEN_API_BASE_URL

        # 適切なAPI使用のための制御
        self.request_delay = 0.5  # 500msの遅延

    def _make_request(self, params: Dict) -> Optional[Dict[str, Any]]:
        """
        KAKEN APIへのリクエストを実行します
        API使用ポリシーに従い、適切な間隔でリクエストを行います

        Args:
            params: リクエストパラメータ

        Returns:
            API応答の辞書またはNone（エラー時）
        """
        # 適切な間隔を空けるための遅延
        time.sleep(self.request_delay)

        # 基本パラメータを設定
        base_params = {
            "format": "json",
            "count": 100
        }

        # パラメータをマージ
        all_params = {**base_params, **params}

        try:
            response = requests.get(self.base_url, params=all_params)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"KAKEN API エラー: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"KAKEN APIリクエスト中にエラーが発生: {e}", exc_info=True)
            return None

    def search_researchers(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        キーワードで研究者を検索します

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数

        Returns:
            研究者情報の辞書のリスト
        """
        params = {
            "q": keyword,
            "type": "researcher",
            "count": min(100, max_results)
        }

        response = self._make_request(params)
        if response and "list" in response:
            researchers = response["list"][:max_results]
            logger.info(f"KAKEN: '{keyword}'で{len(researchers)}人の研究者を検索しました")
            return researchers

        logger.warning(f"KAKEN: '{keyword}'での研究者検索に失敗しました")
        return []

    def search_projects(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        キーワードで研究プロジェクトを検索します

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数

        Returns:
            研究プロジェクト情報の辞書のリスト
        """
        params = {
            "q": keyword,
            "type": "project",
            "count": min(100, max_results)
        }

        response = self._make_request(params)
        if response and "list" in response:
            projects = response["list"][:max_results]
            logger.info(f"KAKEN: '{keyword}'で{len(projects)}件の研究プロジェクトを検索しました")
            return projects

        logger.warning(f"KAKEN: '{keyword}'での研究プロジェクト検索に失敗しました")
        return []

    def get_researcher_details(self, researcher_id: str) -> Optional[Dict[str, Any]]:
        """
        研究者IDの詳細情報を取得します

        Args:
            researcher_id: KAKEN研究者ID

        Returns:
            研究者詳細情報の辞書またはNone（エラー時）
        """
        params = {
            "id": researcher_id,
            "type": "researcher"
        }

        response = self._make_request(params)
        if response and "list" in response and len(response["list"]) > 0:
            return response["list"][0]
        return None

    def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        プロジェクトIDの詳細情報を取得します

        Args:
            project_id: KAKENプロジェクトID

        Returns:
            プロジェクト詳細情報の辞書またはNone（エラー時）
        """
        params = {
            "id": project_id,
            "type": "project"
        }

        response = self._make_request(params)
        if response and "list" in response and len(response["list"]) > 0:
            return response["list"][0]
        return None

    def get_researcher_projects(self, researcher_id: str, max_projects: int = 5) -> List[Dict[str, Any]]:
        """
        研究者に関連するプロジェクトを取得します

        Args:
            researcher_id: KAKEN研究者ID
            max_projects: 取得する最大プロジェクト数

        Returns:
            プロジェクト情報の辞書のリスト
        """
        params = {
            "id": researcher_id,
            "type": "project"
        }

        response = self._make_request(params)
        if response and "list" in response:
            return response["list"][:max_projects]
        return []

    def extract_person_data(self, researcher_data: Dict[str, Any], projects_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        KAKENからの生データを候補者データモデルに変換します

        Args:
            researcher_data: KAKEN研究者の詳細データ
            projects_data: 研究者のプロジェクト情報リスト

        Returns:
            候補者データ辞書
        """
        # 経験サマリ用のテキスト収集
        experience_texts = []

        # 研究者の所属機関
        institution = researcher_data.get("affiliation", "")
        if institution:
            experience_texts.append(f"所属: {institution}")

        # 研究分野
        research_field = researcher_data.get("research_area", "")
        if research_field:
            experience_texts.append(f"研究分野: {research_field}")

        # プロジェクト情報
        for project in projects_data[:5]:  # 上位5つのプロジェクト
            if project.get("title"):
                experience_texts.append(f"研究プロジェクト: {project['title']}")

            # 研究概要
            if project.get("summary"):
                experience_texts.append(f"概要: {project['summary']}")

            # キーワード
            keywords = project.get("keywords", [])
            if keywords and isinstance(keywords, list):
                experience_texts.append(f"キーワード: {', '.join(keywords)}")

        # 経験サマリ作成
        experience_summary = "\n".join(experience_texts)

        # 基本情報の抽出
        person_data = {
            "full_name": researcher_data.get("name", ""),
            "current_affiliation": institution,
            "is_engineer": False,  # デフォルトはFalse（後で他のデータソースから判断）
            "is_researcher": True,  # KAKEN研究者は研究者と仮定
            "experience_summary": experience_summary,
            "raw_kaken_data": researcher_data  # 生データも保存
        }

        return person_data
