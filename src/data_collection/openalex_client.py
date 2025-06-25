"""
OpenAlex APIクライアントモジュール
OpenAlex APIを使用して研究者情報や論文情報を収集します
"""
import time
import requests
from typing import Dict, List, Any, Optional

import config
from src.utils.common import setup_logger, safe_api_call

# ロガーの設定
logger = setup_logger(__name__)

class OpenAlexClient:
    """
    OpenAlex APIとの通信を担当するクライアントクラス
    """
    def __init__(self, email: Optional[str] = None):
        """
        OpenAlexクライアントを初期化します

        Args:
            email: 利用者のメールアドレス（APIポリシーに従い提供、省略時はconfigから取得）
        """
        self.email = email or config.OPENALEX_EMAIL
        self.base_url = config.OPENALEX_API_BASE_URL

        # OpenAlexはAPIキーが不要ですが、ポリシーに従いメールアドレスを送信
        self.user_agent = f"DirectMatch/0.1 ({self.email})"
        self.headers = {
            "User-Agent": self.user_agent
        }

        # 適切なAPI使用のための制御
        self.request_delay = 0.1  # 100msの遅延

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict[str, Any]]:
        """
        OpenAlex APIへのリクエストを実行します
        API使用ポリシーに従い、適切な間隔でリクエストを行います

        Args:
            endpoint: APIエンドポイント（/を先頭に含む）
            params: リクエストパラメータ

        Returns:
            API応答の辞書またはNone（エラー時）
        """
        # 適切な間隔を空けるための遅延
        time.sleep(self.request_delay)

        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"OpenAlex API エラー: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"OpenAlex APIリクエスト中にエラーが発生: {e}", exc_info=True)
            return None

    def search_authors(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        キーワードで著者を検索します

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数

        Returns:
            著者情報の辞書のリスト
        """
        endpoint = "/authors"
        params = {
            "search": keyword,
            "per_page": min(100, max_results)
        }

        response = self._make_request(endpoint, params)
        if response and "results" in response:
            authors = response["results"][:max_results]
            logger.info(f"OpenAlex: '{keyword}'で{len(authors)}人の著者を検索しました")
            return authors

        logger.warning(f"OpenAlex: '{keyword}'での著者検索に失敗しました")
        return []

    def get_author_details(self, author_id: str) -> Optional[Dict[str, Any]]:
        """
        指定された著者IDの詳細情報を取得します

        Args:
            author_id: OpenAlex著者ID

        Returns:
            著者詳細情報の辞書またはNone（エラー時）
        """
        endpoint = f"/authors/{author_id}"
        return self._make_request(endpoint)

    def get_author_works(self, author_id: str, max_works: int = 5) -> List[Dict[str, Any]]:
        """
        指定された著者の論文一覧を取得します

        Args:
            author_id: OpenAlex著者ID
            max_works: 取得する最大論文数

        Returns:
            論文情報の辞書のリスト
        """
        endpoint = "/works"
        params = {
            "filter": f"author.id:{author_id}",
            "per_page": min(100, max_works),
            "sort": "cited_by_count:desc"  # 被引用数が多い順
        }

        response = self._make_request(endpoint, params)
        if response and "results" in response:
            return response["results"][:max_works]
        return []

    def get_work_details(self, work_id: str) -> Optional[Dict[str, Any]]:
        """
        指定された論文IDの詳細情報を取得します

        Args:
            work_id: OpenAlex論文ID

        Returns:
            論文詳細情報の辞書またはNone（エラー時）
        """
        endpoint = f"/works/{work_id}"
        return self._make_request(endpoint)

    def extract_person_data(self, author_data: Dict[str, Any], works_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        OpenAlexからの生データを候補者データモデルに変換します

        Args:
            author_data: OpenAlex著者の詳細データ
            works_data: 著者の論文情報リスト

        Returns:
            候補者データ辞書
        """
        # 経験サマリ用のテキスト収集
        experience_texts = []

        # 研究者の所属機関
        institution = ""
        if author_data.get("last_known_institution"):
            institution = author_data["last_known_institution"].get("display_name", "")
            experience_texts.append(f"所属: {institution}")

        # ORCID ID
        orcid_id = ""
        if author_data.get("orcid"):
            orcid_url = author_data["orcid"]
            # "https://orcid.org/0000-0002-1825-0097" 形式からIDのみ抽出
            if orcid_url and "orcid.org/" in orcid_url:
                orcid_id = orcid_url.split("orcid.org/")[-1]

        # 論文情報
        for work in works_data[:5]:  # 上位5つの論文
            if work.get("title"):
                experience_texts.append(f"論文: {work['title']}")

            # 論文の概要
            if work.get("abstract_inverted_index"):
                try:
                    # インバーテッドインデックスから抽象を再構築
                    idx = work["abstract_inverted_index"]
                    words = list(idx.keys())
                    abstract = " ".join([words[pos] for pos in sorted([pos for positions in idx.values() for pos in positions])])
                    experience_texts.append(f"概要: {abstract}")
                except Exception as e:
                    logger.warning(f"論文概要の再構築に失敗: {e}")

            # 研究分野
            if work.get("concepts"):
                concepts = [c.get("display_name", "") for c in work["concepts"][:3] if c.get("display_name")]
                if concepts:
                    experience_texts.append(f"研究分野: {', '.join(concepts)}")

        # 経験サマリ作成
        experience_summary = "\n".join(experience_texts)

        # 基本情報の抽出
        person_data = {
            "full_name": author_data.get("display_name", ""),
            "orcid_id": orcid_id,
            "current_affiliation": institution,
            "is_engineer": False,  # デフォルトはFalse（後で他のデータソースから判断）
            "is_researcher": True,  # OpenAlex著者は研究者と仮定
            "experience_summary": experience_summary,
            "raw_openalex_data": author_data  # 生データも保存
        }

        return person_data
