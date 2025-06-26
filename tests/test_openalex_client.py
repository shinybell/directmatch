#!/usr/bin/env python3
"""
OpenAlexClientクラスのユニットテスト
"""
import sys
import os
import unittest
from unittest import mock

# ルートディレクトリをシステムパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_collection.openalex_client import OpenAlexClient


class TestOpenAlexClient(unittest.TestCase):
    """OpenAlexClientクラスのテスト"""

    def setUp(self):
        """各テスト前の準備"""
        self.client = OpenAlexClient()

    def test_init(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client.headers)
        self.assertIn("User-Agent", self.client.headers)
        self.assertEqual(self.client.request_delay, 0.1)  # 100msの遅延を確認

    @mock.patch('src.data_collection.openalex_client.requests.get')
    @mock.patch('src.data_collection.openalex_client.time.sleep')
    def test_make_request(self, mock_sleep, mock_get):
        """_make_requestメソッドのテスト"""
        # モックの設定
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response

        # テスト実行
        result = self.client._make_request('/test')

        # 検証
        mock_sleep.assert_called_once_with(0.1)
        mock_get.assert_called_once()
        self.assertEqual(result, {"test": "data"})

    @mock.patch('src.data_collection.openalex_client.OpenAlexClient._make_request')
    def test_search_authors(self, mock_make_request):
        """search_authorsメソッドのテスト"""
        # モックの設定
        expected_authors = [
            {"id": "A1", "display_name": "Author 1"},
            {"id": "A2", "display_name": "Author 2"}
        ]
        mock_make_request.return_value = {"results": expected_authors}

        # テスト実行
        authors = self.client.search_authors("machine learning", 10)

        # 検証
        self.assertEqual(authors, expected_authors)
        mock_make_request.assert_called_with("/authors", {
            "search": "machine learning",
            "per_page": 10
        })

    @mock.patch('src.data_collection.openalex_client.OpenAlexClient._make_request')
    def test_search_authors_error(self, mock_make_request):
        """search_authorsメソッドのエラー処理のテスト"""
        # モックの設定
        mock_make_request.return_value = None

        # テスト実行
        authors = self.client.search_authors("machine learning", 10)

        # 検証
        self.assertEqual(authors, [])
        mock_make_request.assert_called_once()

    @mock.patch('src.data_collection.openalex_client.OpenAlexClient._make_request')
    def test_get_author_details(self, mock_make_request):
        """get_author_detailsメソッドのテスト"""
        # モックの設定
        expected_data = {"id": "A1", "display_name": "Author 1"}
        mock_make_request.return_value = expected_data

        # テスト実行
        result = self.client.get_author_details("A1")

        # 検証
        self.assertEqual(result, expected_data)
        mock_make_request.assert_called_with("/authors/A1")

    @mock.patch('src.data_collection.openalex_client.OpenAlexClient._make_request')
    def test_get_author_works(self, mock_make_request):
        """get_author_worksメソッドのテスト"""
        # モックの設定
        expected_works = [
            {"id": "W1", "title": "Work 1"},
            {"id": "W2", "title": "Work 2"}
        ]
        mock_make_request.return_value = {"results": expected_works}

        # テスト実行
        result = self.client.get_author_works("A1", 5)

        # 検証
        self.assertEqual(result, expected_works)
        mock_make_request.assert_called_with("/works", {
            "filter": "author.id:A1",
            "per_page": 5,
            "sort": "cited_by_count:desc"
        })

    @mock.patch('src.data_collection.openalex_client.OpenAlexClient._make_request')
    def test_get_work_details(self, mock_make_request):
        """get_work_detailsメソッドのテスト"""
        # モックの設定
        expected_data = {"id": "W1", "title": "Work 1"}
        mock_make_request.return_value = expected_data

        # テスト実行
        result = self.client.get_work_details("W1")

        # 検証
        self.assertEqual(result, expected_data)
        mock_make_request.assert_called_with("/works/W1")

    def test_extract_person_data(self):
        """extract_person_dataメソッドのテスト"""
        # テストデータ
        author_data = {
            "display_name": "Test Author",
            "orcid": "https://orcid.org/0000-0001-2345-6789",
            "last_known_institution": {
                "display_name": "Test University"
            }
        }

        works_data = [
            {
                "title": "Test Paper 1",
                "abstract_inverted_index": {
                    "This": [0],
                    "is": [1],
                    "an": [2],
                    "abstract": [3]
                },
                "concepts": [
                    {"display_name": "Machine Learning"},
                    {"display_name": "Artificial Intelligence"}
                ]
            }
        ]

        # テスト実行
        person_data = self.client.extract_person_data(author_data, works_data)

        # 検証
        self.assertEqual(person_data["full_name"], "Test Author")
        self.assertEqual(person_data["orcid_id"], "0000-0001-2345-6789")
        self.assertEqual(person_data["current_affiliation"], "Test University")
        self.assertFalse(person_data["is_engineer"])
        self.assertTrue(person_data["is_researcher"])
        self.assertIn("所属: Test University", person_data["experience_summary"])
        self.assertIn("論文: Test Paper 1", person_data["experience_summary"])
        self.assertIn("概要: This is an abstract", person_data["experience_summary"])
        self.assertIn("研究分野: Machine Learning, Artificial Intelligence", person_data["experience_summary"])
        self.assertEqual(person_data["raw_openalex_data"], author_data)


if __name__ == "__main__":
    unittest.main()
