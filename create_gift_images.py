"""
10種ギフト画像生成スクリプト
スマホ最適化PNG (1080px幅) を生成し imgbb にアップロードする
"""

from PIL import Image, ImageDraw, ImageFont
import os
import base64
import requests

# ===== 設定 =====
IMGBB_API_KEY = "eb86eeb3ecc94fa091596fb9fee87764"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "gift_images")

FONT_REGULAR = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"

# カラー定義
COLOR_NAVY = "#1C2B4A"
COLOR_WHITE = "#FFFFFF"
COLOR_TEXT = "#333333"
COLOR_BG = "#FFFFFF"
COLOR_SECTION_BG = "#1C2B4A"

WIDTH = 1080
MIN_HEIGHT = 1920

BANNER_HEIGHT = 200
FOOTER_HEIGHT = 80
SECTION_ITEM_LINE_HEIGHT = 40
SECTION_PADDING_V = 20
SECTION_MARGIN_H = 40
SECTION_HEADER_HEIGHT = 60
SECTION_GAP = 24
ITEM_INDENT = 50
ITEM_FONT_SIZE = 22


# ===== ユーティリティ =====

def load_font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def wrap_text(text, font, max_width, draw):
    """テキストを max_width 以内で折り返して行リストを返す"""
    lines = []
    for paragraph in text.split('\n'):
        words = list(paragraph)
        current_line = ""
        for char in words:
            test = current_line + char
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = char
            else:
                current_line = test
        lines.append(current_line)
    return lines


def calc_wrapped_height(text, font, max_width, draw, line_height):
    lines = wrap_text(text, font, max_width, draw)
    return len(lines) * line_height


def upload_to_imgbb(image_path, api_key):
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    response = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": api_key, "image": image_data}
    )
    result = response.json()
    if result["success"]:
        return result["data"]["url"]
    else:
        raise Exception(f"imgbb upload failed: {result}")


# ===== 画像構築ヘルパー =====

class ImageBuilder:
    """スクロール描画用ビルダー（縦サイズを動的に計算）"""

    def __init__(self, width):
        self.width = width
        self.elements = []  # (type, data) のリスト

    def add_banner(self, title, subtitle):
        self.elements.append(('banner', {'title': title, 'subtitle': subtitle}))

    def add_section_header(self, text):
        self.elements.append(('section_header', {'text': text}))

    def add_items(self, items):
        """items: str のリスト（各行テキスト）"""
        self.elements.append(('items', {'items': items}))

    def add_gap(self, px=24):
        self.elements.append(('gap', {'px': px}))

    def add_footer(self):
        self.elements.append(('footer', {}))

    def _measure_height(self):
        """仮描画して総高さを計算"""
        # 仮のイメージで textbbox を使う
        dummy_img = Image.new('RGB', (self.width, 100))
        dummy_draw = ImageDraw.Draw(dummy_img)
        font_item = load_font(FONT_REGULAR, ITEM_FONT_SIZE)
        font_header = load_font(FONT_BOLD, 26)

        total_h = 0
        max_text_width = self.width - SECTION_MARGIN_H * 2 - ITEM_INDENT

        for etype, data in self.elements:
            if etype == 'banner':
                total_h += BANNER_HEIGHT
            elif etype == 'section_header':
                total_h += SECTION_GAP + SECTION_HEADER_HEIGHT
            elif etype == 'items':
                total_h += SECTION_PADDING_V
                for item in data['items']:
                    lines = wrap_text(item, font_item, max_text_width, dummy_draw)
                    total_h += len(lines) * SECTION_ITEM_LINE_HEIGHT
                total_h += SECTION_PADDING_V
            elif etype == 'gap':
                total_h += data['px']
            elif etype == 'footer':
                total_h += FOOTER_HEIGHT

        return max(total_h, MIN_HEIGHT)

    def render(self, output_path):
        h = self._measure_height()
        img = Image.new('RGB', (self.width, h), COLOR_BG)
        draw = ImageDraw.Draw(img)

        font_title = load_font(FONT_BOLD, 36)
        font_subtitle = load_font(FONT_REGULAR, 22)
        font_section = load_font(FONT_BOLD, 26)
        font_item = load_font(FONT_REGULAR, ITEM_FONT_SIZE)
        font_footer = load_font(FONT_REGULAR, 24)

        y = 0
        max_text_width = self.width - SECTION_MARGIN_H * 2 - ITEM_INDENT

        for etype, data in self.elements:
            if etype == 'banner':
                # バナー背景
                draw.rectangle([0, y, self.width, y + BANNER_HEIGHT], fill=COLOR_NAVY)
                # タイトル
                t_bbox = draw.textbbox((0, 0), data['title'], font=font_title)
                t_w = t_bbox[2] - t_bbox[0]
                t_x = (self.width - t_w) // 2
                # バナー内でタイトルと副題を縦に中央寄せ
                sub_bbox = draw.textbbox((0, 0), data['subtitle'], font=font_subtitle)
                sub_w = sub_bbox[2] - sub_bbox[0]
                total_text_h = (t_bbox[3] - t_bbox[1]) + 12 + (sub_bbox[3] - sub_bbox[1])
                t_y = y + (BANNER_HEIGHT - total_text_h) // 2
                draw.text((t_x, t_y), data['title'], font=font_title, fill=COLOR_WHITE)
                sub_x = (self.width - sub_w) // 2
                sub_y = t_y + (t_bbox[3] - t_bbox[1]) + 12
                draw.text((sub_x, sub_y), data['subtitle'], font=font_subtitle, fill=COLOR_WHITE)
                y += BANNER_HEIGHT

            elif etype == 'section_header':
                y += SECTION_GAP
                draw.rectangle([SECTION_MARGIN_H, y, self.width - SECTION_MARGIN_H, y + SECTION_HEADER_HEIGHT], fill=COLOR_SECTION_BG)
                s_bbox = draw.textbbox((0, 0), data['text'], font=font_section)
                s_h = s_bbox[3] - s_bbox[1]
                s_y = y + (SECTION_HEADER_HEIGHT - s_h) // 2
                draw.text((SECTION_MARGIN_H + 16, s_y), data['text'], font=font_section, fill=COLOR_WHITE)
                y += SECTION_HEADER_HEIGHT

            elif etype == 'items':
                y += SECTION_PADDING_V
                for item in data['items']:
                    lines = wrap_text(item, font_item, max_text_width, draw)
                    for li, line in enumerate(lines):
                        draw.text((SECTION_MARGIN_H + ITEM_INDENT, y), line, font=font_item, fill=COLOR_TEXT)
                        y += SECTION_ITEM_LINE_HEIGHT
                y += SECTION_PADDING_V

            elif etype == 'gap':
                y += data['px']

            elif etype == 'footer':
                # フッターは画像の末尾
                footer_y = h - FOOTER_HEIGHT
                draw.rectangle([0, footer_y, self.width, h], fill=COLOR_NAVY)
                footer_text = "© 低単価ウェブデザイナー救済のプロ /岡本"
                f_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
                f_w = f_bbox[2] - f_bbox[0]
                f_h = f_bbox[3] - f_bbox[1]
                draw.text(
                    ((self.width - f_w) // 2, footer_y + (FOOTER_HEIGHT - f_h) // 2),
                    footer_text, font=font_footer, fill=COLOR_WHITE
                )

        img.save(output_path, 'PNG')
        print(f"  保存: {output_path}")
        return output_path


# ===== 各ギフト画像の定義 =====

def build_gift_01(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("プロフィール改善チェックリスト", "32項目")
    b.add_section_header("アカウント設計（1-8）")
    b.add_items([
        "1. アイコンは顔写真か作業写真にしている",
        "2. 名前にサービス内容のキーワードが入っている",
        "3. 肩書が「誰の何を解決するか」になっている",
        "4. プロフ1行目に誰向けか明示している",
        "5. プロフ文に実績数字が1つ以上ある",
        "6. プロフ文は5行以内に収まっている",
        "7. 懇願表現（フォローして等）がない",
        "8. リンクが設置されている",
    ])
    b.add_section_header("発信設計（9-16）")
    b.add_items([
        "9. 投稿テーマが1つに絞られている",
        "10. 過去30日に10件以上の投稿がある",
        "11. フィードを見て3秒で専門性が分かる",
        "12. 固定投稿に実績か自己紹介がある",
        "13. キャプション1行目にフックがある",
        "14. ハッシュタグが5個以内",
        "15. 投稿時間が揃っている",
        "16. 日常も定期的に発信している",
    ])
    b.add_section_header("価値提供（17-24）")
    b.add_items([
        "17. フォロワーの悩みを把握している",
        "18. 「あなたへ書いた」と感じる投稿が多い",
        "19. 教育系とエンタメ系が7:3の比率",
        "20. 自分の持論を定期的に発信している",
        "21. 競合と差別化できるポジションがある",
        "22. ターゲットに刺さる言葉を使っている",
        "23. 投稿にCTAが含まれている",
        "24. 保存される投稿が月1本以上ある",
    ])
    b.add_section_header("集客導線（25-32）")
    b.add_items([
        "25. 問い合わせの入口が明確にある",
        "26. LINEやDMへの誘導がある",
        "27. プレゼントや特典の設計がある",
        "28. 問い合わせまでの流れが想像できる",
        "29. 定期的にサービス内容を投稿している",
        "30. 新規フォロワーへの自己紹介がある",
        "31. コメント返信をしている",
        "32. インサイトを週1回確認している",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_01_prof.png"))


def build_gift_02(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("単価3倍の提案文", "Before / After 実例")
    b.add_section_header("Before（よくある失敗例）")
    b.add_items([
        "「はじめまして。ウェブデザイナーをしております。",
        " ご依頼の件、ぜひお受けしたいと思います。",
        " LP制作が得意です。丁寧に対応いたします。",
        " よろしくお願いいたします。」",
        "",
        "問題: 誰でも書ける / 強みゼロ / 安くしか見えない",
    ])
    b.add_section_header("After（単価3倍になった提案文）")
    b.add_items([
        "「はじめまして。岡本と申します。",
        " 貴社の課題をプロフィールで確認しました。",
        " 直近3ヶ月、EC系LPでCV率2.8%→5.1%に改善した実績があります。",
        " 今回の案件では、ABテスト設計まで提案できます。",
        " 予算は○万円を想定しています。",
        " まず30分のご相談からでも可能です。」",
    ])
    b.add_section_header("単価3倍の3原則")
    b.add_items([
        "原則1: 「お願いします」→「貢献できます」に変える",
        "原則2: 抽象的なPR → 数字・事例1つ",
        "原則3: 価値を提示してから金額を出す",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_02_teian.png"))


def build_gift_03(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("高単価を引き寄せる発信の型", "3パターン")
    b.add_section_header("型1: 問題提起型")
    b.add_items([
        "書き出し: 「○○で悩んでいる人へ」",
        "例: 「単価が上がらない人には共通点がある」",
        "効果: ターゲットが自分のことと感じて反応する",
    ])
    b.add_section_header("型2: 実績証拠型")
    b.add_items([
        "書き出し: 「○○の結果が出た話」",
        "例: 「LP制作を変えたら受注単価が2.5倍になった件」",
        "ポイント: 数字・期間・Before/Afterを必ず入れる",
    ])
    b.add_section_header("型3: 思考転換型")
    b.add_items([
        "書き出し: 「常識を逆から見せる」",
        "例: 「提案数を増やすほど単価が下がる理由」",
        "効果: 同業の投稿と真逆の主張が差別化になる",
    ])
    b.add_section_header("高単価クライアントが反応する共通点")
    b.add_items([
        "・「私に向けて書いてある」と感じさせる",
        "・抽象論ではなく具体的な数字・事例がある",
        "・コンテンツ自体に価値がある（保存される）",
        "・継続して同じテーマを発信している",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_03_hassin.png"))


def build_gift_04(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("稼げない人 vs 稼げる人", "10の違い")
    b.add_section_header("比較表（左: 稼げない人 / 右: 稼げる人）")
    b.add_items([
        "提案: 多く送る  /  質の高い1件を送る",
        "価格: 相場に合わせる  /  自分の価値から決める",
        "発信: 「できます」で終わる  /  「課題を解決できます」まで言う",
        "実績: 実績がないと諦める  /  伝え方で勝負する",
        "交渉: 言われた金額を飲む  /  理由をつけて提案する",
        "学習: スキルだけ磨く  /  営業・マーケも並行して学ぶ",
        "専門: 広く浅くやる  /  ニッチに特化する",
        "客層: 誰でもOK  /  理想のクライアントを選ぶ",
        "時間: 制作時間を売る  /  成果・価値を売る",
        "行動: 準備が整ってから  /  今すぐ小さく始める",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_04_chigai.png"))


def build_gift_05(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("AIで制作時間を1/3にする", "実務ワークフロー")
    b.add_section_header("フェーズ1: ヒアリング〜方向性（旧60分→新20分）")
    b.add_items([
        "・Claudeにヒアリングシートを生成させる",
        "・競合サイト3件を貼り付けて「違い」を分析させる",
        "・ファーストビューのコピー案を5パターン出させる",
    ])
    b.add_section_header("フェーズ2: ワイヤー〜デザイン（旧3時間→新1時間）")
    b.add_items([
        "・サイトマップをAIに提案させて自分で精査",
        "・ChatGPTにセクション構成案を出させる",
        "・Figmaプラグインでグリッド・コンポーネントを自動配置",
    ])
    b.add_section_header("フェーズ3: テキスト・コピー（旧2時間→新30分）")
    b.add_items([
        "・「このターゲット向けにボディコピーを書いて」と指示",
        "・生成→編集→確認のサイクルを3回まわす",
        "・AIの文章を「自分の言葉」に変換する（必須）",
    ])
    b.add_section_header("時短の落とし穴")
    b.add_items([
        "・AIの出力をそのまま使うと「量産品」に見える",
        "・「確認・判断」は人間がやる",
        "・ツールに頼りすぎると思考力が落ちる",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_05_ai_jitan.png"))


def build_gift_06(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("断られない見積もりの出し方", "価格設定シート")
    b.add_section_header("価格設定の3ステップ")
    b.add_items([
        "Step1: 「かかる時間 × 希望時給」で原価を計算する",
        "  例: 40時間 × 5,000円 = 200,000円（原価）",
        "Step2: 価値提供の「結果」から逆算する",
        "  例: CV率改善で月10万円の売上増 → LP制作費30万は適正",
        "Step3: ポジションに合わせて「底値」を決める",
        "  例: 安い競合と比べず価値で勝負する",
    ])
    b.add_section_header("断られない見積書の構成")
    b.add_items([
        "・課題の確認（ヒアリング内容の要約）",
        "・提案内容（具体的な成果物リスト）",
        "・予想される効果（数字・根拠）",
        "・料金 + 内訳",
        "・スケジュール",
    ])
    b.add_section_header("値下げ要求への返し方")
    b.add_items([
        "「費用は変えられませんが、",
        "  納期を1週間延ばすことで対応できます」",
        "",
        "「その予算では○と○の2点に絞った",
        "  形でご提案できます」",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_06_mitsumori.png"))


def build_gift_07(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("単価を上げた交渉の実例", "LINEやり取り再現")
    b.add_section_header("状況")
    b.add_items([
        "継続案件: 初回5万円 → 3回目の更新時に10万円へ",
    ])
    b.add_section_header("実際のやり取り")
    b.add_items([
        "クライアント: 「来月もお願いしたいのですが」",
        "",
        "自分: 「今月のLP経由CVが先月比1.4倍になりました。",
        "      次回からABテスト設計まで含めますので",
        "      10万円でご提案します」",
        "",
        "クライアント: 「少し高いですね」",
        "",
        "自分: 「3ヶ月継続契約であれば8万円に対応できます」",
        "",
        "クライアント: 「では継続でお願いします」",
    ])
    b.add_section_header("単価交渉の3原則")
    b.add_items([
        "1. 交渉前に「実績数字」を用意する",
        "2. 値上げの理由は「スコープの拡大」で伝える",
        "3. 代替案（継続割引など）を必ず用意する",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_07_koushou.png"))


def build_gift_08(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("月50万到達までの90日", "ロードマップ")
    b.add_section_header("Day 1-30: ポジション確立期")
    b.add_items([
        "目標: 月5万円の案件を1件受注する",
        "- ターゲット・得意ジャンルを1つに絞る",
        "- ポートフォリオを3件整備する",
        "- プロフィール・提案文を完成させる",
        "- 10件提案してフィードバックを記録する",
    ])
    b.add_section_header("Day 31-60: 単価アップ期")
    b.add_items([
        "目標: 月15万円（5万×3件 or 15万×1件）",
        "- クラウドソーシングからSNS・紹介に移行",
        "- 提案→受注→納品のPDCAを3サイクル回す",
        "- 専門領域を深堀りして「専門家」を強化する",
    ])
    b.add_section_header("Day 61-90: スケール期")
    b.add_items([
        "目標: 月50万円",
        "- 継続案件を2件確保する（安定収入の土台）",
        "- 単価20万以上の案件1件を取る",
        "- SNS経由の問い合わせが月1件来る状態を作る",
        "- AIで制作時間を短縮して3案件同時対応",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_08_tsuki50.png"))


def build_gift_09(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("低単価から抜け出した3人の実話", "共通点は1つだった")
    b.add_section_header("Aさん（28歳・元会社員）")
    b.add_items([
        "状況: スクール卒業後8ヶ月で月収2万円止まり",
        "転換点: 「LP専門」に特化してポートフォリオを作り直した",
        "結果: 3ヶ月でLP案件の単価が5万→18万に上昇",
    ])
    b.add_section_header("Bさん（34歳・副業から独立）")
    b.add_items([
        "状況: 提案100件で採用率3%。消耗していた",
        "転換点: クラウドソーシングをやめてSNS発信に完全移行",
        "結果: SNS経由で月2件の問い合わせが来るようになった",
    ])
    b.add_section_header("Cさん（31歳・育児中フリーランス）")
    b.add_items([
        "状況: 「子育て中で時間がない」を理由に単価を下げていた",
        "転換点: AIツールで制作時間を1/3にして単価交渉に時間を使った",
        "結果: 稼働時間は変えずに月収が3倍になった",
    ])
    b.add_section_header("3人の共通点")
    b.add_items([
        "1. 「何でもやります」をやめた",
        "2. 実績を言語化して伝えるようにした",
        "3. 「安くすれば選ばれる」という思い込みを捨てた",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_09_jitsuwa.png"))


def build_gift_10(output_dir):
    b = ImageBuilder(WIDTH)
    b.add_banner("ポジショニング設計シート", "選ばれるデザイナーになる4ステップ")
    b.add_section_header("ポジション設計の4ステップ")
    b.add_items([
        "Step1: 自分が解決できる「課題」を1つ選ぶ",
        "  例: 「CVしないLPをCVするLPに変える」",
        "Step2: ターゲットを「誰に向けて」まで絞る",
        "  例: 「ECサイト運営の中小企業」",
        "Step3: 競合との「違い」を1行で言えるようにする",
        "  例: 「ABテスト設計まで含めるLP制作」",
        "Step4: 実績・数字で証明できる材料を集める",
    ])
    b.add_section_header("設計シート（記入欄）")
    b.add_items([
        "あなたが解決できる課題: ＿＿＿＿＿＿＿＿＿＿＿＿＿",
        "ターゲットクライアント: ＿＿＿＿＿＿＿＿＿＿＿＿＿",
        "競合との差別化ポイント: ＿＿＿＿＿＿＿＿＿＿＿＿＿",
        "実績・数字: ＿＿＿＿＿＿＿＿＿＿＿＿＿",
        "一言でのポジション表現: ＿＿＿＿＿＿＿＿＿＿＿＿＿",
    ])
    b.add_section_header("よくある失敗パターン")
    b.add_items([
        "NG: 「丁寧・誠実・スピード対応」→誰でも言える",
        "NG: 「何でも対応可能」→選ばれない",
        "OK: 「○○向けの○○専門家」→指名が来る",
    ])
    b.add_footer()
    return b.render(os.path.join(output_dir, "gift_10_position.png"))


# ===== メイン =====

GIFT_BUILDERS = [
    ("gift_01_prof.png", build_gift_01),
    ("gift_02_teian.png", build_gift_02),
    ("gift_03_hassin.png", build_gift_03),
    ("gift_04_chigai.png", build_gift_04),
    ("gift_05_ai_jitan.png", build_gift_05),
    ("gift_06_mitsumori.png", build_gift_06),
    ("gift_07_koushou.png", build_gift_07),
    ("gift_08_tsuki50.png", build_gift_08),
    ("gift_09_jitsuwa.png", build_gift_09),
    ("gift_10_position.png", build_gift_10),
]

# キーワードとファイルのマッピング（app.py更新用）
GIFT_KEYWORD_MAP = {
    "プロフ": "gift_01_prof.png",
    "提案文": "gift_02_teian.png",
    "発信": "gift_03_hassin.png",
    "違い": "gift_04_chigai.png",
    "AI時短": "gift_05_ai_jitan.png",
    "見積もり": "gift_06_mitsumori.png",
    "交渉": "gift_07_koushou.png",
    "月50万": "gift_08_tsuki50.png",
    "実話": "gift_09_jitsuwa.png",
    "ポジション": "gift_10_position.png",
}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== ギフト画像生成開始 ===")
    uploaded_urls = {}

    for filename, builder_func in GIFT_BUILDERS:
        print(f"\n[生成] {filename}")
        path = builder_func(OUTPUT_DIR)

        print(f"  imgbbアップロード中...")
        url = upload_to_imgbb(path, IMGBB_API_KEY)
        uploaded_urls[filename] = url
        print(f"  URL: {url}")

    print("\n=== 全画像アップロード完了 ===")
    print("\n--- URL一覧 ---")
    for fname, url in uploaded_urls.items():
        print(f"{fname}: {url}")

    # URL一覧をファイルに保存
    url_file = os.path.join(OUTPUT_DIR, "uploaded_urls.txt")
    with open(url_file, "w") as f:
        for fname, url in uploaded_urls.items():
            f.write(f"{fname}\t{url}\n")
    print(f"\nURLをファイルに保存: {url_file}")

    return uploaded_urls


if __name__ == "__main__":
    main()
