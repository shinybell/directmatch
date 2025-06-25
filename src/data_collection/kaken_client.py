"""
KAKEN APIクライアントモジュール
KAKEN APIを使用して研究者情報や研究課題情報を収集します
"""
import time
import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional

import config
from src.utils.common import setup_logger, safe_api_call

# ロガーの設定
logger = setup_logger(__name__)

class KakenClient:
    """
    KAKEN APIとの通信を担当するクライアントクラス
    研究者情報の検索のみに対応しています
    """
    def __init__(self):
        """
        KAKENクライアントを初期化します
        """
        self.base_url = config.KAKEN_API_BASE_URL

        # 適切なAPI使用のための制御
        self.request_delay = 0.5  # 500msの遅延

    def _extract_researchers_from_html(self, soup: BeautifulSoup, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        BeautifulSoupオブジェクトから研究者情報を抽出します

        Args:
            soup: BeautifulSoupオブジェクト
            max_results: 最大結果数

        Returns:
            研究者情報の辞書のリスト
        """
        results = []

        # 研究者リストの各アイテムを取得
        researchers = soup.select('.listitem.xfolkentry')

        for researcher in researchers[:max_results]:
            # 基本情報の取得
            name_elem = researcher.select_one('.item_mainTitle a')
            if not name_elem:
                continue

            name = name_elem.text.strip()
            # ID部分を取得 (例: (70213486))
            researcher_id = None
            if '(' in name and ')' in name:
                id_match = name.split('(')[-1].split(')')[0]
                if id_match.isdigit():
                    researcher_id = id_match
                    # IDの部分を除去
                    name = name.split('(')[0].strip()

            # プロフィールURL
            profile_url = name_elem.get('href', '')

            # 所属情報の取得
            affiliation = []
            affiliation_elem = researcher.select_one('tr:has(th:contains("所属")) td')
            if affiliation_elem:
                for line in affiliation_elem.stripped_strings:
                    if line.strip():
                        affiliation.append(line.strip())

            # キーワードの取得
            keywords = []
            keywords_elem = researcher.select_one('tr:has(th:contains("キーワード")) td')
            if keywords_elem:
                keywords = [a.text.strip() for a in keywords_elem.select('a')]

            # 研究課題数と研究成果数
            research_projects = 0
            research_projects_elem = researcher.select_one('tr:has(th:contains("研究課題数")) td')
            if research_projects_elem:
                try:
                    research_projects = int(research_projects_elem.text.strip().replace(',', ''))
                except:
                    pass

            research_results = 0
            research_results_elem = researcher.select_one('tr:has(th:contains("研究成果数")) td')
            if research_results_elem:
                try:
                    research_results = int(research_results_elem.text.strip().replace(',', ''))
                except:
                    pass

            # 結果を辞書として格納
            researcher_info = {
                'name': name,
                'researcher_id': researcher_id,
                'profile_url': profile_url,
                'affiliation': affiliation,
                'keywords': keywords,
                'research_projects_count': research_projects,
                'research_results_count': research_results
            }

            results.append(researcher_info)

        return results

    def _make_request(self, params: Dict) -> Optional[BeautifulSoup]:
        """
        KAKEN APIへのリクエストを実行します
        API使用ポリシーに従い、適切な間隔でリクエストを行います

        Args:
            params: リクエストパラメータ

        Returns:
            BeautifulSoupオブジェクトまたはNone（エラー時）
        """
        # 適切な間隔を空けるための遅延
        time.sleep(self.request_delay)

        # 基本パラメータを設定（appidを含める）
        base_params = {
            "appid": "gu782hFEjCChFcYxyeb9",  # APIキー
            "rw": 100  # 結果数
        }

        # パラメータをマージ
        all_params = {**base_params, **params}

        try:
            response = requests.get(self.base_url, params=all_params)

            if response.status_code == 200:
                # HTMLとしてパース
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup
            else:
                logger.error(f"KAKEN API エラー: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"KAKEN APIリクエスト中にエラーが発生: {e}", exc_info=True)
            return None

    def search_researchers(self, keyword: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        キーワードで研究者を検索します

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大結果数

        Returns:
            研究者情報の辞書のリスト
        """
        params = {
            "qf": keyword,  # 全文検索用クエリ
            "qd": "[審査区分:審査区分]大区分J OR [審査区分:審査希望区分(新学術領域研究)]複合領域",  # 審査区分による絞り込み
            "rw": min(100, max_results),  # 結果の数
            "od": "1"  # ソート順（1は関連度順）
        }

        soup = self._make_request(params)
        if not soup:
            logger.warning(f"KAKEN: '{keyword}'での研究者検索に失敗しました")
            return []

        # 検索結果を抽出
        results = self._extract_researchers_from_html(soup, max_results)
        logger.info(f"KAKEN: '{keyword}'で{len(results)}人の研究者を検索しました")
        return results

    def get_researcher_details(self, researcher_id: str) -> Optional[Dict[str, Any]]:
        """
        研究者IDの詳細情報を取得します

        Args:
            researcher_id: KAKEN研究者ID

        Returns:
            研究者詳細情報の辞書またはNone（エラー時）
        """
        params = {
            "qn": researcher_id,  # 研究者ID
            "qo": "author"  # 研究者で検索
        }

        soup = self._make_request(params)
        if not soup:
            logger.warning(f"KAKEN: 研究者ID '{researcher_id}' の詳細情報取得に失敗しました")
            return None

        # 研究者リストから最初の要素（該当する研究者）を抽出
        researchers = self._extract_researchers_from_html(soup, 1)
        if researchers:
            return researchers[0]
        return None

    def extract_person_data(self, researcher_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        KAKENからの生データを候補者データモデルに変換します

        Args:
            researcher_data: KAKEN研究者の詳細データ

        Returns:
            候補者データ辞書。researcher_dataがNoneの場合はNoneを返します
        """
        if researcher_data is None:
            return None

        # 経験サマリ用のテキスト収集
        experience_texts = []

        # 研究者の所属機関
        affiliations = researcher_data.get("affiliation", [])
        institution = ", ".join(affiliations) if affiliations else ""
        if institution:
            experience_texts.append(f"所属: {institution}")

        # キーワード
        keywords = researcher_data.get("keywords", [])
        if keywords:
            experience_texts.append(f"研究キーワード: {', '.join(keywords)}")

        # 研究課題数と研究成果数
        research_projects_count = researcher_data.get("research_projects_count", 0)
        research_results_count = researcher_data.get("research_results_count", 0)
        experience_texts.append(f"研究課題数: {research_projects_count}")
        experience_texts.append(f"研究成果数: {research_results_count}")

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

if __name__ == "__main__":
    # テスト用のコード
    client = KakenClient()
    researchers = client.search_researchers("深層学習", 100)
    for researcher in researchers:
        print(researcher)

    if researchers:
        details = client.get_researcher_details(researchers[0]['researcher_id'])
        print(details)

        person_data = client.extract_person_data(details)
        print(person_data)
