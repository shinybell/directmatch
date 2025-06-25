# エンジニア・研究者ダイレクトリクルーティング MVP

## プロジェクト概要

Web 上の公開情報（GitHub、Qiita、国際学会論文、KAKEN、OpenAlex など）を効率的に収集・分析し、人材要件に合致するエンジニア・研究者を特定するための MVP（Minimum Viable Product）です。

本プロジェクトは、ダイレクトリクルーティングのプロセスを最小限の機能で実現し、その有効性を検証するために開発されました。

## 主な機能

- **情報収集**: GitHub、Qiita、OpenAlex、KAKEN などの公開 API/サイトからの情報収集
- **データ整理**: 収集した情報のデータベースへの保存と同一人物の特定・情報統合
- **マッチング**: 人材要件に基づく NLP による適合度計算
- **候補者リスト**: 適合度スコアに基づく候補者リストの表示と簡易検索
- **連絡先管理**: 候補者の公開連絡先の閲覧・コピー

## セットアップ方法

### 前提条件

- Python 3.9 以上
- pip (Python パッケージマネージャ)

### インストール

1. **リポジトリのクローン**:

   ```bash
   git clone https://github.com/yourusername/directmatch.git
   cd directmatch
   ```

2. **仮想環境の作成と有効化**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate
   ```

3. **依存パッケージのインストール**:

   ```bash
   pip install -r requirements.txt
   ```

4. **日本語 NLP 用の MeCab と IPADIC の設定**:

   ```bash
   # Macの場合
   brew install mecab mecab-ipadic

   # Ubuntuの場合
   sudo apt-get install mecab libmecab-dev mecab-ipadic-utf8
   ```

   ※ MeCab の代わりに Python パッケージ fugashi + ipadic を使用しています

5. **環境変数の設定**:
   `.env`ファイルを編集し、API キーなどの設定を行います：
   ```
   GITHUB_API_KEY=your_github_api_key
   QIITA_API_KEY=your_qiita_api_key
   OPENALEX_EMAIL=your_email@example.com
   ```

### 実行方法

アプリケーションを実行するには：

```bash
streamlit run app.py
```

ブラウザで自動的に`http://localhost:8501`が開き、アプリケーションにアクセスできます。

### ログ機能

本アプリケーションには包括的なログ機能が実装されています：

- **ログ出力先**: コンソール出力とファイル出力（`logs/`ディレクトリ）
- **ログレベル**: DEBUG、INFO、WARNING、ERROR、CRITICAL
- **ログ形式**: タイムスタンプ、ロガー名、ログレベル、ファイル名、行番号、メッセージ
- **ログファイル**: 日付別とロガー名でファイルを分割
- **エラーログ**: ERROR レベル以上のログは別ファイルにも記録
- **ログローテーション**: 最大サイズに達したらローテーションし、古いログを自動的にアーカイブ

ログレベルは`.env`ファイルで設定できます：

```
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICALのいずれか
```

ログファイルは以下のディレクトリに保存されます：

```
logs/YYYY-MM-DD_[ロガー名].log      # 一般ログ
logs/YYYY-MM-DD_[ロガー名]_error.log # エラーログ
```

#### ログ機能テスト

ログ機能を手動でテストするには、付属のテストスクリプトを実行します：

```bash
python test_logging.py
```

これにより、各ログレベルのサンプルメッセージが出力され、ログファイルが正しく生成されるか確認できます。

## プロジェクト構成

```
project_root/
├── app.py                      # Streamlitアプリケーションのエントリーポイント
├── config.py                   # アプリケーション共通の設定（APIキー、DBパスなど）
├── requirements.txt            # Pythonの依存関係リスト
├── .env                        # 環境変数（APIキーなどの機密情報）
├── data/                       # データ保存用ディレクトリ
│   └── recruiting_mvp.db       # SQLiteデータベースファイル
├── logs/                       # アプリケーションログ保存用ディレクトリ
│   ├── YYYY-MM-DD_app.log     # 日付別の一般ログファイル
│   └── YYYY-MM-DD_app_error.log # 日付別のエラーログファイル
└── src/                        # アプリケーションのコアロジックを格納
    ├── data_collection/        # 外部APIとの連携、データ取得ロジック
    │   ├── github_client.py    # GitHub APIクライアント
    │   ├── qiita_client.py     # Qiita APIクライアント
    │   ├── openalex_client.py  # OpenAlex APIクライアント
    │   ├── kaken_client.py     # KAKEN APIクライアント
    │   └── collector.py        # 各クライアントを呼び出し、データ収集を統括するモジュール
    ├── database/               # データベース操作関連ロジック
    │   ├── models.py           # SQLAlchemy ORMモデル定義
    │   ├── db_manager.py       # データベース接続、セッション管理
    │   └── crud.py             # CRUD操作（データの作成、読み込み、更新、削除）
    ├── nlp_processing/         # 自然言語処理関連ロジック
    │   ├── preprocessor.py     # テキスト前処理（トークン化、正規化、日本語処理）
    │   ├── matcher.py          # TF-IDFベクトル化とコサイン類似度計算
    │   └── models.py           # NLPモデルのロード/保存
    ├── core/                   # アプリケーションの主要ビジネスロジック
    │   └── recruitment_service.py # データ収集、NLP処理、データベース操作を連携させ、採用活動の主要ロジックを実装
    └── utils/                  # 汎用的なユーティリティ関数
        └── common.py           # ログ設定、ID生成、エラーハンドリングなど、共通で利用する関数
```

## 使用技術

- **バックエンド**: Python 3.9+
- **Web フレームワーク**: Streamlit
- **データベース**: SQLite（MVP 向け）
- **ORM**: SQLAlchemy
- **データ処理**: pandas, numpy
- **NLP**: scikit-learn (TF-IDF, Cosine Similarity), nltk / MeCab (日本語前処理)
- **ログ管理**: Python 標準ライブラリの logging モジュール

## 注意事項

- このプロジェクトは個人情報を扱いますので、個人情報保護法に従った運用が必要です。
- 各 API/サイトの利用規約を遵守してください。特に商用利用や大規模なデータ収集に関する制限を確認してください。
- 無許可の Web スクレイピングは行わないでください。公式に提供されている API を利用しています。

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は LICENSE ファイルを参照してください。
