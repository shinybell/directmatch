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

    # タブ切り替え時のコールバック
    def tab_change_callback(tab_index):
        st.session_state.active_tab = tab_index

    st.title(config.APP_TITLE)
    st.markdown("Web上の公開情報からエンジニアおよび研究者の候補者を見つけ出すためのツールです")

    # サービスオブジェクトを初期化
    service = RecruitmentService()

    # サイドバーで検索オプション設定
    with st.sidebar:
        st.header("ダッシュボード")

        # データ概要セクション
        st.subheader("データ概要")

        # データベースからの統計情報取得
        persons = service.get_all_persons()
        total_count = len(persons)

        # 研究者とエンジニアのカウント
        researcher_count = sum(1 for p in persons if p.is_researcher)
        engineer_count = sum(1 for p in persons if p.is_engineer)

        # データソースごとの人数を集計（data_sourcesカラム使用）
        github_count = sum(1 for p in persons if p.data_sources and "github" in p.data_sources)
        qiita_count = sum(1 for p in persons if p.data_sources and "qiita" in p.data_sources)
        openalex_count = sum(1 for p in persons if p.data_sources and "openalex" in p.data_sources)
        kaken_count = sum(1 for p in persons if p.data_sources and "kaken" in p.data_sources)

        # 最新の更新日時
        if persons:
            latest_update = max((p.last_updated_at for p in persons if p.last_updated_at), default=None)
            latest_update_str = latest_update.strftime("%Y-%m-%d %H:%M") if latest_update else "なし"
        else:
            latest_update_str = "なし"

        # メトリクスを表示
        col1, col2 = st.columns(2)
        with col1:
            st.metric("総候補者数", total_count)
            st.metric("研究者", researcher_count)
        with col2:
            st.metric("エンジニア", engineer_count)

        st.caption(f"最終更新: {latest_update_str}")

        # データソース内訳
        st.caption("データソース内訳:")
        st.write(f"GitHub: {github_count}人, Qiita: {qiita_count}人, OpenAlex: {openalex_count}人, KAKEN: {kaken_count}人")

        st.divider()

        # クイック検索セクション
        st.subheader("クイック検索")

        # よく使われるキーワードを設定（実際には利用頻度から動的に生成するとよい）
        common_keywords = [
            "Python", "機械学習", "データサイエンス", "深層学習",
            "自然言語処理", "コンピュータビジョン", "TensorFlow", "PyTorch"
        ]

        # クイック検索ボタン
        st.caption("キーワードでクイック検索:")

        # 2列でボタンを配置
        for i in range(0, len(common_keywords), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(common_keywords):
                    keyword = common_keywords[i + j]
                    if cols[j].button(keyword, key=f"quick_search_{keyword}"):
                        # ボタンがクリックされたらキーワードを検索ボックスにセット
                        st.session_state.search_keyword = keyword
                        st.session_state.active_tab = 0  # 候補者一覧タブに切り替え

        # カスタム検索
        st.caption("カスタム検索:")
        custom_search = st.text_input("キーワードを入力", key="sidebar_search_input")
        if st.button("検索", key="sidebar_search_button"):
            if custom_search:
                st.session_state.search_keyword = custom_search
                st.session_state.active_tab = 0  # 候補者一覧タブに切り替え
                st.rerun()  # UIを更新

        st.divider()

        # お気に入り候補者（将来の機能のためのプレースホルダー）
        st.subheader("最近閲覧した候補者")

        # セッション状態に最近閲覧した候補者リストを初期化
        if "recent_viewed_persons" not in st.session_state:
            st.session_state.recent_viewed_persons = []

        # 最近閲覧した候補者がいれば表示
        if st.session_state.recent_viewed_persons:
            for person_id in st.session_state.recent_viewed_persons[:5]:  # 最新5件まで表示
                person = service.get_person_by_id(person_id)
                if person:
                    if st.button(f"{person.full_name}", key=f"recent_{person.id}"):
                        # 候補者一覧タブに移動して該当候補者を選択
                        st.session_state.selected_person_id = person.id
                        st.session_state.active_tab = 0
                        st.rerun()
        else:
            st.caption("まだ候補者が閲覧されていません")

    # メインコンテンツ
    # タブ選択用のセッション状態を初期化
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0  # デフォルトは候補者一覧タブ

    # データ収集完了時の処理
    # タブの自動切り替えは行わず、フラグのみリセットする
    # if st.session_state.get("collection_completed", False):
        # 自動タブ切り替えは行わない
        # st.session_state.collection_completed = False  # フラグをリセットしない（表示を維持するため）

    # タブの定義
    tab_names = ["候補者一覧", "人材要件入力", "データ収集", "アプローチ戦略"]

    # タブを作成し、アクティブなタブを選択
    tabs = st.tabs(tab_names)

    # セッション状態からアクティブなタブのインデックスを取得
    current_tab_index = st.session_state.active_tab

    # タブ選択用のセッション状態を初期化
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0

    # タブを選択
    if "active_tab" in st.session_state:
        st.session_state.active_tab_obj = tabs[st.session_state.active_tab]

    # 候補者一覧タブ
    with tabs[0]:
        st.header("候補者一覧")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("検索オプション")
            st.text_input("キーワードで候補者を検索", key="search_keyword")
            st.checkbox("研究者", value=True, key="include_researchers")
            st.checkbox("エンジニア", value=True, key="include_engineers")
        with col2:
            st.subheader("表示オプション")
            st.checkbox("詳細情報を表示", value=False, key="show_details")

            # 詳細表示が有効な場合、表示するフィールドを選択
            if "show_details" in st.session_state and st.session_state.show_details:
                st.multiselect(
                    "表示するフィールド",
                    options=["メール", "LinkedIn", "個人ブログ", "最終更新日"],
                    default=["メール"],
                    key="display_fields"
                )
            else:
                # デフォルト値を設定
                st.session_state.display_fields = []

        st.divider()  # 区切り線を追加
        # データ更新フラグがある場合はリフレッシュ
        refresh_data = st.session_state.get("refresh_data", False)

        # ダミーデータでテーブルを作成（実際にはDBから取得）
        if "match_score" not in st.session_state:
            st.session_state.match_score = {}

        persons = service.get_all_persons()

        if refresh_data:
            st.session_state.refresh_data = False  # フラグをリセット

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
                        "データソース": ", ".join(p.data_sources) if p.data_sources else "",
                        "GitHub": p.github_username or "",
                        "Qiita": "https://qiita.com/" + p.qiita_id  if p.qiita_id else "",
                        "ORCID": p.orcid_id or "",
                        "経験サマリー": p.experience_summary or ""
                    }

                    # 詳細表示が有効な場合の追加フィールド
                    if "show_details" in st.session_state and st.session_state.show_details:
                        if "メール" in st.session_state.display_fields:
                            row["メール"] = p.email or ""

                        if "LinkedIn" in st.session_state.display_fields:
                            row["LinkedIn"] = p.linkedin_url or ""

                        if "個人ブログ" in st.session_state.display_fields:
                            row["個人ブログ"] = p.personal_blog_url or ""

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
                    "所属": st.column_config.Column(width="small"),
                    "適合度": st.column_config.NumberColumn(format="%.2f", width="small"),
                    "研究者": st.column_config.Column(width="small"),
                    "エンジニア": st.column_config.Column(width="small"),
                    "データソース": st.column_config.Column(width="medium"),
                    "GitHub": st.column_config.LinkColumn(width="small"),
                    "Qiita": st.column_config.LinkColumn(width="small"),
                    "ORCID": st.column_config.LinkColumn(width="small"),
                    "経験サマリー": st.column_config.Column(width="large")
                }

                # 詳細表示が有効な場合の追加カラム設定
                if "show_details" in st.session_state and st.session_state.show_details:
                    if "メール" in st.session_state.display_fields:
                        column_config["メール"] = st.column_config.Column(width="medium")

                    if "LinkedIn" in st.session_state.display_fields:
                        column_config["LinkedIn"] = st.column_config.LinkColumn(width="small")

                    if "個人ブログ" in st.session_state.display_fields:
                        column_config["個人ブログ"] = st.column_config.LinkColumn(width="small")

                    if "最終更新日" in st.session_state.display_fields:
                        column_config["最終更新日"] = st.column_config.DateColumn(width="medium", format="YYYY-MM-DD HH:mm")

                # セッション状態に選択された候補者IDを保存するキーを追加
                if "selected_person_id" not in st.session_state:
                    st.session_state.selected_person_id = None

                def handle_click():
                    st.session_state.selected_person_row = st.session_state.person_selection.selection.rows[0]
                    print(f"選択された候補者ID: {st.session_state.selected_person_row}")


                # テーブル表示
                st.dataframe(
                    df,
                    hide_index=True,
                    column_config=column_config,
                    use_container_width=True,
                    key="person_selection",
                    on_select=handle_click,  # 行クリック時のコールバックを設定
                    selection_mode="single-row"
                )

                # 候補者詳細表示
                st.subheader("候補者詳細")
                # selected_id = st.selectbox("詳細を表示する候補者を選択", options=df["ID"].tolist(), format_func=lambda x: df[df["ID"]==x]["氏名"].iloc[0])
                # セレクトボックスを使わず、クリックされた行のIDを使用
                # selected_person_rowは行番号なので、これを使ってIDを取得
                selected_id = df.iloc[st.session_state.person_selection.selection.rows[0]]["ID"] if st.session_state.person_selection.selection.rows else None

                if selected_id:
                    person = service.get_person_by_id(selected_id)
                    if person:
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(f"**氏名:** {person.full_name}")
                            st.markdown(f"**所属:** {person.current_affiliation or '不明'}")

                            # データソース情報を表示
                            sources_str = "、".join(person.data_sources) if person.data_sources else "不明"
                            st.markdown(f"**データソース:** {sources_str}")

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

                    # 候補者一覧タブに自動切り替え
                    st.session_state.active_tab = 0  # 候補者一覧タブに切り替え
                    st.rerun()  # アプリを再実行して表示を更新
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
                    # データ収集が既に実行中でないことを確認
                    if not st.session_state.get("collecting", False):
                        st.session_state.collecting = True
                        st.session_state.progress = 0
                        st.session_state.collected_count = 0
                        # 完了フラグをリセット
                        st.session_state.collection_completed = False
                        st.rerun()  # リロードして収集処理を開始
                    else:
                        st.warning("データ収集はすでに実行中です。完了までお待ちください。")
                else:
                    st.error("少なくとも1つのデータソースを有効にし、検索キーワードを指定してください")
        # データベースリセット機能
        st.divider()  # 区切り線を追加
        st.subheader("データベース管理")
        with st.expander("データベースリセット", expanded=False):
            st.warning("この操作は取り消せません。データベース内のすべての候補者情報が削除されます。")
            reset_confirmed = st.checkbox("データベースリセットを実行することを確認します")

            if st.button("データベースをリセット", disabled=not reset_confirmed):
                if reset_confirmed:
                    with st.spinner("データベースをリセット中..."):
                        deleted_count = service.reset_database()
                        st.success(f"データベースをリセットしました。{deleted_count}件の候補者データを削除しました。")
                        # セッション状態のマッチングスコアもリセット
                        if "match_score" in st.session_state:
                            st.session_state.match_score = {}
                else:
                    st.error("確認チェックボックスにチェックを入れてください")

        with col2:
            st.subheader("収集状況")

            if "collecting" in st.session_state and st.session_state.collecting:
                progress_bar = st.progress(st.session_state.progress)
                status_text = st.empty()

                # 無限ループを防ぐためにフラグを最初にリセット
                collecting_flag = st.session_state.collecting
                st.session_state.collecting = False

                # データ収集フラグを明示的にチェック
                if collecting_flag and not st.session_state.get("collection_completed", False):
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

                        # データ収集完了フラグを設定
                        st.session_state.collection_completed = True
                        # 自動タブ切り替えと再実行は行わない（メッセージが表示されたままになる）

                    except Exception as e:
                        st.error(f"データ収集中にエラーが発生しました: {e}")
                        import traceback
                        st.write(traceback.format_exc())
            else:
                st.info("「データ収集開始」ボタンをクリックするとデータ収集が始まります")

            if "collected_count" in st.session_state and st.session_state.collected_count > 0:
                st.metric("収集済み候補者数", st.session_state.collected_count)

    with tabs[3]:
        # 候補者詳細表示
        st.subheader("候補者詳細")
        # selected_id = st.selectbox("詳細を表示する候補者を選択", options=df["ID"].tolist(), format_func=lambda x: df[df["ID"]==x]["氏名"].iloc[0])
        # セレクトボックスを使わず、クリックされた行のIDを使用
        # selected_person_rowは行番号なので、これを使ってIDを取得
        if persons:
            selected_id = df.iloc[st.session_state.person_selection.selection.rows[0]]["ID"] if st.session_state.person_selection.selection.rows else None
        else:
            selected_id = None

        if selected_id:
            person = service.get_person_by_id(selected_id)
            if person:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**氏名:** {person.full_name}")
                    st.markdown(f"**所属:** {person.current_affiliation or '不明'}")

                    # データソース情報を表示
                    sources_str = "、".join(person.data_sources) if person.data_sources else "不明"
                    st.markdown(f"**データソース:** {sources_str}")

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

        st.subheader("アプローチ戦略")

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
