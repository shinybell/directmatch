"""
テキスト間の適合度を計算するマッチングモジュール
TF-IDFとコサイン類似度を用いて、人材要件と候補者の適合度を計算する
"""
import numpy as np
from typing import List, Tuple, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.database.models import Person
from src.nlp_processing.preprocessor import preprocess_text
from src.utils.common import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

def prepare_corpus(requirements: str, persons: List[Person]) -> List[str]:
    """
    TF-IDF学習用のコーパスを準備する

    Args:
        requirements: マッチングする人材要件テキスト
        persons: 候補者リスト

    Returns:
        プリプロセス済みのコーパス（人材要件 + 各候補者の経験サマリ）
    """
    # 人材要件を最初に追加
    corpus = [requirements]

    # 候補者の経験サマリを追加
    for person in persons:
        experience = person.experience_summary
        if experience:
            corpus.append(experience)
        else:
            # 経験サマリがない場合は空文字列を追加（インデックスを保持するため）
            corpus.append("")

    return corpus

def create_tfidf_matrix(corpus: List[str]) -> Tuple[TfidfVectorizer, np.ndarray]:
    """
    コーパスからTF-IDF行列を作成する

    Args:
        corpus: プリプロセス済みのテキストコーパス

    Returns:
        TF-IDFベクトライザと作成されたTF-IDF行列のタプル
    """
    # 前処理済みテキストをスペースで結合した配列を作成
    processed_corpus = []

    for text in corpus:
        tokens = preprocess_text(text)
        processed_text = " ".join(tokens)
        processed_corpus.append(processed_text)

    # TF-IDFベクトライザの初期化と適用
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(processed_corpus)

    return vectorizer, tfidf_matrix

def compute_similarity_scores(tfidf_matrix: np.ndarray) -> np.ndarray:
    """
    TF-IDF行列からコサイン類似度スコアを計算する

    Args:
        tfidf_matrix: TF-IDF行列

    Returns:
        最初の文書と他の全文書とのコサイン類似度スコアの配列
    """
    # 最初の文書（人材要件）のベクトル
    query_vector = tfidf_matrix[0]

    # 全ての文書とのコサイン類似度を計算
    similarities = cosine_similarity(query_vector, tfidf_matrix)[0]

    # 自分自身との類似度（通常は1.0）を除外
    similarities = similarities[1:]

    return similarities

def match_requirements(requirements: str, persons: List[Person]) -> List[Tuple[str, float]]:
    """
    人材要件と候補者リストのマッチングを行い、スコアを返す

    Args:
        requirements: マッチングする人材要件テキスト
        persons: 候補者リスト

    Returns:
        (候補者ID, マッチングスコア)のタプルのリスト（スコア降順）
    """
    if not requirements or not persons:
        logger.warning("マッチング対象の人材要件または候補者リストが空です")
        return []

    try:
        # コーパスの準備
        corpus = prepare_corpus(requirements, persons)

        # TF-IDF行列の作成
        _, tfidf_matrix = create_tfidf_matrix(corpus)

        # 類似度スコアの計算
        similarity_scores = compute_similarity_scores(tfidf_matrix)

        # 候補者IDとスコアのペアを作成
        result_pairs = [(person.id, score) for person, score in zip(persons, similarity_scores)]

        # スコア降順でソート
        result_pairs.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"{len(result_pairs)}人の候補者に対するマッチングスコアを計算しました")
        return result_pairs

    except Exception as e:
        logger.error(f"マッチング処理中にエラーが発生: {e}", exc_info=True)
        return []
