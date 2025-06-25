#!/usr/bin/env python3
"""
ログ機能テスト用スクリプト
異なるレベルのログを生成して、ログファイルの出力を確認します
"""
import sys
import os
import time
from datetime import datetime
from src.utils.common import setup_logger
import config

# ディレクトリの場所を確認して、必要なら作成する
if not os.path.exists(config.LOG_DIR):
    os.makedirs(config.LOG_DIR)
    print(f"ログディレクトリを作成しました: {config.LOG_DIR}")
else:
    print(f"ログディレクトリがすでに存在します: {config.LOG_DIR}")

def main():
    # テスト用ロガーのインスタンスを作成
    logger = setup_logger('test_logging')

    logger.info('----------- ログテスト開始 -----------')

    # 各ログレベルでメッセージを出力
    logger.debug('これはDEBUGレベルのログメッセージです')
    logger.info('これはINFOレベルのログメッセージです')
    logger.warning('これはWARNINGレベルのログメッセージです')
    logger.error('これはERRORレベルのログメッセージです')
    logger.critical('これはCRITICALレベルのログメッセージです')

    # 例外をキャッチしてログ
    try:
        x = 1 / 0
    except Exception as e:
        logger.exception('例外が発生しました！詳細なトレースバック情報を含みます')

    # 日本語文字列のログ
    logger.info('日本語を含むログメッセージ: こんにちは世界！')

    # 複数行の情報をログ
    multiline_info = """
    これは
    複数行の
    ログメッセージです。
    インデントと改行が
    保持されるかテストします。
    """
    logger.info(multiline_info)

    # 繰り返しログを生成（ファイル回転のテスト用）
    for i in range(10):
        logger.info(f'繰り返しログ #{i+1}: ファイル回転機能のテスト')
        time.sleep(0.1)  # わずかな遅延

    logger.info('----------- ログテスト終了 -----------')

    # ログファイルの場所を表示
    import os
    today = time.strftime('%Y-%m-%d')
    log_file = os.path.join(config.LOG_DIR, f"{today}_test_logging.log")
    error_log_file = os.path.join(config.LOG_DIR, f"{today}_test_logging_error.log")

    print(f"\nログファイルの場所:")
    print(f"  一般ログ: {log_file}")
    print(f"  エラーログ: {error_log_file}")
    print(f"\n以下のコマンドでログを確認できます:")
    print(f"  cat {log_file}")
    print(f"  cat {error_log_file}")

if __name__ == '__main__':
    main()
