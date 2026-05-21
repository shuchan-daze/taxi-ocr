#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8501}"
OUT_DIR=".kamichizu_debug"
URL_FILE="$OUT_DIR/iphone_streamlit_url.txt"
QR_FILE="$OUT_DIR/iphone_streamlit_qr.png"

ip_address="$(ipconfig getifaddr en0 2>/dev/null || true)"
if [[ -z "$ip_address" ]]; then
  ip_address="$(ipconfig getifaddr en1 2>/dev/null || true)"
fi

if [[ -z "$ip_address" ]]; then
  echo "MacのWi-Fi IPを取得できませんでした。Wi-Fi接続を確認してください。"
  echo "手動確認: ipconfig getifaddr en0"
  exit 1
fi

url="http://$ip_address:$PORT"

mkdir -p "$OUT_DIR"
printf '%s\n' "$url" > "$URL_FILE"

echo "Streamlit URL:"
echo "$url"
echo
echo "iPhoneでMacと同じWi-Fiに接続し、このURLを開いてください。"

if command -v qrencode >/dev/null 2>&1; then
  qrencode -o "$QR_FILE" "$url"
  echo
  echo "QRコード:"
  echo "$QR_FILE"
  echo
  echo "iPhoneでこのQRを読み取ってください。"
  if command -v open >/dev/null 2>&1; then
    open "$QR_FILE"
  fi
else
  echo
  echo "qrencode が見つからないため、QR画像は生成していません。"
  echo "URLテキストは保存しました:"
  echo "$URL_FILE"
  echo
  echo "QR生成が必要なら qrencode をインストールしてください。"
fi
