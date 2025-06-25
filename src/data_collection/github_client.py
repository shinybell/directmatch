"""
GitHub APIクライアントモジュール
GitHub APIを使用してユーザー情報やリポジトリ情報を収集します
"""
import time
import requests
from typing import Dict, List, Any, Optional

import config
from src.utils.common import setup_logger, safe_api_call

# ロガーの設定
logger = setup_logger(__name__)

class GitHubClient:
    """
    GitHub APIとの通信を担当するクライアントクラス
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        GitHubクライアントを初期化します

        Args:
            api_key: GitHub APIのアクセストークン（省略時はconfigから取得）
        """
        self.api_key = api_key or config.GITHUB_API_KEY
        self.base_url = config.GITHUB_API_BASE_URL
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }

        # APIキーが設定されている場合は認証ヘッダーを追加
        if self.api_key:
            self.headers["Authorization"] = f"token {self.api_key}"

        # レートリミット関連
        self.rate_limit_remaining = 5000  # デフォルト値
        self.rate_limit_reset = 0

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict[str, Any]]:
        """
        GitHub APIへのリクエストを実行します
        レートリミットを考慮し、必要に応じて待機します

        Args:
            endpoint: APIエンドポイント（/を先頭に含む）
            params: リクエストパラメータ

        Returns:
            API応答の辞書またはNone（エラー時）
        """
        # レートリミットがほぼ消費されている場合は待機
        if self.rate_limit_remaining < 5:
            current_time = time.time()
            wait_time = max(0, self.rate_limit_reset - current_time + 1)
            if wait_time > 0:
                logger.info(f"GitHub APIのレートリミットに達しました。{wait_time:.1f}秒待機します")
                time.sleep(wait_time)

        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)

            # レートリミット情報を更新
            self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 5000))
            self.rate_limit_reset = int(response.headers.get("X-RateLimit-Reset", 0))

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"GitHub API エラー: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"GitHub APIリクエスト中にエラーが発生: {e}", exc_info=True)
            return None

    def search_users(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        キーワードでユーザーを検索します

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数

        Returns:
            ユーザー情報の辞書のリスト
        """
        endpoint = "/search/users"
        params = {
            "q": keyword,
            "sort": "followers",
            "order": "desc",
            "per_page": min(100, max_results)
        }

        response = self._make_request(endpoint, params)
        if response and "items" in response:
            users = response["items"][:max_results]
            logger.info(f"GitHub: '{keyword}'で{len(users)}人のユーザーを検索しました")
            return users

        logger.warning(f"GitHub: '{keyword}'でのユーザー検索に失敗しました")
        return []

    def get_user_details(self, username: str) -> Optional[Dict[str, Any]]:
        """
        指定されたユーザーの詳細情報を取得します

        Args:
            username: GitHubユーザー名

        Returns:
            ユーザー詳細情報の辞書またはNone（エラー時）
        """
        endpoint = f"/users/{username}"
        return self._make_request(endpoint)

    def get_user_repositories(self, username: str, max_repos: int = 5) -> List[Dict[str, Any]]:
        """
        指定されたユーザーのリポジトリ一覧を取得します

        Args:
            username: GitHubユーザー名
            max_repos: 取得する最大リポジトリ数

        Returns:
            リポジトリ情報の辞書のリスト
        """
        endpoint = f"/users/{username}/repos"
        params = {
            "sort": "stars",
            "direction": "desc",
            "per_page": min(100, max_repos)
        }

        response = self._make_request(endpoint, params)
        if response:
            return response[:max_repos]
        return []

    def get_repository_readme(self, owner: str, repo: str) -> Optional[str]:
        """
        指定されたリポジトリのREADMEコンテンツを取得します

        Args:
            owner: リポジトリ所有者のユーザー名
            repo: リポジトリ名

        Returns:
            READMEの内容（デコード済み）またはNone（エラー時）
        """
        endpoint = f"/repos/{owner}/{repo}/readme"
        response = self._make_request(endpoint)

        if response and "content" in response:
            import base64
            try:
                # Base64デコード
                content = base64.b64decode(response["content"]).decode("utf-8")
                return content
            except Exception as e:
                logger.error(f"README解析中にエラーが発生: {e}", exc_info=True)

        return None

    def extract_person_data(self, user_data: Dict[str, Any], repos_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        GitHubからの生データを候補者データモデルに変換します

        Args:
            user_data: GitHubユーザーの詳細データ
            repos_data: ユーザーのリポジトリ情報リスト

        Returns:
            候補者データ辞書
        """
        # 経験サマリ用のテキスト収集
        experience_texts = []

        # プロフィールの説明文
        if user_data.get("bio"):
            experience_texts.append(user_data["bio"])

        # リポジトリの説明
        for repo in repos_data[:5]:  # 上位5つのリポジトリ
            if repo.get("description"):
                experience_texts.append(f"Repository: {repo['name']} - {repo['description']}")

            # リポジトリの言語
            if repo.get("language"):
                experience_texts.append(f"Language: {repo['language']}")

        # 経験サマリ作成
        experience_summary = "\n".join(experience_texts)

        # メールアドレス（公開されている場合のみ）
        email = user_data.get("email")

        # 基本情報の抽出
        person_data = {
            "full_name": user_data.get("name") or user_data.get("login", ""),
            "email": email,
            "current_affiliation": user_data.get("company", ""),
            "github_username": user_data.get("login"),
            "personal_blog_url": user_data.get("blog"),
            "is_engineer": True,  # GitHub利用者はエンジニアと仮定
            "is_researcher": False,  # デフォルトはFalse（後で他のデータソースから判断）
            "experience_summary": experience_summary,
            "raw_github_data": user_data  # 生データも保存
        }

        return person_data
