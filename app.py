"""
エンジニア・研究者ダイレクトリクルーティングMVPのメインアプリケーション
Streamlitを使用したWebインターフェースを提供します
"""
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from src.core.recruitment_service import RecruitmentService
from src.nlp_processing.matcher import match_requirements
from src.utils.common import setup_logger
import config

# メインロガーを設定
logger = setup_logger('app')

def main():
    # アプリケーション起動時にログを記録
    logger.info(f"アプリケーション {config.APP_TITLE} を起動しました")
    logger.debug(f"設定情報: LOG_DIR={config.LOG_DIR}, LOG_LEVEL={config.LOG_LEVEL}")

    # 環境とシステム情報をログに記録
    import platform
    import sys
    logger.info(f"実行環境: Python {sys.version}, OS: {platform.platform()}")

    st.set_page_config(
        page_title=config.APP_TITLE,
        page_icon="🔍",
        layout="wide"
    )

    st.title(config.APP_TITLE)
    st.markdown("Web上の公開情報からエンジニアおよび研究者の候補者を見つけ出すためのツールです")

    # サービスオブジェクトを初期化
    service = RecruitmentService()

    # サイドバーで検索オプション設定
    with st.sidebar:
        st.header("検索オプション")
        st.text_input("キーワードで候補者を検索", key="search_keyword")
        st.checkbox("研究者", value=True, key="include_researchers")
        st.checkbox("エンジニア", value=True, key="include_engineers")

        st.header("表示オプション")
        st.checkbox("詳細情報を表示", value=False, key="show_details")

        # 詳細表示が有効な場合、表示するフィールドを選択
        if "show_details" in st.session_state and st.session_state.show_details:
            st.multiselect(
                "表示するフィールド",
                options=["メール", "LinkedIn", "個人ブログ", "経験サマリー", "最終更新日"],
                default=["メール", "経験サマリー"],
                key="display_fields"
            )
        else:
            # デフォルト値を設定
            st.session_state.display_fields = []

    # メインコンテンツ
    tabs = st.tabs(["候補者一覧", "人材要件入力", "データ収集"])

    # 候補者一覧タブ
    with tabs[0]:
        st.header("候補者一覧")

        # ダミーデータでテーブルを作成（実際にはDBから取得）
        if "match_score" not in st.session_state:
            st.session_state.match_score = {}

        persons = service.get_all_persons()

        if persons:
            # 検索キーワードでフィルタリング
            if st.session_state.search_keyword:
                persons = service.search_persons_by_keyword(
                    persons, st.session_state.search_keyword
                )

            # チェックボックスでフィルタリング
            filtered_persons = []
            for p in persons:
                if (p.is_researcher and st.session_state.include_researchers) or \
                   (p.is_engineer and st.session_state.include_engineers):
                    filtered_persons.append(p)

            if filtered_persons:
                # Pandas DataFrameに変換
                rows = []
                for p in filtered_persons:
                    # 常に表示する基本フィールド
                    row = {
                        "ID": p.id,
                        "氏名": p.full_name,
                        "所属": p.current_affiliation or "",
                        "適合度": st.session_state.match_score.get(p.id, 0.0),
                        "研究者": "✓" if p.is_researcher else "",
                        "エンジニア": "✓" if p.is_engineer else "",
                        "GitHub": p.github_username or "",
                        "Qiita": "https://qiita.com/" + p.qiita_id  if p.qiita_id else "",
                        "ORCID": p.orcid_id or ""
                    }

                    # 詳細表示が有効な場合の追加フィールド
                    if "show_details" in st.session_state and st.session_state.show_details:
                        if "メール" in st.session_state.display_fields:
                            row["メール"] = p.email or ""

                        if "LinkedIn" in st.session_state.display_fields:
                            row["LinkedIn"] = p.linkedin_url or ""

                        if "個人ブログ" in st.session_state.display_fields:
                            row["個人ブログ"] = p.personal_blog_url or ""

                        if "経験サマリー" in st.session_state.display_fields:
                            row["経験サマリー"] = p.experience_summary or ""

                        if "最終更新日" in st.session_state.display_fields:
                            row["最終更新日"] = p.last_updated_at.strftime("%Y-%m-%d %H:%M") if p.last_updated_at else ""

                    rows.append(row)

                # DataFrameの作成
                df = pd.DataFrame(rows)

                # 適合度でソート
                df = df.sort_values("適合度", ascending=False)

                # 基本カラム設定
                column_config = {
                    "ID": st.column_config.Column(width="small"),
                    "氏名": st.column_config.Column(width="medium"),
                    "所属": st.column_config.Column(width="medium"),
                    "適合度": st.column_config.NumberColumn(format="%.2f", width="small"),
                    "研究者": st.column_config.Column(width="small"),
                    "エンジニア": st.column_config.Column(width="small"),
                    "GitHub": st.column_config.LinkColumn(width="small"),
                    "Qiita": st.column_config.LinkColumn(width="small"),
                    "ORCID": st.column_config.LinkColumn(width="small")
                }

                # 詳細表示が有効な場合の追加カラム設定
                if "show_details" in st.session_state and st.session_state.show_details:
                    if "メール" in st.session_state.display_fields:
                        column_config["メール"] = st.column_config.Column(width="medium")

                    if "LinkedIn" in st.session_state.display_fields:
                        column_config["LinkedIn"] = st.column_config.LinkColumn(width="small")

                    if "個人ブログ" in st.session_state.display_fields:
                        column_config["個人ブログ"] = st.column_config.LinkColumn(width="small")

                    if "経験サマリー" in st.session_state.display_fields:
                        column_config["経験サマリー"] = st.column_config.TextColumn(width="large")

                    if "最終更新日" in st.session_state.display_fields:
                        column_config["最終更新日"] = st.column_config.DateColumn(width="medium", format="YYYY-MM-DD HH:mm")

                # テーブル表示
                st.dataframe(
                    df,
                    hide_index=True,
                    column_config=column_config,
                    use_container_width=True
                )

                # 候補者詳細表示
                st.subheader("候補者詳細")
                selected_id = st.selectbox("詳細を表示する候補者を選択", options=df["ID"].tolist(), format_func=lambda x: df[df["ID"]==x]["氏名"].iloc[0])

                if selected_id:
                    person = service.get_person_by_id(selected_id)
                    if person:
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(f"**氏名:** {person.full_name}")
                            st.markdown(f"**所属:** {person.current_affiliation or '不明'}")

                            if person.email:
                                st.markdown(f"**メール:** {person.email}")
                                st.button(f"{person.email} をコピー", key=f"copy_email_{person.id}")

                            st.markdown("**リンク:**")
                            if person.github_username:
                                st.markdown(f"- [GitHub](https://github.com/{person.github_username})")
                            if person.qiita_id:
                                st.markdown(f"- [Qiita](https://qiita.com/{person.qiita_id})")
                            if person.orcid_id:
                                st.markdown(f"- [ORCID](https://orcid.org/{person.orcid_id})")
                            if person.linkedin_url:
                                st.markdown(f"- [LinkedIn]({person.linkedin_url})")
                            if person.personal_blog_url:
                                st.markdown(f"- [個人ブログ]({person.personal_blog_url})")

                        with col2:
                            st.markdown("**経験サマリ:**")
                            st.markdown(person.experience_summary or "情報がありません")
            else:
                st.info("条件に一致する候補者が見つかりませんでした")
        else:
            st.info("候補者データがありません。「データ収集」タブからデータを収集してください")

    # 人材要件入力タブ
    with tabs[1]:
        st.header("人材要件入力")

        requirements = st.text_area(
            "求める人材の要件を入力してください",
            placeholder="例: 機械学習を使った5年以上の実務経験、自己教師あり学習の実装経験、Python、TensorFlow、PyTorchの習熟度、ICLRでの発表経験など",
            height=200
        )

        if st.button("要件に基づいて候補者をマッチング"):
            if requirements:
                with st.spinner("マッチング処理中..."):
                    # 全候補者を取得
                    all_persons = service.get_all_persons()

                    # マッチングスコア計算
                    match_results = match_requirements(requirements, all_persons)

                    # セッション状態に保存
                    st.session_state.match_score = {
                        person_id: score for person_id, score in match_results
                    }

                    st.success(f"{len(match_results)}人の候補者のマッチングスコアを計算しました")
                    st.info("「候補者一覧」タブで適合度順にソートされた結果を確認できます")
            else:
                st.error("人材要件を入力してください")

    # データ収集タブ
    with tabs[2]:
        st.header("データ収集")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("データソース設定")

            # ソースごとに設定できる高度なモードを追加
            advanced_mode = st.checkbox("ソースごとに詳細設定", value=False)

            # 初期設定
            if "source_configs" not in st.session_state:
                st.session_state.source_configs = {
                    "github": {"enabled": True, "keywords": [], "max_results": 30},
                    "qiita": {"enabled": True, "keywords": [], "max_results": 30},
                    "openalex": {"enabled": True, "keywords": [], "max_results": 30},
                    "kaken": {"enabled": True, "keywords": [], "max_results": 30}
                }

            if advanced_mode:
                # ソースごとに異なる設定を可能にする
                st.write("各データソースの設定")

                # GitHub設定
                with st.expander("GitHub", expanded=True):
                    st.session_state.source_configs["github"]["enabled"] = st.checkbox(
                        "GitHub を有効化",
                        value=st.session_state.source_configs["github"]["enabled"]
                    )
                    github_keywords = st.text_input(
                        "GitHub検索キーワード（カンマ区切りで複数指定可）",
                        ", ".join(st.session_state.source_configs["github"].get("keywords", [])),
                        key="github_keywords"
                    )
                    st.session_state.source_configs["github"]["keywords"] = [k.strip() for k in github_keywords.split(",") if k.strip()]
                    st.session_state.source_configs["github"]["max_results"] = st.slider(
                        "GitHubの最大取得件数",
                        min_value=5, max_value=100,
                        value=st.session_state.source_configs["github"].get("max_results", 30),
                        step=5,
                        key="github_max_results"
                    )

                # Qiita設定
                with st.expander("Qiita", expanded=True):
                    st.session_state.source_configs["qiita"]["enabled"] = st.checkbox(
                        "Qiita を有効化",
                        value=st.session_state.source_configs["qiita"]["enabled"]
                    )
                    qiita_keywords = st.text_input(
                        "Qiita検索キーワード（カンマ区切りで複数指定可）",
                        ", ".join(st.session_state.source_configs["qiita"].get("keywords", [])),
                        key="qiita_keywords"
                    )
                    st.session_state.source_configs["qiita"]["keywords"] = [k.strip() for k in qiita_keywords.split(",") if k.strip()]
                    st.session_state.source_configs["qiita"]["max_results"] = st.slider(
                        "Qiitaの最大取得件数",
                        min_value=5, max_value=100,
                        value=st.session_state.source_configs["qiita"].get("max_results", 30),
                        step=5,
                        key="qiita_max_results"
                    )

                # OpenAlex設定
                with st.expander("OpenAlex", expanded=True):
                    st.session_state.source_configs["openalex"]["enabled"] = st.checkbox(
                        "OpenAlex を有効化",
                        value=st.session_state.source_configs["openalex"]["enabled"]
                    )
                    openalex_keywords = st.text_input(
                        "OpenAlex検索キーワード（カンマ区切りで複数指定可）",
                        ", ".join(st.session_state.source_configs["openalex"].get("keywords", [])),
                        key="openalex_keywords"
                    )
                    st.session_state.source_configs["openalex"]["keywords"] = [k.strip() for k in openalex_keywords.split(",") if k.strip()]
                    st.session_state.source_configs["openalex"]["max_results"] = st.slider(
                        "OpenAlexの最大取得件数",
                        min_value=5, max_value=100,
                        value=st.session_state.source_configs["openalex"].get("max_results", 30),
                        step=5,
                        key="openalex_max_results"
                    )

                # KAKEN設定
                with st.expander("KAKEN", expanded=True):
                    st.session_state.source_configs["kaken"]["enabled"] = st.checkbox(
                        "KAKEN を有効化",
                        value=st.session_state.source_configs["kaken"]["enabled"]
                    )
                    kaken_keywords = st.text_input(
                        "KAKEN検索キーワード（カンマ区切りで複数指定可）",
                        ", ".join(st.session_state.source_configs["kaken"].get("keywords", [])),
                        key="kaken_keywords"
                    )
                    st.session_state.source_configs["kaken"]["keywords"] = [k.strip() for k in kaken_keywords.split(",") if k.strip()]
                    st.session_state.source_configs["kaken"]["max_results"] = st.slider(
                        "KAKENの最大取得件数",
                        min_value=5, max_value=100,
                        value=st.session_state.source_configs["kaken"].get("max_results", 30),
                        step=5,
                        key="kaken_max_results"
                    )
            else:
                # 従来のシンプルなUI
                sources = {
                    "github": st.checkbox("GitHub", value=st.session_state.source_configs["github"]["enabled"]),
                    "qiita": st.checkbox("Qiita", value=st.session_state.source_configs["qiita"]["enabled"]),
                    "openalex": st.checkbox("OpenAlex", value=st.session_state.source_configs["openalex"]["enabled"]),
                    "kaken": st.checkbox("KAKEN", value=st.session_state.source_configs["kaken"]["enabled"])
                }

                # ソースの有効/無効状態をセッション状態に保存
                for src, enabled in sources.items():
                    st.session_state.source_configs[src]["enabled"] = enabled

                keywords = st.text_input("検索キーワード（カンマ区切りで複数指定可）", placeholder="python, 機械学習, データサイエンス")
                max_results = st.slider("最大取得件数", min_value=10, max_value=100, value=30, step=10)

                # すべてのソースに同じキーワードと最大件数を設定
                if keywords:
                    keywords_list = [k.strip() for k in keywords.split(",") if k.strip()]
                    for src in st.session_state.source_configs:
                        if st.session_state.source_configs[src]["enabled"]:
                            st.session_state.source_configs[src]["keywords"] = keywords_list
                            st.session_state.source_configs[src]["max_results"] = max_results

            # 実行ボタン
            if st.button("データ収集開始"):
                # 有効なソースとキーワードをチェック
                valid_configs = any(
                    cfg["enabled"] and len(cfg["keywords"]) > 0
                    for cfg in st.session_state.source_configs.values()
                )

                if valid_configs:
                    st.session_state.collecting = True
                    st.session_state.progress = 0
                    st.session_state.collected_count = 0
                else:
                    st.error("少なくとも1つのデータソースを有効にし、検索キーワードを指定してください")

        with col2:
            st.subheader("収集状況")

            if "collecting" in st.session_state and st.session_state.collecting:
                progress_bar = st.progress(st.session_state.progress)
                status_text = st.empty()

                try:
                    # ソース設定を準備
                    source_configs = {}

                    for src, cfg in st.session_state.source_configs.items():
                        if cfg["enabled"] and cfg["keywords"]:
                            source_configs[src] = {
                                "keywords": cfg["keywords"],
                                "max_results": cfg["max_results"]
                            }

                    # ソース設定の概要を表示
                    if source_configs:
                        status_text.info("以下の設定でデータ収集を開始します:")
                        for src, cfg in source_configs.items():
                            st.write(f"- {src}: {len(cfg['keywords'])}個のキーワード, 最大{cfg['max_results']}件")

                    # データ収集実行
                    total_collected = service.collect_data(source_configs=source_configs)

                    st.session_state.collected_count = total_collected
                    st.session_state.progress = 1.0
                    progress_bar.progress(1.0)
                    status_text.success(f"データ収集完了: {total_collected}件の候補者情報を収集しました")
                except Exception as e:
                    st.error(f"データ収集中にエラーが発生しました: {e}")
                    import traceback
                    st.write(traceback.format_exc())

                st.session_state.collecting = False
            else:
                st.info("「データ収集開始」ボタンをクリックするとデータ収集が始まります")

            if "collected_count" in st.session_state and st.session_state.collected_count > 0:
                st.metric("収集済み候補者数", st.session_state.collected_count)

def log_system_info():
    """システム情報をログに記録する"""
    import platform
    import sys
    import psutil

    try:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        logger.info(f"システム情報:")
        logger.info(f"  - OS: {platform.platform()}")
        logger.info(f"  - Python: {sys.version}")
        logger.info(f"  - メモリ使用量: {mem.percent}% ({mem.used / (1024**3):.2f}GB/{mem.total / (1024**3):.2f}GB)")
        logger.info(f"  - ディスク使用量: {disk.percent}% ({disk.used / (1024**3):.2f}GB/{disk.total / (1024**3):.2f}GB)")
    except Exception as e:
        logger.warning(f"システム情報の取得に失敗しました: {e}")

if __name__ == "__main__":
    start_time = datetime.now()
    try:
        # ログディレクトリの確認
        if not os.path.exists(config.LOG_DIR):
            os.makedirs(config.LOG_DIR)
            logger.info(f"ログディレクトリを作成しました: {config.LOG_DIR}")

        # システム情報をログに記録
        try:
            log_system_info()
        except ImportError:
            logger.warning("psutilがインストールされていないため、詳細なシステム情報を記録できません。")
            logger.warning("pip install psutilを実行してインストールすることを推奨します。")

        logger.info("----------- アプリケーション起動 -----------")
        main()
    except Exception as e:
        logger.error(f"アプリケーションで予期せぬエラーが発生しました: {e}", exc_info=True)
        # エラー情報をユーザーに表示（Streamlitが起動している場合）
        import traceback
        error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
        try:
            st.error(error_msg)
        except:
            pass  # Streamlitコンテキスト外の場合
        raise
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"アプリケーション終了 - 実行時間: {duration:.2f}秒")
        logger.info("----------------------------------------")
