#!/bin/sh
set -e

# Generate Xray config if VLESS variables are present
if [ -n "$VLESS_HOST" ] && [ -n "$VLESS_PORT" ] && [ -n "$VLESS_UUID" ]; then
  echo "[xray] enabling VLESS proxy to $VLESS_HOST:$VLESS_PORT"
  mkdir -p /etc/xray
  : "${VLESS_SERVICE_NAME:=movie}"
  : "${VLESS_TLS:=true}"
  : "${VLESS_GRPC:=true}"
  : "${VLESS_SNI:=}"
  : "${XRAY_SOCKS_PORT:=10808}"
  : "${XRAY_HTTP_PORT:=10809}"

  cat > /etc/xray/config.json << JSON
{
  "inbounds": [
    { "port": ${XRAY_SOCKS_PORT}, "listen": "127.0.0.1", "protocol": "socks", "settings": { "udp": true } },
    { "port": ${XRAY_HTTP_PORT},  "listen": "127.0.0.1", "protocol": "http" }
  ],
  "outbounds": [
    {
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "${VLESS_HOST}",
            "port": ${VLESS_PORT},
            "users": [ { "id": "${VLESS_UUID}", "encryption": "none" } ]
          }
        ]
      },
      "streamSettings": {
        "network": "grpc",
        "security": "tls",
        "grpcSettings": { "serviceName": "${VLESS_SERVICE_NAME}" }${VLESS_SNI:+,
        "tlsSettings": { "serverName": "${VLESS_SNI}" }}
      }
    }
  ]
}
JSON

  # start xray in background
  /usr/bin/xray -c /etc/xray/config.json &
  export YDL_PROXY="socks5h://127.0.0.1:${XRAY_SOCKS_PORT}"
  echo "[xray] started, YDL_PROXY=$YDL_PROXY"
fi

# start app
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
