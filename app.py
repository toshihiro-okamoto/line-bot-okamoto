from flask import Flask, request, abort
import requests as req
import json
import hmac
import hashlib
import base64
import threading
import time
import os
import re
import unicodedata

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']

DELAY = 5

# A/B/C ストーリーシーケンスは2026-05-21に無効化（手動対応に切り替え）
# STORY_MESSAGES = {} # 削除済み

def text_msg(text):
    return {'type': 'text', 'text': text}


def image_msg(url):
    return {
        'type': 'image',
        'originalContentUrl': url,
        'previewImageUrl': url,
    }


# =============================
# プレゼント自動配信（2026-05-21 Wow版・全面リライト10種）
# 内容はウェブスキ動画vault・清水コーチ講座準拠でフル詰め込み
# =============================
GIFT_MESSAGES = {
    'プロフ': [
        image_msg("https://i.ibb.co/vCY88gvg/33dfa27350f6.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '提案文': [
        image_msg("https://i.ibb.co/S4Wpgcrm/5b41d210c956.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '発信': [
        image_msg("https://i.ibb.co/sdpF2Dgs/1776e3693a2a.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '違い': [
        image_msg("https://i.ibb.co/5g8mNtJM/0a4634d9229f.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    'AI時短': [
        image_msg("https://i.ibb.co/prKWPQRc/52f907047aa5.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '見積もり': [
        image_msg("https://i.ibb.co/Cpq3Y5xN/b58e4befaa98.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '交渉': [
        image_msg("https://i.ibb.co/BWjQnVM/cba61326a006.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '月50万': [
        image_msg("https://i.ibb.co/WpfNbkvJ/67661eae5b82.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '実話': [
        image_msg("https://i.ibb.co/rRwZsBtD/98e0151d7e51.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    'ポジション': [
        image_msg("https://i.ibb.co/9HVnCd9N/4ddcf385a51f.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
}


# 句読点・装飾記号を取り除いて完全一致しなくても拾うためのマッチャー
_DECORATION_PATTERN = re.compile(
    r'^[\s「『""\'\'（()【\[\s]+|[\s」』""\'\'）)】\]！？!?。、,.\s]+$'
)


def match_keyword(text):
    """ユーザー入力からキーワードを判定。(種別, キー) を返す。該当なしは (None, None)。"""
    norm = unicodedata.normalize('NFKC', text).strip()

    # 装飾記号を剥がして完全一致チェック
    stripped = _DECORATION_PATTERN.sub('', norm)
    # story（A/B/C）は2026-05-21無効化のためチェックしない
    if stripped in GIFT_MESSAGES:
        return ('gift', stripped)

    # ギフトキーワードは2文字以上のみ部分一致で救う（「提案文ください」「修正お願い」など）
    for k in sorted(GIFT_MESSAGES.keys(), key=len, reverse=True):
        if len(k) >= 2 and k in norm:
            return ('gift', k)

    return (None, None)


def verify_signature(body, signature):
    hash_val = hmac.new(
        CHANNEL_SECRET.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash_val).decode('utf-8') == signature


def push_message(user_id, message_obj):
    """message_obj は LINE Messaging API の messages 配列の1要素（dict）"""
    req.post(
        'https://api.line.me/v2/bot/message/push',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        },
        json={
            'to': user_id,
            'messages': [message_obj]
        }
    )


def send_sequence(user_id, messages):
    for i, msg in enumerate(messages):
        if i > 0:
            time.sleep(DELAY)
        # 後方互換: str が来たらテキストメッセージとして送る
        if isinstance(msg, str):
            push_message(user_id, text_msg(msg))
        else:
            push_message(user_id, msg)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    if not verify_signature(body, signature):
        abort(400)

    events = json.loads(body).get('events', [])
    for event in events:
        if event.get('type') == 'message' and event['message'].get('type') == 'text':
            text = event['message']['text'].strip()
            user_id = event['source']['userId']

            kind, key = match_keyword(text)
            # story（A/B/C）は2026-05-21無効化。キーワードギフト10種のみ対応。
            if kind == 'gift':
                t = threading.Thread(target=send_sequence, args=(user_id, GIFT_MESSAGES[key]))
                t.daemon = True
                t.start()

    return 'OK'


@app.route("/health", methods=['GET'])
def health():
    return 'OK', 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
