from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import threading
import time
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])

DELAY = 60  # 各メッセージの間隔（秒）

MESSAGES = {
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

STEP3_MESSAGE = (
    "来てくれてありがとう\n\n"
    "スクール卒業後に案件ゼロで悩んでる人に\n"
    "使ってほしくて作ったから、ちゃんと話するね\n\n"
    "あなたが今一番詰まってるのどこ？\n"
    "教えてくれたら、あなた専用の話をするね\n\n"
    "　A と送って\n"
    "　→「提案しても選ばれない」\n\n"
    "　B と送って\n"
    "　→「スキル不足が不安でやめられない」\n\n"
    "　C と送って\n"
    "　→「何をすれば変わるかわからない」"
)

STEP3_KEYWORDS = {'ロードマップ', 'チェック', 'テンプレ', '読む'}


def send_sequence(user_id, messages):
    for i, msg in enumerate(messages):
        if i > 0:
            time.sleep(DELAY)
        line_bot_api.push_message(user_id, TextSendMessage(text=msg))


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id

    if text in MESSAGES:
        t = threading.Thread(target=send_sequence, args=(user_id, MESSAGES[text]))
        t.daemon = True
        t.start()
    elif text in STEP3_KEYWORDS:
        t = threading.Thread(target=send_sequence, args=(user_id, [STEP3_MESSAGE]))
        t.daemon = True
        t.start()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
