#!/usr/bin/env python3
"""
QiitaClientクラスのユニットテスト
"""
import sys
import os
import unittest
from unittest import mock

# ルートディレクトリをシステムパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_collection.qiita_client import QiitaClient


class TestQiitaClient(unittest.TestCase):
    """QiitaClientクラスのテスト"""

    def setUp(self):
        """各テスト前の準備"""
        self.client = QiitaClient()

    def test_init(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client.headers)
        self.assertIn("Content-Type", self.client.headers)

    @mock.patch('src.data_collection.qiita_client.requests.get')
    def test_make_request(self, mock_get):
        """_make_requestメソッドのテスト"""
        # モックの設定
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.headers = {"Rate-Remaining": "50", "Rate-Reset": "1000"}
        mock_get.return_value = mock_response

        # テスト実行
        result = self.client._make_request('/test')

        # 検証
        mock_get.assert_called_once()
        self.assertEqual(result, {"test": "data"})
        self.assertEqual(self.client.rate_limit_remaining, 50)

    @mock.patch('src.data_collection.qiita_client.QiitaClient._make_request')
    def test_search_items(self, mock_make_request):
        """search_itemsメソッドのテスト"""
        # モックの設定
        expected_items = [{"title": "テスト記事", "id": "123"}]
        mock_make_request.return_value = expected_items

        # テスト実行
        items = self.client.search_items("python", 10)

        # 検証
        self.assertEqual(items, expected_items)
        mock_make_request.assert_called_with("/items", {"query": "python", "per_page": 10})

    def test_extract_person_data(self):
        """extract_person_dataメソッドのテスト"""
        # テストデータ
        user_data = {
            "id": "testuser",
            "name": "テストユーザー",
            "organization": "テスト株式会社",
            "description": "Python開発者です",
            "website_url": "https://example.com"
        }

        items_data = [
            {
                "title": "Pythonの基本",
                "tags": [{"name": "Python"}, {"name": "初心者"}]
            },
            {
                "title": "Djangoの使い方",
                "tags": [{"name": "Django"}, {"name": "Web"}]
            }
        ]

        # テスト実行
        person_data = self.client.extract_person_data(user_data, items_data)

        # 検証
        self.assertEqual(person_data["full_name"], "テストユーザー")
        self.assertEqual(person_data["qiita_id"], "testuser")
        self.assertEqual(person_data["current_affiliation"], "テスト株式会社")
        self.assertEqual(person_data["personal_blog_url"], "https://example.com")
        self.assertTrue(person_data["is_engineer"])
        self.assertFalse(person_data["is_researcher"])
        self.assertIn("Python開発者です", person_data["experience_summary"])
        self.assertIn("記事: Pythonの基本", person_data["experience_summary"])
        self.assertIn("タグ: Python, 初心者", person_data["experience_summary"])


if __name__ == "__main__":
    unittest.main()
