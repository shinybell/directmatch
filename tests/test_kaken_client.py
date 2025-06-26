#!/usr/bin/env python3
"""
KakenClientクラスのユニットテスト
"""
import sys
import os
import unittest
from unittest import mock

# ルートディレクトリをシステムパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_collection.kaken_client import KakenClient


class TestKakenClient(unittest.TestCase):
    """KakenClientクラスのテスト"""

    def setUp(self):
        """各テスト前の準備"""
        self.client = KakenClient()

    def test_init(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.base_url, "https://nrid.nii.ac.jp/opensearch/")

    @mock.patch('src.data_collection.kaken_client.requests.get')
    @mock.patch('src.data_collection.kaken_client.BeautifulSoup')
    def test_make_request(self, mock_bs, mock_get):
        """_make_requestメソッドのテスト"""
        # モックの設定
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Test</body></html>"
        mock_get.return_value = mock_response

        mock_soup = mock.Mock()
        mock_bs.return_value = mock_soup

        # テスト実行
        result = self.client._make_request({"test": "param"})

        # 検証
        mock_get.assert_called_once()
        mock_bs.assert_called_once()
        self.assertEqual(result, mock_soup)

    @mock.patch('src.data_collection.kaken_client.KakenClient._make_request')
    def test_search_researchers(self, mock_make_request):
        """search_researchersメソッドのテスト"""
        # モックの設定
        mock_soup = mock.Mock()
        mock_make_request.return_value = mock_soup

        # _extract_researchers_from_htmlの戻り値をモック
        expected_researchers = [
            {"name": "研究者1", "researcher_id": "12345", "keywords": ["キーワード1"]},
            {"name": "研究者2", "researcher_id": "67890", "keywords": ["キーワード2"]}
        ]

        # _extract_researchers_from_htmlメソッドをモック
        with mock.patch.object(self.client, '_extract_researchers_from_html', return_value=expected_researchers) as mock_extract:
            # テスト実行
            researchers = self.client.search_researchers("深層学習", 5)

            # 検証
            mock_make_request.assert_called_once()
            mock_extract.assert_called_once_with(mock_soup, 5)
            self.assertEqual(researchers, expected_researchers)

    @mock.patch('src.data_collection.kaken_client.KakenClient._make_request')
    def test_get_researcher_details(self, mock_make_request):
        """get_researcher_detailsメソッドのテスト"""
        # モックの設定
        mock_soup = mock.Mock()
        mock_make_request.return_value = mock_soup

        expected_researcher = {"name": "テスト研究者", "researcher_id": "12345", "affiliation": ["テスト大学"]}

        with mock.patch.object(self.client, '_extract_researchers_from_html', return_value=[expected_researcher]) as mock_extract:
            # テスト実行
            result = self.client.get_researcher_details("12345")

            # 検証
            mock_make_request.assert_called_once()
            mock_extract.assert_called_once_with(mock_soup, 1)
            self.assertEqual(result, expected_researcher)

    def test_extract_person_data(self):
        """extract_person_dataメソッドのテスト"""
        # テストデータ
        researcher_data = {
            "name": "テスト研究者",
            "researcher_id": "12345",
            "affiliation": ["テスト大学", "コンピュータ科学部"],
            "keywords": ["深層学習", "自然言語処理", "画像認識"],
            "research_projects_count": 5,
            "research_results_count": 10
        }

        # テスト実行
        person_data = self.client.extract_person_data(researcher_data)

        # 検証
        self.assertEqual(person_data["full_name"], "テスト研究者")
        self.assertEqual(person_data["current_affiliation"], "テスト大学, コンピュータ科学部")
        self.assertTrue(person_data["is_researcher"])
        self.assertFalse(person_data["is_engineer"])
        self.assertIn("研究キーワード: 深層学習, 自然言語処理, 画像認識", person_data["experience_summary"])
        self.assertIn("研究課題数: 5", person_data["experience_summary"])
        self.assertIn("研究成果数: 10", person_data["experience_summary"])
        self.assertEqual(person_data["raw_kaken_data"], researcher_data)


if __name__ == "__main__":
    unittest.main()
