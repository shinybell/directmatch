"""
テキスト前処理モジュール
日本語・英語テキストの前処理を行う関数群を提供
"""
import re
import unicodedata
from typing import List, Set, Dict, Any

# 英語用
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
# from nltk.stem.porter import PorterStemmer

# 日本語用
try:
    import fugashi
    import ipadic
except ImportError:
    pass

# ロガーの設定
from src.utils.common import setup_logger
logger = setup_logger(__name__)

# 必要なNLTKデータのダウンロード
def download_nltk_resources():
    """
    必要なNLTKリソースをダウンロード
    """
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        logger.info("NLTKリソースのダウンロードが完了しました")
    except Exception as e:
        logger.error(f"NLTKリソースのダウンロード中にエラーが発生: {e}")

# 日本語のストップワード
JAPANESE_STOPWORDS = {
    'あそこ', 'あたり', 'あちら', 'あっち', 'あと', 'あな', 'あなた', 'あれ', 'いくつ', 'いつ', 'いま', 'いや',
    'おい', 'おかげ', 'おまえ', 'おれ', 'がい', 'かく', 'かたち', 'かやの', 'から', 'がら', 'きた', 'くせ',
    'ここ', 'こちら', 'こっち', 'こと', 'ごと', 'こな', 'これ', 'ごろ', 'さて', 'さん', 'しかた', 'しよう',
    'すか', 'ずつ', 'すね', 'すべて', 'せる', 'そこ', 'そちら', 'そっち', 'そで', 'それ', 'それぞれ', 'たい',
    'たかい', 'たくさん', 'たち', 'たび', 'だめ', 'ちゃ', 'ちゃん', 'てん', 'とき', 'どこ', 'どちら', 'どっち',
    'どの', 'なか', 'なに', 'など', 'なん', 'はじめ', 'はず', 'はるか', 'はん', 'ひと', 'ひとつ', 'ふく', 'ぶり',
    'べつ', 'ほか', 'まさ', 'まし', 'まとも', 'まま', 'みたい', 'みつ', 'みなさん', 'みんな', 'もと', 'もの',
    'やつ', 'よう', 'よそ', 'わけ', 'わたし', 'われ', 'ん', 'ア', 'イ', 'ウ', 'エ', 'オ', 'カ', 'キ', 'ク', 'ケ',
    'コ', 'サ', 'シ', 'ス', 'セ', 'ソ', 'タ', 'チ', 'ツ', 'テ', 'ト', 'ナ', 'ニ', 'ヌ', 'ネ', 'ノ', 'ハ', 'ヒ', 'フ',
    'ヘ', 'ホ', 'マ', 'ミ', 'ム', 'メ', 'モ', 'ヤ', 'ユ', 'ヨ', 'ラ', 'リ', 'ル', 'レ', 'ロ', 'ワ', 'ヲ', 'ン',
    '一', '一方', '一部', '上', '下', '何', '何か', '全体', '全部', '他', '内', '前', '後',
    'だ', 'です', 'どう', 'ます', 'ある', 'いる', 'おる', 'です', 'ない', 'ように'
}

# MeCabトークナイザの初期化（fugashi + ipadic使用）
def init_mecab():
    """
    MeCabトークナイザを初期化します
    """
    try:
        return fugashi.Tagger('-d {}'.format(ipadic.DICDIR))
    except Exception as e:
        logger.error(f"MeCabトークナイザの初期化に失敗: {e}")
        return None

# 日本語テキストの前処理
def preprocess_japanese(text: str) -> List[str]:
    """
    日本語テキストの前処理を行います
    - 全角->半角変換
    - トークン化
    - ストップワード除去
    - 名詞・動詞・形容詞の原型抽出

    Args:
        text: 前処理対象の日本語テキスト

    Returns:
        前処理済みの単語リスト
    """
    if not text:
        return []

    # テキストの正規化
    text = unicodedata.normalize('NFKC', text)

    try:
        # MeCabトークナイザの初期化
        mecab_tagger = init_mecab()
        if not mecab_tagger:
            return []

        # トークン化して単語と品詞を抽出
        tokens = []
        for word in mecab_tagger(text):
            # 品詞の確認
            pos = word.feature.pos

            # 名詞、動詞、形容詞のみを抽出
            if pos in ('名詞', '動詞', '形容詞'):
                # 原型（辞書形）を使用（なければ表層形を使用）
                base_form = word.feature.lemma
                if base_form is None:
                    base_form = word.surface

                # ストップワード、数字のみ、1文字のトークンを除外
                if (base_form not in JAPANESE_STOPWORDS and
                    not base_form.isdigit() and
                    len(base_form) > 1):
                    tokens.append(base_form)

        return tokens

    except Exception as e:
        logger.error(f"日本語テキストの前処理でエラーが発生: {e}")
        return []

# 英語テキストの前処理
def preprocess_english(text: str) -> List[str]:
    """
    英語テキストの前処理を行います
    - 小文字化
    - トークン化
    - ストップワード除去
    - レンマ化（原型化）

    Args:
        text: 前処理対象の英語テキスト

    Returns:
        前処理済みの単語リスト
    """
    if not text:
        return []

    try:
        # 小文字化
        text = text.lower()

        # 特殊文字の除去（アルファベット、数字、スペース以外を除去）
        text = re.sub(r'[^a-z0-9\s]', ' ', text)

        # トークン化
        tokens = word_tokenize(text)

        # ストップワード除去
        stop_words = set(stopwords.words('english'))
        tokens = [word for word in tokens if word not in stop_words]

        # レンマ化（語の原型化）
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(word) for word in tokens]

        # 短いトークンや数字のみのトークンを除去
        tokens = [word for word in tokens if len(word) > 2 and not word.isdigit()]

        return tokens

    except Exception as e:
        logger.error(f"英語テキストの前処理でエラーが発生: {e}")
        return []

# 言語検出と前処理適用
def preprocess_text(text: str) -> List[str]:
    """
    テキストの言語を検出し、適切な前処理を適用します

    Args:
        text: 前処理対象のテキスト

    Returns:
        前処理済みの単語リスト
    """
    if not text:
        return []

    # 簡易的な言語判定（日本語の文字が一定比率以上含まれるかで判定）
    jp_chars_ratio = len([c for c in text if ord(c) > 0x3000]) / max(len(text), 1)

    if jp_chars_ratio > 0.2:  # 20%以上が日本語文字なら日本語と判定
        return preprocess_japanese(text)
    else:
        return preprocess_english(text)
