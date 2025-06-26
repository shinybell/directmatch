#!/usr/bin/env python3
"""
GitHubClientクラスのユニットテスト
"""
import sys
import os
import unittest
from unittest import mock

# ルートディレクトリをシステムパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_collection.github_client import GitHubClient


class TestGitHubClient(unittest.TestCase):
    """GitHubClientクラスのテスト"""

    def setUp(self):
        """各テスト前の準備"""
        self.client = GitHubClient()

    def test_init(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client.headers)
        self.assertIn("Accept", self.client.headers)
        self.assertEqual(self.client.rate_limit_remaining, 5000)
        self.assertEqual(self.client.rate_limit_reset, 0)

    @mock.patch('src.data_collection.github_client.requests.get')
    def test_make_request(self, mock_get):
        """_make_requestメソッドのテスト"""
        # モックの設定
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.headers = {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "1000"}
        mock_get.return_value = mock_response

        # テスト実行
        result = self.client._make_request('/test')

        # 検証
        mock_get.assert_called_once()
        self.assertEqual(result, {"test": "data"})
        self.assertEqual(self.client.rate_limit_remaining, 50)
        self.assertEqual(self.client.rate_limit_reset, 1000)

    @mock.patch('src.data_collection.github_client.GitHubClient._make_request')
    def test_search_users(self, mock_make_request):
        """search_usersメソッドのテスト"""
        # モックの設定
        expected_users = [{"login": "user1", "name": "User 1"}, {"login": "user2", "name": "User 2"}]
        mock_make_request.return_value = {"items": expected_users}

        # テスト実行
        users = self.client.search_users("python", 10)

        # 検証
        self.assertEqual(users, expected_users)
        mock_make_request.assert_called_with("/search/users", {
            "q": "python",
            "sort": "followers",
            "order": "desc",
            "per_page": 10
        })

    @mock.patch('src.data_collection.github_client.GitHubClient._make_request')
    def test_search_users_error(self, mock_make_request):
        """search_usersメソッドのエラー処理のテスト"""
        # モックの設定
        mock_make_request.return_value = None

        # テスト実行
        users = self.client.search_users("python", 10)

        # 検証
        self.assertEqual(users, [])
        mock_make_request.assert_called_once()

    @mock.patch('src.data_collection.github_client.GitHubClient._make_request')
    def test_get_user_details(self, mock_make_request):
        """get_user_detailsメソッドのテスト"""
        # モックの設定
        expected_data = {"login": "testuser", "name": "Test User"}
        mock_make_request.return_value = expected_data

        # テスト実行
        result = self.client.get_user_details("testuser")

        # 検証
        self.assertEqual(result, expected_data)
        mock_make_request.assert_called_with("/users/testuser")

    @mock.patch('src.data_collection.github_client.GitHubClient._make_request')
    def test_get_user_repositories(self, mock_make_request):
        """get_user_repositoriesメソッドのテスト"""
        # モックの設定
        expected_repos = [
            {"name": "repo1", "description": "Test repo 1", "language": "Python"},
            {"name": "repo2", "description": "Test repo 2", "language": "JavaScript"}
        ]
        mock_make_request.return_value = expected_repos

        # テスト実行
        result = self.client.get_user_repositories("testuser", 5)

        # 検証
        self.assertEqual(result, expected_repos)
        mock_make_request.assert_called_with("/users/testuser/repos", {
            "sort": "stars",
            "direction": "desc",
            "per_page": 5
        })

    @mock.patch('src.data_collection.github_client.GitHubClient._make_request')
    def test_get_repository_readme(self, mock_make_request):
        """get_repository_readmeメソッドのテスト"""
        # モックの設定
        import base64
        test_content = "# Test README\nThis is a test readme."
        encoded_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        mock_make_request.return_value = {"content": encoded_content}

        # テスト実行
        result = self.client.get_repository_readme("testowner", "testrepo")

        # 検証
        self.assertEqual(result, test_content)
        mock_make_request.assert_called_with("/repos/testowner/testrepo/readme")

    def test_extract_person_data(self):
        """extract_person_dataメソッドのテスト"""
        # テストデータ
        user_data = {
            "login": "testuser",
            "name": "Test User",
            "company": "Test Company",
            "bio": "Python developer",
            "blog": "https://example.com",
            "email": "test@example.com"
        }

        repos_data = [
            {"name": "repo1", "description": "Test repo 1", "language": "Python"},
            {"name": "repo2", "description": "Test repo 2", "language": "JavaScript"}
        ]

        # テスト実行
        person_data = self.client.extract_person_data(user_data, repos_data)

        # 検証
        self.assertEqual(person_data["full_name"], "Test User")
        self.assertEqual(person_data["github_username"], "testuser")
        self.assertEqual(person_data["current_affiliation"], "Test Company")
        self.assertEqual(person_data["personal_blog_url"], "https://example.com")
        self.assertEqual(person_data["email"], "test@example.com")
        self.assertTrue(person_data["is_engineer"])
        self.assertFalse(person_data["is_researcher"])
        self.assertIn("Python developer", person_data["experience_summary"])
        self.assertIn("Repository: repo1 - Test repo 1", person_data["experience_summary"])
        self.assertIn("Language: Python", person_data["experience_summary"])
        self.assertEqual(person_data["raw_github_data"], user_data)


if __name__ == "__main__":
    unittest.main()
