"""
NLPモデルの管理モジュール
TF-IDFベクトライザなどのモデルの保存・読み込みを行う
"""
import os
import pickle
from typing import Optional, Any
from sklearn.feature_extraction.text import TfidfVectorizer

import config
from src.utils.common import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

# モデルファイルのパス
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "models")
TFIDF_MODEL_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")

def ensure_models_dir():
    """
    モデルディレクトリの存在確認と作成
    """
    os.makedirs(MODELS_DIR, exist_ok=True)

def save_tfidf_vectorizer(vectorizer: TfidfVectorizer) -> bool:
    """
    TF-IDFベクトライザをファイルに保存

    Args:
        vectorizer: 保存するTF-IDFベクトライザ

    Returns:
        保存が成功したかのブール値
    """
    ensure_models_dir()

    try:
        with open(TFIDF_MODEL_PATH, 'wb') as f:
            pickle.dump(vectorizer, f)
        logger.info(f"TF-IDFベクトライザを保存しました: {TFIDF_MODEL_PATH}")
        return True
    except Exception as e:
        logger.error(f"TF-IDFベクトライザの保存に失敗: {e}", exc_info=True)
        return False

def load_tfidf_vectorizer() -> Optional[TfidfVectorizer]:
    """
    TF-IDFベクトライザをファイルから読み込み

    Returns:
        読み込んだTF-IDFベクトライザまたはNone（失敗時）
    """
    if not os.path.exists(TFIDF_MODEL_PATH):
        logger.warning(f"TF-IDFベクトライザファイルが見つかりません: {TFIDF_MODEL_PATH}")
        return None

    try:
        with open(TFIDF_MODEL_PATH, 'rb') as f:
            vectorizer = pickle.load(f)
        logger.info(f"TF-IDFベクトライザを読み込みました: {TFIDF_MODEL_PATH}")
        return vectorizer
    except Exception as e:
        logger.error(f"TF-IDFベクトライザの読み込みに失敗: {e}", exc_info=True)
        return None

def save_model(model: Any, model_name: str) -> bool:
    """
    任意のモデルをファイルに保存

    Args:
        model: 保存するモデル
        model_name: モデル名（ファイル名になります）

    Returns:
        保存が成功したかのブール値
    """
    ensure_models_dir()
    model_path = os.path.join(MODELS_DIR, f"{model_name}.pkl")

    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"モデル {model_name} を保存しました: {model_path}")
        return True
    except Exception as e:
        logger.error(f"モデル {model_name} の保存に失敗: {e}", exc_info=True)
        return False

def load_model(model_name: str) -> Optional[Any]:
    """
    任意のモデルをファイルから読み込み

    Args:
        model_name: モデル名（ファイル名）

    Returns:
        読み込んだモデルまたはNone（失敗時）
    """
    model_path = os.path.join(MODELS_DIR, f"{model_name}.pkl")

    if not os.path.exists(model_path):
        logger.warning(f"モデルファイルが見つかりません: {model_path}")
        return None

    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"モデル {model_name} を読み込みました: {model_path}")
        return model
    except Exception as e:
        logger.error(f"モデル {model_name} の読み込みに失敗: {e}", exc_info=True)
        return None
