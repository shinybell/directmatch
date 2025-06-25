"""
Qiita APIクライアントモジュール
Qiita APIを使用してユーザー情報や記事情報を収集します
"""
import time
import requests
from typing import Dict, List, Any, Optional

import config
from src.utils.common import setup_logger, safe_api_call

# ロガーの設定
logger = setup_logger(__name__)

class QiitaClient:
    """
    Qiita APIとの通信を担当するクライアントクラス
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Qiitaクライアントを初期化します

        Args:
            api_key: Qiita APIのアクセストークン（省略時はconfigから取得）
        """
        self.api_key = api_key or config.QIITA_API_KEY
        self.base_url = config.QIITA_API_BASE_URL
        self.headers = {
            "Content-Type": "application/json"
        }

        # APIキーが設定されている場合は認証ヘッダーを追加
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        # レートリミット
        self.rate_limit_remaining = 60  # デフォルト値
        self.rate_limit_reset = 0

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Any]:
        """
        Qiita APIへのリクエストを実行します
        レートリミットを考慮し、必要に応じて待機します

        Args:
            endpoint: APIエンドポイント（/を先頭に含む）
            params: リクエストパラメータ

        Returns:
            API応答の辞書/リストまたはNone（エラー時）
        """
        # レートリミットがほぼ消費されている場合は待機
        if self.rate_limit_remaining < 5:
            current_time = time.time()
            wait_time = max(0, self.rate_limit_reset - current_time + 1)
            if wait_time > 0:
                logger.info(f"Qiita APIのレートリミットに達しました。{wait_time:.1f}秒待機します")
                time.sleep(wait_time)

        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)

            # レートリミット情報を更新
            self.rate_limit_remaining = int(response.headers.get("Rate-Remaining", 60))
            self.rate_limit_reset = int(response.headers.get("Rate-Reset", 0))

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Qiita API エラー: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Qiita APIリクエスト中にエラーが発生: {e}", exc_info=True)
            return None

    def search_items(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        キーワードで記事を検索します

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数

        Returns:
            記事情報の辞書のリスト
        """
        endpoint = "/items"
        params = {
            "query": keyword,
            "per_page": min(100, max_results)
        }

        response = self._make_request(endpoint, params)
        if response:
            items = response[:max_results]
            logger.info(f"Qiita: '{keyword}'で{len(items)}件の記事を検索しました")
            return items

        logger.warning(f"Qiita: '{keyword}'での記事検索に失敗しました")
        return []

    def get_user_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        指定されたユーザーの詳細情報を取得します

        Args:
            user_id: QiitaユーザーID

        Returns:
            ユーザー詳細情報の辞書またはNone（エラー時）
        """
        endpoint = f"/users/{user_id}"
        return self._make_request(endpoint)

    def get_user_items(self, user_id: str, max_items: int = 5) -> List[Dict[str, Any]]:
        """
        指定されたユーザーの投稿記事一覧を取得します

        Args:
            user_id: QiitaユーザーID
            max_items: 取得する最大記事数

        Returns:
            記事情報の辞書のリスト
        """
        endpoint = f"/users/{user_id}/items"
        params = {
            "per_page": min(100, max_items)
        }

        response = self._make_request(endpoint, params)
        if response:
            return response[:max_items]
        return []

    def extract_person_data(self, user_data: Dict[str, Any], items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Qiitaからの生データを候補者データモデルに変換します

        Args:
            user_data: Qiitaユーザーの詳細データ
            items_data: ユーザーの記事情報リスト

        Returns:
            候補者データ辞書
        """
        # 経験サマリ用のテキスト収集
        experience_texts = []

        # プロフィールの説明文
        if user_data.get("description"):
            experience_texts.append(user_data["description"])

        # 記事タイトルとタグ
        for item in items_data[:5]:  # 上位5つの記事
            if item.get("title"):
                experience_texts.append(f"記事: {item['title']}")

            # 記事のタグ
            if item.get("tags"):
                tags = [tag.get("name", "") for tag in item["tags"] if tag.get("name")]
                experience_texts.append(f"タグ: {', '.join(tags)}")

        # 経験サマリ作成
        experience_summary = "\n".join(experience_texts)

        # 基本情報の抽出
        person_data = {
            "full_name": user_data.get("name") or user_data.get("id", ""),
            "qiita_id": user_data.get("id"),
            "current_affiliation": user_data.get("organization", ""),
            "personal_blog_url": user_data.get("website_url") or user_data.get("twitter_screen_name"),
            "is_engineer": True,  # Qiita利用者はエンジニアと仮定
            "is_researcher": False,  # デフォルトはFalse（後で他のデータソースから判断）
            "experience_summary": experience_summary,
            "raw_qiita_data": user_data  # 生データも保存
        }

        return person_data
