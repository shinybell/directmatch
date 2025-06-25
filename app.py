"""
エンジニア・研究者ダイレクトリクルーティングMVPのメインアプリケーション
Streamlitを使用したWebインターフェースを提供します
"""
import streamlit as st
import pandas as pd
from src.core.recruitment_service import RecruitmentService
from src.nlp_processing.matcher import match_requirements
import config

def main():
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
                df = pd.DataFrame([
                    {
                        "ID": p.id,
                        "氏名": p.full_name,
                        "所属": p.current_affiliation,
                        "適合度": st.session_state.match_score.get(p.id, 0.0),
                        "研究者": "✓" if p.is_researcher else "",
                        "エンジニア": "✓" if p.is_engineer else "",
                        "GitHub": p.github_username or "",
                        "Qiita": p.qiita_id or "",
                        "ORCID": p.orcid_id or ""
                    } for p in filtered_persons
                ])

                # 適合度でソート
                df = df.sort_values("適合度", ascending=False)

                # テーブル表示
                st.dataframe(
                    df,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.Column(width="None"),
                        "氏名": st.column_config.Column(width="medium"),
                        "所属": st.column_config.Column(width="large"),
                        "適合度": st.column_config.NumberColumn(format="%.2f", width="small"),
                        "研究者": st.column_config.Column(width="small"),
                        "エンジニア": st.column_config.Column(width="small"),
                        "GitHub": st.column_config.LinkColumn(width="medium"),
                        "Qiita": st.column_config.LinkColumn(width="medium"),
                        "ORCID": st.column_config.LinkColumn(width="medium")
                    },
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
            st.subheader("データソース選択")

            sources = {
                "github": st.checkbox("GitHub", value=True),
                "qiita": st.checkbox("Qiita", value=True),
                "openalex": st.checkbox("OpenAlex", value=True),
                "kaken": st.checkbox("KAKEN", value=True)
            }

            keywords = st.text_input("検索キーワード（カンマ区切りで複数指定可）", placeholder="python, 機械学習, データサイエンス")
            max_results = st.slider("最大取得件数", min_value=10, max_value=100, value=30, step=10)

            if st.button("データ収集開始"):
                if any(sources.values()) and keywords:
                    st.session_state.collecting = True
                    st.session_state.progress = 0
                    st.session_state.collected_count = 0
                else:
                    st.error("データソースと検索キーワードを指定してください")

        with col2:
            st.subheader("収集状況")

            if "collecting" in st.session_state and st.session_state.collecting:
                progress_bar = st.progress(st.session_state.progress)
                status_text = st.empty()

                # 実際のデータ収集処理（実装時には非同期処理などを検討）
                keywords_list = [k.strip() for k in keywords.split(",")]

                try:
                    total_collected = service.collect_data(
                        keywords=keywords_list,
                        sources={k: v for k, v in sources.items() if v},
                        max_results_per_source=max_results
                    )

                    st.session_state.collected_count = total_collected
                    st.session_state.progress = 1.0
                    progress_bar.progress(1.0)
                    status_text.success(f"データ収集完了: {total_collected}件の候補者情報を収集しました")
                except Exception as e:
                    st.error(f"データ収集中にエラーが発生しました: {e}")

                st.session_state.collecting = False
            else:
                st.info("「データ収集開始」ボタンをクリックするとデータ収集が始まります")

            if "collected_count" in st.session_state and st.session_state.collected_count > 0:
                st.metric("収集済み候補者数", st.session_state.collected_count)

if __name__ == "__main__":
    main()
