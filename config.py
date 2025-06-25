"""
アプリケーション全体の設定を管理するモジュール
APIキー、データベースパスなど、アプリケーションで共通で利用する設定を管理します。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# プロジェクトのルートパス
ROOT_DIR = Path(__file__).parent.absolute()

# データベースファイルのパス
DB_PATH = os.path.join(ROOT_DIR, "data", "recruiting_mvp.db")
DB_URL = f"sqlite:///{DB_PATH}"

# GitHub API設定
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
GITHUB_API_BASE_URL = "https://api.github.com"

# Qiita API設定
QIITA_API_KEY = os.getenv("QIITA_API_KEY")
QIITA_API_BASE_URL = "https://qiita.com/api/v2"

# OpenAlex API設定
OPENALEX_API_BASE_URL = "https://api.openalex.org"
OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL")  # APIのポリシーに従ってユーザー識別用

# KAKEN API設定
KAKEN_API_BASE_URL = "https://nrid.nii.ac.jp/opensearch/"

# アプリケーション設定
APP_TITLE = "エンジニア・研究者ダイレクトリクルーティングMVP"
APP_DESCRIPTION = "Web上の公開情報からエンジニアおよび研究者の候補者を見つけ出し、ダイレクトリクルーティングを行うためのMVP"

# ロギング設定
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
LOG_DIR = os.path.join(ROOT_DIR, "logs")
LOG_TO_FILE = True  # ファイルへのログ出力を有効化
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5  # 保持するバックアップファイル数
LOG_ERRORS_SEPARATELY = True  # エラーログを別ファイルに出力
