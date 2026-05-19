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

# =============================
# A/B/C ストーリーシーケンス
# =============================
STORY_MESSAGES = {
    'A': [
        "Aね\n\n毎日何件も送って、\nそれだけで疲れ果てるやつだよね...",
        "ぼく、スクールで\n「才能ある！すごいね！」\nって言われてたんだよ（笑）\n\n信じてたんだよね、それを...",
        "でも始めたら全然そんなことなくて\n\n本業もあるのに\nすきま時間に提案文書いて送って\nまた返ってこない、また書く、また送る...（汗）\n\nなんかもう、虚しくてさ",
        "時給計算したらボランティアじゃん！ってなって（汗）\n\n「才能あるって言ってたじゃないか」\nって思ったけど誰にも言えなくて...\n\n本気でやめようと思ってたよ",
        "変わったきっかけはAIだったんだよね\n\nなんかさ、提案送り続けることが\n正解じゃなかったって気づいて\n\n発信して向こうから来てもらう形にしたら\n1ヶ月もしないうちに最初の連絡来た\n\n届け方を変えるだけだったんだよね\n\n何でも聞いてきて！",
    ],
    'B': [
        "Bね\n\n「まだスキルが足りないのかも...」\nって感じてるんだよね",
        "ぼくさ、スクールで褒められてたんだよ（笑）\n「才能ある！センスいい！」って\n\nだから自信あったんだよ、最初は...",
        "でも現場出たら全然通用しなくて（汗）\n\n「才能あるって言ってたのに！」\nってなったけど誰にも言えないじゃん...\n\nで、「スキルがまだ足りないのかも」って\nなるんだよね、ぼくもそうだった",
        "でもさ\n\n問題スキルじゃなかったんだよ！\n知識はあった、作れてた\n「どう届けるか」を誰も教えてくれてなかっただけで",
        "AIとマーケティング組み合わせてから\nなんか急に「あ、そういうことか！」ってなってさ\n\nスキルは今のままで良かった\n足りなかったのは組み合わせ方だったんだよね\n\nまた別のスクール探してたら\nたぶん同じことになってたと思う（笑）\n\n気になること何でも聞いて！",
    ],
    'C': [
        "Cね\n\nそれ一番しんどいよ...\n「何をすればいいかわからない」って",
        "ぼくもずっとそこにいたんだよね\n\n知識もあった、作れるものもあった\nでも「これをどう活かせばいいか」が\n全然わからなくて...（汗）",
        "スクールでは「才能ある！絶対いける！」\nって言われてたから信じてたんだけどさ（笑）\n\n始めたら現実が全然違って（汗）\n\n本業もあって支払いの不安もあって\nもう本当にどうしようかって感じだった",
        "AIに出会ってから変わった\n\nなんかさ、デザインとAI組み合わせたら\n「点が線になった」感覚があってさ\n\nあ、これだ！ってなった\n\n「何をすれば」ってずっと考えてる時間が\n一番もったいないんだよね\n\n何でも話せるから聞いてきて！",
    ],
}

# =============================
# プレゼント自動配信（2026-05-19 全面差し替え・CV検証10種）
# =============================
GIFT_MESSAGES = {
    'プロフ': [
        image_msg("https://i.ibb.co/yc5m7Ct7/4dfccdf9ea27.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '提案文': [
        image_msg("https://i.ibb.co/BKrbFDVs/6fc6858b19b0.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '発信': [
        image_msg("https://i.ibb.co/nsjq26VM/30dc1b8af84e.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '違い': [
        image_msg("https://i.ibb.co/JFtdgjPL/558c64828dd6.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    'AI時短': [
        image_msg("https://i.ibb.co/DnZpPdC/1ae24368864e.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '見積もり': [
        image_msg("https://i.ibb.co/PsKDNr3P/915d009c222b.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '交渉': [
        image_msg("https://i.ibb.co/5XCYg197/a2e31e4da3f6.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '月50万': [
        image_msg("https://i.ibb.co/XQ7MC3Q/bb05793cd586.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    '実話': [
        image_msg("https://i.ibb.co/yHNdwGb/96b2af46e5eb.png"),
        text_msg("なにかお悩みはありますか？\nどんな小さなことでもお気軽にどうぞ。"),
    ],
    'ポジション': [
        image_msg("https://i.ibb.co/TD6Ch89B/b24d09c69188.png"),
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
    if stripped in STORY_MESSAGES:
        return ('story', stripped)
    if stripped in GIFT_MESSAGES:
        return ('gift', stripped)

    # A/B/C は短いので「A と送って」「a」等を冒頭マッチで救う（大小文字許容）
    m = re.match(r'^([ABCabc])(?:[\s、。」』）)】\]！？!?,.]|$)', norm)
    if m and m.group(1).upper() in STORY_MESSAGES:
        return ('story', m.group(1).upper())

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


def text_msg(text):
    return {'type': 'text', 'text': text}


def image_msg(url):
    return {
        'type': 'image',
        'originalContentUrl': url,
        'previewImageUrl': url,
    }


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
            if kind == 'story':
                t = threading.Thread(target=send_sequence, args=(user_id, STORY_MESSAGES[key]))
                t.daemon = True
                t.start()
            elif kind == 'gift':
                t = threading.Thread(target=send_sequence, args=(user_id, GIFT_MESSAGES[key]))
                t.daemon = True
                t.start()

    return 'OK'


@app.route("/health", methods=['GET'])
def health():
    return 'OK', 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
