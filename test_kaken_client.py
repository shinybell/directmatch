#!/usr/bin/env python3
"""
KAKEN APIクライアントのテスト用スクリプト
"""
import sys
import os

# ルートディレクトリをシステムパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_collection.kaken_client import KakenClient
from pprint import pprint

def test_kaken_client():
    """KAKENクライアントの動作テスト"""
    client = KakenClient()

    # キーワードで研究者を検索
    print("\n=== 研究者検索テスト ===")
    researchers = client.search_researchers("深層学習", 5)
    print(f"検索結果: {len(researchers)}件")
    for i, researcher in enumerate(researchers):
        print(f"\n--- 研究者 {i+1} ---")
        print(f"氏名: {researcher['name']}")
        print(f"研究者ID: {researcher['researcher_id']}")
        print(f"所属: {', '.join(researcher['affiliation'][:1]) if researcher['affiliation'] else ''}")
        print(f"キーワード: {', '.join(researcher['keywords'][:3]) if researcher['keywords'] else ''}")

    # 研究者IDから詳細情報を取得
    if researchers and researchers[0]['researcher_id']:
        researcher_id = researchers[0]['researcher_id']
        print(f"\n=== 研究者詳細テスト (ID: {researcher_id}) ===")
        researcher_detail = client.get_researcher_details(researcher_id)
        if researcher_detail:
            print(f"氏名: {researcher_detail['name']}")
            print(f"所属: {', '.join(researcher_detail['affiliation'][:1]) if researcher_detail['affiliation'] else ''}")
            print(f"キーワード: {', '.join(researcher_detail['keywords'][:5]) if researcher_detail['keywords'] else ''}")

        # 研究者のプロジェクトを取得
        print(f"\n=== 研究者プロジェクトテスト (ID: {researcher_id}) ===")
        projects = client.get_researcher_projects(researcher_id, 3)
        print(f"プロジェクト数: {len(projects)}")
        for i, project in enumerate(projects):
            print(f"\n--- プロジェクト {i+1} ---")
            print(f"タイトル: {project['title']}")
            print(f"プロジェクトID: {project['project_id']}")
            print(f"期間: {project.get('period', '')}")
            print(f"キーワード: {', '.join(project['keywords'][:3]) if project['keywords'] else ''}")

        # データモデル変換テスト
        if projects:
            print("\n=== データモデル変換テスト ===")
            person_data = client.extract_person_data(researcher_detail, projects)
            print(f"氏名: {person_data['full_name']}")
            print(f"所属: {person_data['current_affiliation']}")
            print(f"研究者: {person_data['is_researcher']}")
            print(f"エンジニア: {person_data['is_engineer']}")
            print("経験サマリ:")
            print(person_data['experience_summary'][:500] + "..." if len(person_data['experience_summary']) > 500 else person_data['experience_summary'])

    # キーワードでプロジェクトを検索
    print("\n=== プロジェクト検索テスト ===")
    projects = client.search_projects("人工知能", 5)
    print(f"検索結果: {len(projects)}件")
    for i, project in enumerate(projects):
        print(f"\n--- プロジェクト {i+1} ---")
        print(f"タイトル: {project['title']}")
        print(f"研究代表者: {project.get('researcher_name', '')}")
        print(f"プロジェクトID: {project['project_id']}")
        print(f"期間: {project.get('period', '')}")

if __name__ == "__main__":
    test_kaken_client()
