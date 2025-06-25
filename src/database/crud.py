"""
データベース操作（CRUD: Create, Read, Update, Delete）を提供するモジュール
"""
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.database.models import Person
from src.utils.common import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

# 候補者（Person）のCRUD操作

def create_person(db: Session, person_data: Dict[str, Any]) -> Person:
    """
    新しい候補者をデータベースに作成します。

    Args:
        db: データベースセッション
        person_data: 候補者データの辞書

    Returns:
        作成された候補者のオブジェクト
    """
    try:
        db_person = Person(**person_data)
        db.add(db_person)
        db.commit()
        db.refresh(db_person)
        logger.info(f"候補者を作成しました: {db_person.id} - {db_person.full_name}")
        return db_person
    except Exception as e:
        db.rollback()
        logger.error(f"候補者作成中にエラーが発生: {e}", exc_info=True)
        raise

def get_person_by_id(db: Session, person_id: str) -> Optional[Person]:
    """
    IDで候補者を検索します。

    Args:
        db: データベースセッション
        person_id: 候補者ID

    Returns:
        候補者オブジェクト。見つからない場合はNone。
    """
    return db.query(Person).filter(Person.id == person_id).first()

def get_all_persons(db: Session, skip: int = 0, limit: int = 100) -> List[Person]:
    """
    すべての候補者を取得します。

    Args:
        db: データベースセッション
        skip: スキップする件数
        limit: 取得する最大件数

    Returns:
        候補者オブジェクトのリスト
    """
    return db.query(Person).offset(skip).limit(limit).all()

def update_person(db: Session, person_id: str, update_data: Dict[str, Any]) -> Optional[Person]:
    """
    既存の候補者データを更新します。

    Args:
        db: データベースセッション
        person_id: 更新する候補者のID
        update_data: 更新するフィールドと値の辞書

    Returns:
        更新された候補者オブジェクト。見つからない場合はNone。
    """
    db_person = get_person_by_id(db, person_id)
    if db_person:
        try:
            for key, value in update_data.items():
                setattr(db_person, key, value)
            db.commit()
            db.refresh(db_person)
            logger.info(f"候補者を更新しました: {db_person.id} - {db_person.full_name}")
            return db_person
        except Exception as e:
            db.rollback()
            logger.error(f"候補者更新中にエラーが発生: {e}", exc_info=True)
            raise
    return None

def delete_person(db: Session, person_id: str) -> bool:
    """
    候補者を削除します。

    Args:
        db: データベースセッション
        person_id: 削除する候補者のID

    Returns:
        削除が成功したかどうかのブール値
    """
    db_person = get_person_by_id(db, person_id)
    if db_person:
        try:
            db.delete(db_person)
            db.commit()
            logger.info(f"候補者を削除しました: {person_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"候補者削除中にエラーが発生: {e}", exc_info=True)
            raise
    return False

def search_persons(db: Session, keyword: str) -> List[Person]:
    """
    キーワードで候補者を検索します。

    Args:
        db: データベースセッション
        keyword: 検索キーワード

    Returns:
        マッチする候補者のリスト
    """
    search = f"%{keyword}%"
    return db.query(Person).filter(
        or_(
            Person.full_name.ilike(search),
            Person.current_affiliation.ilike(search),
            Person.experience_summary.ilike(search)
        )
    ).all()

def find_person_by_identifiers(db: Session, identifiers: Dict[str, Any]) -> Optional[Person]:
    """
    識別子で候補者を検索します。
    同一人物検出用の関数です。

    Args:
        db: データベースセッション
        identifiers: 以下のいずれかの識別子の辞書
            - email: メールアドレス
            - orcid_id: ORCID ID
            - github_username: GitHubユーザー名
            - (full_name + current_affiliation): 氏名と所属の組み合わせ

    Returns:
        一致する候補者。見つからない場合はNone。
    """
    query = db.query(Person)

    # 優先順位に従って検索
    if identifiers.get('email'):
        person = query.filter(Person.email == identifiers['email']).first()
        if person:
            return person

    if identifiers.get('orcid_id'):
        person = query.filter(Person.orcid_id == identifiers['orcid_id']).first()
        if person:
            return person

    if identifiers.get('github_username'):
        person = query.filter(Person.github_username == identifiers['github_username']).first()
        if person:
            return person

    # 氏名と所属の完全一致
    if identifiers.get('full_name') and identifiers.get('current_affiliation'):
        person = query.filter(
            Person.full_name == identifiers['full_name'],
            Person.current_affiliation == identifiers['current_affiliation']
        ).first()
        if person:
            return person

    return None

def update_match_scores(db: Session, score_dict: Dict[str, float]) -> int:
    """
    候補者のマッチングスコアを一括で更新します。

    Args:
        db: データベースセッション
        score_dict: 候補者IDとマッチングスコアの辞書

    Returns:
        更新された候補者の数
    """
    updated_count = 0
    try:
        for person_id, score in score_dict.items():
            db_person = get_person_by_id(db, person_id)
            if db_person:
                db_person.match_score = score
                updated_count += 1

        db.commit()
        logger.info(f"{updated_count}件の候補者のマッチスコアを更新しました")
        return updated_count
    except Exception as e:
        db.rollback()
        logger.error(f"マッチスコア更新中にエラーが発生: {e}", exc_info=True)
        raise
