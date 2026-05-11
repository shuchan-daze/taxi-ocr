"""日報分類の純粋 A/B/C 比較スクリプト（アプリ本体と独立）。

目的:
    同じ画像・同じプロンプトを複数モデルに与え、出力 JSON を fields 単位で diff して
    「モデル差のみ」を可視化する対照実験。Streamlit や app の前処理を介在させない。

設定:
    MODELS リストに比較したいモデルを並べる。先頭がリファレンス（基準）。
    リファレンス以外のモデルを順に diff して、何件一致したかをサマリ。

使い方:
    1. secrets.toml に ANTHROPIC_API_KEY を追記
    2. テスト画像を test_data/ に配置
    3. venv/bin/python compare_nippou.py test_data/*.HEIC test_data/*.JPEG
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
from pathlib import Path

import toml
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

# ============================================================
# 比較対象モデル: 先頭がリファレンス（基準）。残りを diff する。
# 全部 Anthropic 系（Gemini 2.5 Flash は前回検証で精度不可と判明したため除外）。
# ============================================================
# variant: 'inline' = 現状のアプリ実装と同じ (image + prompt を user message に同梱)
#          'cached' = NIPPOU_PROMPT を system prompt に移し cache_control を立てる
#                     （Prompt Caching を効かせる本番候補。inline と出力が一致するか検証必須）
MODELS = [
    {'label': 'claude-opus-4-5', 'model': 'claude-opus-4-5', 'variant': 'inline'},          # 基準
    {'label': 'claude-opus-4-5-cached', 'model': 'claude-opus-4-5', 'variant': 'cached'},   # caching 検証
    {'label': 'claude-opus-4-7', 'model': 'claude-opus-4-7', 'variant': 'inline'},          # 新 Opus
    {'label': 'claude-sonnet-4-6', 'model': 'claude-sonnet-4-6', 'variant': 'inline'},      # コスト候補
]

# v1.4.00 の app.py:NIPPOU_PROMPT と一致させること
NIPPOU_PROMPT = """これはタクシー乗務員の手書き日報です。
日報の各行を上から順に処理し、以下のルールで JSON 配列を返してください。

【通常行】
{"meter_no": 連番（1始まり、上から何番目の乗客か）, "passengers": 人数（数字）, "kind": "現収" or "未収", "memo": "Visa/Suica/Uber/交通系/現金 等", "case": "normal", "nippou_amount": 日報の現収/未収欄に書かれた金額の数字（読めない/書かれていない場合は null）}

【現収/未収判定】
- 摘要に「Visa」「Uber」「Suica」「交通系」「PayPay」等のカード/電子マネー名 → 必ず「未収」
- 摘要が空欄、または「現金」 → 「現収」

【nippou_amount について】
- 日報の現収/未収欄に手書きで書かれている金額をそのまま読み取る（数値のみ、カンマ無し）。
- 読み取れない・書かれていない・かすれている場合は null を返す。
- 「+100」のような追記は除外し、メインの金額のみを読む。
- この値は出力テーブルの金額にはならない（出力金額はメーター明細から取られる）。
  メーター明細との比較で「日報誤記の検知（mismatch ハイライト）」のためだけに使われる。

【障害者割引（障割）】
摘要に「障割」「障害者割引」の記載がある割引額行は、
日報の現収欄に書かれていても kind="未収" として読み取ること。
case="discount" として判定し、割引額を nippou_amount に記録する。

【から回し行の判定】
- 乗車区間が取り消し線（横線・斜線・×印）で消されており、現収欄に「+100」「+200」のように「+金額」だけ書かれた行は「から回し」（メーター消し忘れ）。
- この行は ride として出力しない。
- 代わりに、この行の直前の通常行の case を "overage" に変更し、overage_amount にその金額（数値）をセットする。

【出力例】
[
  {"meter_no": 1, "passengers": 2, "kind": "未収", "memo": "アプリ", "case": "normal", "nippou_amount": 1500},
  {"meter_no": 2, "passengers": 1, "kind": "現収", "memo": "現金", "case": "normal", "nippou_amount": null},
  {"meter_no": 21, "passengers": 2, "kind": "未収", "memo": "Visa", "case": "overage", "overage_amount": 100, "nippou_amount": 1600}
]

【厳守】
- JSON 配列のみを返す。前後に余計なテキスト・コードブロック記号・思考過程は付けない。
- 「+100」を「1,100」と誤読しない。「+200」を「1,200」と誤読しない。
- 取り消し線行を独立した ride として出力しない。
- 出力テーブルの最終金額は **メーター明細書の値** が使われる（nippou_amount は mismatch 検知のみに使われる）。"""


def load_anthropic_key():
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        secrets_path = Path(__file__).parent / 'secrets.toml'
        if secrets_path.exists():
            key = toml.load(secrets_path).get('ANTHROPIC_API_KEY')
    if not key:
        sys.exit('ERROR: ANTHROPIC_API_KEY が見つかりません。secrets.toml または env に設定してください。')
    return key


def load_image_normalized(path):
    """アプリと同じ前処理: EXIF orientation + 3000px thumbnail + JPEG q=92。
    両モデルに完全に同じバイト列を渡して「画像処理由来の差」を排除する。"""
    from PIL import ExifTags
    img = Image.open(path)
    try:
        orientation = next((k for k, v in ExifTags.TAGS.items() if v == 'Orientation'), None)
        exif = img._getexif() if orientation else None
        if exif:
            o = exif.get(orientation)
            if o == 3: img = img.rotate(180, expand=True)
            elif o == 6: img = img.rotate(270, expand=True)
            elif o == 8: img = img.rotate(90, expand=True)
    except Exception:
        pass
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')
    img.thumbnail((3000, 3000))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=92)
    return buf.getvalue()


def call_claude(anthropic_key, jpeg_bytes, model_config):
    """variant に応じて inline / cached のどちらかで Claude を呼ぶ。
    inline: image + NIPPOU_PROMPT を user message に同梱（既存アプリと同じ）
    cached: NIPPOU_PROMPT を system prompt に移し cache_control を立てる
            → 2 回目以降の入力コストが 1/10 になる。出力は inline と同じになる想定だが要検証。"""
    import anthropic
    client = anthropic.Anthropic(api_key=anthropic_key)
    b64 = base64.standard_b64encode(jpeg_bytes).decode()
    model_name = model_config['model']
    variant = model_config['variant']

    kwargs = {
        'model': model_name,
        'max_tokens': 4000,
    }
    if 'opus-4-7' not in model_name:
        kwargs['temperature'] = 0

    if variant == 'cached':
        kwargs['system'] = [{
            'type': 'text',
            'text': NIPPOU_PROMPT,
            'cache_control': {'type': 'ephemeral'},
        }]
        kwargs['messages'] = [{'role': 'user', 'content': [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': b64}},
        ]}]
    else:  # inline
        kwargs['messages'] = [{'role': 'user', 'content': [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': b64}},
            {'type': 'text', 'text': NIPPOU_PROMPT},
        ]}]

    res = client.messages.create(**kwargs)
    # キャッシュヒット状況をログ出力
    usage = getattr(res, 'usage', None)
    if usage:
        cache_read = getattr(usage, 'cache_read_input_tokens', 0) or 0
        cache_write = getattr(usage, 'cache_creation_input_tokens', 0) or 0
        if cache_read or cache_write:
            print(f'       [cache] read={cache_read} write={cache_write} tokens', flush=True)
    return res.content[0].text.strip()


def extract_rides(text):
    m = re.search(r'\[.*\]', text or '', re.DOTALL)
    if not m:
        return None, 'JSON 配列が見つからない'
    try:
        return json.loads(m.group(0)), None
    except json.JSONDecodeError as e:
        return None, f'JSON parse error: {e}'


def diff_rides(ref_rides, other_rides):
    """ref を基準に other との行・フィールド単位の差分を抽出。"""
    max_len = max(len(ref_rides), len(other_rides))
    diffs = []
    fields = ('meter_no', 'passengers', 'kind', 'memo', 'case', 'nippou_amount', 'overage_amount')
    for i in range(max_len):
        ref = ref_rides[i] if i < len(ref_rides) else None
        oth = other_rides[i] if i < len(other_rides) else None
        if ref is None:
            diffs.append((i, 'EXTRA_IN_OTHER', None, oth))
            continue
        if oth is None:
            diffs.append((i, 'MISSING_IN_OTHER', ref, None))
            continue
        row_diff = {f: (ref.get(f), oth.get(f)) for f in fields if ref.get(f) != oth.get(f)}
        if row_diff:
            diffs.append((i, 'MISMATCH', ref, oth, row_diff))
    return diffs


def main(image_paths):
    anthropic_key = load_anthropic_key()
    reference = MODELS[0]
    others = MODELS[1:]
    match_count = {m['label']: 0 for m in others}
    total = 0

    for path in image_paths:
        path = Path(path)
        if not path.exists():
            print(f'⚠️  SKIP: {path} が見つかりません')
            continue
        print(f'\n{"="*70}')
        print(f'📄 {path.name}')
        print(f'{"="*70}')
        try:
            jpeg_bytes = load_image_normalized(path)
        except Exception as e:
            print(f'❌ 画像読み込み失敗: {e}')
            continue

        results = {}
        skip_this_image = False
        for m in MODELS:
            label = m['label']
            print(f'  → {label} 呼び出し中...', flush=True)
            try:
                text = call_claude(anthropic_key, jpeg_bytes, m)
                rides, err = extract_rides(text)
            except Exception as e:
                print(f'  ❌ {label} 失敗: {e}')
                skip_this_image = True
                break
            if err:
                print(f'  ❌ {label} 出力解析失敗: {err}')
                print(f'  RAW: {text[:200]}')
                skip_this_image = True
                break
            results[label] = rides
            print(f'  ✓ {label}: {len(rides)} rides')

        if skip_this_image:
            continue

        total += 1
        ref_rides = results[reference['label']]
        print(f'  📌 基準: {reference["label"]} = {len(ref_rides)} rides')

        for m in others:
            label = m['label']
            other_rides = results[label]
            diffs = diff_rides(ref_rides, other_rides)
            if not diffs:
                print(f'  🟢 {label}: 完全一致')
                match_count[label] += 1
            else:
                print(f'  🔴 {label}: 差分 {len(diffs)} 件')
                for d in diffs[:8]:
                    idx, kind = d[0], d[1]
                    if kind == 'MISMATCH':
                        _, _, ref, oth, row_diff = d
                        diff_str = ', '.join(f'{f}: {av!r}→{bv!r}' for f, (av, bv) in row_diff.items())
                        print(f'      [{idx}] {diff_str}')
                    elif kind == 'MISSING_IN_OTHER':
                        print(f'      [{idx}] {label} で欠落: {d[2]}')
                    else:
                        print(f'      [{idx}] {label} が余分: {d[3]}')
                if len(diffs) > 8:
                    print(f'      ...他 {len(diffs) - 8} 件省略')

    print(f'\n{"="*70}')
    print(f'📊 最終サマリ（基準: {reference["label"]}）')
    print(f'{"="*70}')
    for m in others:
        print(f'  {m["label"]}: {match_count[m["label"]]} / {total} 画像で完全一致')
    print(f'{"="*70}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('使い方: python compare_nippou.py <image1> [image2 ...]')
    main(sys.argv[1:])
