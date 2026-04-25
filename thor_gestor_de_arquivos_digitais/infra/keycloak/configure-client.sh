#!/bin/sh
set -eu

KCADM=/opt/keycloak/bin/kcadm.sh

: "${KC_SERVER:=http://keycloak:8080}"
: "${KC_ADMIN_USER:=admin}"
: "${KC_ADMIN_PASSWORD:=admin}"
: "${KC_REALM:=thor}"
: "${KC_CLIENT_ID:=thor-api}"
: "${FRONTEND_URL:=http://localhost:3000}"

echo "Aguardando Keycloak em ${KC_SERVER}..."
until "$KCADM" config credentials \
  --server "$KC_SERVER" \
  --realm master \
  --user "$KC_ADMIN_USER" \
  --password "$KC_ADMIN_PASSWORD" >/dev/null 2>&1; do
  sleep 2
done

CLIENT_UUID=$(
  "$KCADM" get clients \
    -r "$KC_REALM" \
    -q clientId="$KC_CLIENT_ID" \
    --fields id \
    --format csv |
    head -n 1 |
    tr -d '"' |
    tr -d '\r'
)

if [ -z "$CLIENT_UUID" ]; then
  echo "Client '${KC_CLIENT_ID}' não encontrado no realm '${KC_REALM}'." >&2
  exit 1
fi

"$KCADM" update "clients/${CLIENT_UUID}" \
  -r "$KC_REALM" \
  -s 'publicClient=true' \
  -s 'standardFlowEnabled=true' \
  -s 'directAccessGrantsEnabled=true' \
  -s "redirectUris=[\"${FRONTEND_URL}/auth/callback\",\"${FRONTEND_URL}/*\"]" \
  -s "webOrigins=[\"${FRONTEND_URL}\"]" \
  -s "attributes={\"post.logout.redirect.uris\":\"${FRONTEND_URL}/login##${FRONTEND_URL}/*\"}"

echo "Client '${KC_CLIENT_ID}' atualizado para usar '${FRONTEND_URL}'."
