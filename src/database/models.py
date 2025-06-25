"""
データベースモデル（テーブル定義）を管理するモジュール
"""
from sqlalchemy import Column, String, Boolean, Float, DateTime, JSON
from sqlalchemy.sql import func
from datetime import datetime

from src.database.db_manager import Base
from src.utils.common import generate_id

class Person(Base):
    """
    候補者（エンジニア・研究者）のテーブル
    要件定義書のpersonsテーブルの仕様に準拠
    """
    __tablename__ = "persons"

    # 主キー
    id = Column(String, primary_key=True, default=generate_id)

    # 基本情報
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    current_affiliation = Column(String, nullable=True)

    # プロフィール識別子
    github_username = Column(String, nullable=True, unique=True)
    qiita_id = Column(String, nullable=True, unique=True)
    orcid_id = Column(String, nullable=True, unique=True)

    # 追加URL
    linkedin_url = Column(String, nullable=True)
    personal_blog_url = Column(String, nullable=True)

    # 候補者カテゴリフラグ
    is_researcher = Column(Boolean, nullable=False, default=False)
    is_engineer = Column(Boolean, nullable=False, default=False)

    # 経験情報（主要なNLP処理対象）
    experience_summary = Column(String, nullable=True)

    # 生データ（JSON形式）
    raw_github_data = Column(JSON, nullable=True)
    raw_qiita_data = Column(JSON, nullable=True)
    raw_openalex_data = Column(JSON, nullable=True)
    raw_kaken_data = Column(JSON, nullable=True)

    # 管理情報
    last_updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # UIでの表示用スコア（NLPマッチングスコア）
    match_score = Column(Float, nullable=True)

    def __repr__(self):
        """オブジェクトの文字列表現"""
        return f"<Person(id='{self.id}', name='{self.full_name}', affiliation='{self.current_affiliation}')>"

    def to_dict(self):
        """オブジェクトを辞書に変換"""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "current_affiliation": self.current_affiliation,
            "github_username": self.github_username,
            "qiita_id": self.qiita_id,
            "orcid_id": self.orcid_id,
            "linkedin_url": self.linkedin_url,
            "personal_blog_url": self.personal_blog_url,
            "is_researcher": self.is_researcher,
            "is_engineer": self.is_engineer,
            "experience_summary": self.experience_summary,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None,
            "match_score": self.match_score
        }
