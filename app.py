from flask import Flask, request, abort
import json
import hmac
import hashlib
import base64
import os
import re
import unicodedata

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']

# =============================
# 2026-05-21 完全手動モードに切り替え
# A/B/Cストーリー・キーワードギフト自動送信をすべて無効化。
# キーワードを受信してもボットは何も返さない。
# 岡本がLINE管理画面から手動で返信する。
#
# 対応キーワード（手動送信用メモ）：
#   プロフ    → 01_プロフ_プロフィール改善32項目.pdf
#   提案文    → 02_提案文_単価3倍の提案文テンプレ集.pdf
#   発信      → 03_発信_Threadsで使える発信テンプレ集.pdf
#   違い      → 04_違い_稼げない人と稼げる人20の違い.pdf
#   AI時短    → 05_AI時短_コピペで使えるAI時短プロンプト10本.pdf
#   見積もり  → 06_見積もり_断られない見積もり5パターン.pdf
#   交渉      → 07_交渉_値下げに屈しない交渉スクリプト集.pdf
#   月50万    → 08_月50万_月50万までの90日ロードマップ.pdf
#   実話      → 09_実話_低単価から抜け出した3人の実話.pdf
#   ポジション→ 10_ポジション_AI×デザイン×業界ポジション設計シート.pdf
#
# PDFの保存場所:
#   Obsidian/副業AIデザインThreads/LINEプレゼントPDF/
# =============================


def verify_signature(body, signature):
    hash_val = hmac.new(
        CHANNEL_SECRET.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash_val).decode('utf-8') == signature


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    if not verify_signature(body, signature):
        abort(400)

    # 完全手動モード：すべてのメッセージイベントを受け取るが何も返送しない
    return 'OK'


@app.route("/health", methods=['GET'])
def health():
    return 'OK', 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
