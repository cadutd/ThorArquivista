#!/bin/sh
set -eu

KCADM=/opt/keycloak/bin/kcadm.sh

: "${KC_SERVER:=http://keycloak:8080}"
: "${KC_ADMIN_USER:=admin}"
: "${KC_ADMIN_PASSWORD:=admin}"
: "${KC_REALM:=thor}"
: "${KC_CLIENT_ID:=thor-api}"
: "${KC_BACKEND_CLIENT_ID:=$KC_CLIENT_ID}"
: "${KC_FRONTEND_CLIENT_ID:=$KC_CLIENT_ID}"
: "${FRONTEND_URL:=http://localhost:3000}"
: "${BACKEND_URL:=http://localhost:8000}"
: "${KC_APP_ADMIN_USER:=admin}"
: "${KC_APP_ADMIN_PASSWORD:=admin}"
: "${KC_APP_ADMIN_EMAIL:=admin@thor.local}"

get_client_uuid() {
  "$KCADM" get clients \
    -r "$KC_REALM" \
    -q clientId="$1" \
    --fields id \
    --format csv |
    head -n 1 |
    tr -d '"' |
    tr -d '\r'
}

get_user_uuid() {
  "$KCADM" get users \
    -r "$KC_REALM" \
    -q username="$1" \
    --fields id \
    --format csv |
    head -n 1 |
    tr -d '"' |
    tr -d '\r'
}

get_mapper_uuid() {
  "$KCADM" get "clients/$1/protocol-mappers/models" \
    -r "$KC_REALM" \
    --fields id,name \
    --format csv |
    awk -F, -v mapper_name="$2" '
      {
        gsub(/"/, "", $1)
        gsub(/"/, "", $2)
        gsub(/\r/, "", $1)
        gsub(/\r/, "", $2)
        if ($1 == "id" && $2 == "name") {
          next
        }
        if ($2 == mapper_name) {
          print $1
          exit
        }
      }
    '
}

echo "Aguardando Keycloak em ${KC_SERVER}..."
until "$KCADM" config credentials \
  --server "$KC_SERVER" \
  --realm master \
  --user "$KC_ADMIN_USER" \
  --password "$KC_ADMIN_PASSWORD" >/dev/null 2>&1; do
  sleep 2
done

if ! "$KCADM" get "realms/${KC_REALM}" >/dev/null 2>&1; then
  echo "Realm '${KC_REALM}' não encontrado. Criando..."
  "$KCADM" create realms \
    -s "realm=${KC_REALM}" \
    -s 'enabled=true' \
    -s 'registrationAllowed=false' \
    -s 'resetPasswordAllowed=true' \
    -s 'loginWithEmailAllowed=true'
else
  echo "Realm '${KC_REALM}' já existe."
fi

APP_ADMIN_UUID=$(get_user_uuid "$KC_APP_ADMIN_USER")

if [ -z "$APP_ADMIN_UUID" ]; then
  echo "Usuário '${KC_APP_ADMIN_USER}' não encontrado no realm '${KC_REALM}'. Criando..."
  "$KCADM" create users \
    -r "$KC_REALM" \
    -s "username=${KC_APP_ADMIN_USER}" \
    -s "email=${KC_APP_ADMIN_EMAIL}" \
    -s 'firstName=Admin' \
    -s 'lastName=Sistema' \
    -s 'enabled=true' \
    -s 'emailVerified=true' \
    -s 'requiredActions=[]'
  APP_ADMIN_UUID=$(get_user_uuid "$KC_APP_ADMIN_USER")
else
  echo "Usuário '${KC_APP_ADMIN_USER}' já existe no realm '${KC_REALM}'."
fi

if [ -z "$APP_ADMIN_UUID" ]; then
  echo "Não foi possível configurar o usuário '${KC_APP_ADMIN_USER}' no realm '${KC_REALM}'." >&2
  exit 1
fi

"$KCADM" update "users/${APP_ADMIN_UUID}" \
  -r "$KC_REALM" \
  -s "email=${KC_APP_ADMIN_EMAIL}" \
  -s 'firstName=Admin' \
  -s 'lastName=Sistema' \
  -s 'enabled=true' \
  -s 'emailVerified=true' \
  -s 'requiredActions=[]'

"$KCADM" set-password \
  -r "$KC_REALM" \
  --username "$KC_APP_ADMIN_USER" \
  --new-password "$KC_APP_ADMIN_PASSWORD" \
  --temporary=false

BACKEND_CLIENT_UUID=$(get_client_uuid "$KC_BACKEND_CLIENT_ID")

if [ -z "$BACKEND_CLIENT_UUID" ]; then
  echo "Client backend '${KC_BACKEND_CLIENT_ID}' não encontrado. Criando..."
  "$KCADM" create clients \
    -r "$KC_REALM" \
    -s "clientId=${KC_BACKEND_CLIENT_ID}" \
    -s 'enabled=true' \
    -s 'publicClient=false' \
    -s 'standardFlowEnabled=false' \
    -s 'directAccessGrantsEnabled=false' \
    -s 'serviceAccountsEnabled=false' \
    -s "rootUrl=${BACKEND_URL}" \
    -s 'redirectUris=[]' \
    -s 'webOrigins=[]'
  BACKEND_CLIENT_UUID=$(get_client_uuid "$KC_BACKEND_CLIENT_ID")
else
  echo "Client backend '${KC_BACKEND_CLIENT_ID}' já existe."
fi

if [ -z "$BACKEND_CLIENT_UUID" ]; then
  echo "Não foi possível configurar o client backend '${KC_BACKEND_CLIENT_ID}' no realm '${KC_REALM}'." >&2
  exit 1
fi

FRONTEND_CLIENT_UUID=$(get_client_uuid "$KC_FRONTEND_CLIENT_ID")

if [ -z "$FRONTEND_CLIENT_UUID" ]; then
  echo "Client frontend '${KC_FRONTEND_CLIENT_ID}' não encontrado. Criando..."
  "$KCADM" create clients \
    -r "$KC_REALM" \
    -s "clientId=${KC_FRONTEND_CLIENT_ID}" \
    -s 'enabled=true' \
    -s 'protocol=openid-connect' \
    -s 'publicClient=true' \
    -s 'standardFlowEnabled=true' \
    -s 'directAccessGrantsEnabled=true' \
    -s 'implicitFlowEnabled=false' \
    -s 'serviceAccountsEnabled=false'
  FRONTEND_CLIENT_UUID=$(get_client_uuid "$KC_FRONTEND_CLIENT_ID")
else
  echo "Client frontend '${KC_FRONTEND_CLIENT_ID}' já existe."
fi

if [ -z "$FRONTEND_CLIENT_UUID" ]; then
  echo "Não foi possível configurar o client frontend '${KC_FRONTEND_CLIENT_ID}' no realm '${KC_REALM}'." >&2
  exit 1
fi

echo "Configurando client frontend '${KC_FRONTEND_CLIENT_ID}' para '${FRONTEND_URL}'..."
"$KCADM" update "clients/${FRONTEND_CLIENT_UUID}" \
  -r "$KC_REALM" \
  -s 'enabled=true' \
  -s 'protocol=openid-connect' \
  -s 'publicClient=true' \
  -s 'standardFlowEnabled=true' \
  -s 'directAccessGrantsEnabled=true' \
  -s 'implicitFlowEnabled=false' \
  -s 'serviceAccountsEnabled=false' \
  -s "rootUrl=${FRONTEND_URL}" \
  -s "baseUrl=${FRONTEND_URL}" \
  -s "adminUrl=${FRONTEND_URL}" \
  -s "redirectUris=[\"${FRONTEND_URL}/auth/callback\",\"${FRONTEND_URL}/*\"]" \
  -s "webOrigins=[\"${FRONTEND_URL}\"]" \
  -s "attributes={\"post.logout.redirect.uris\":\"${FRONTEND_URL}/login##${FRONTEND_URL}/*\",\"pkce.code.challenge.method\":\"S256\"}"

if [ "$KC_FRONTEND_CLIENT_ID" != "$KC_BACKEND_CLIENT_ID" ]; then
  AUDIENCE_MAPPER_NAME="audience-${KC_BACKEND_CLIENT_ID}"
  MAPPER_UUID=$(get_mapper_uuid "$FRONTEND_CLIENT_UUID" "$AUDIENCE_MAPPER_NAME")

  if [ -z "$MAPPER_UUID" ]; then
    echo "Criando mapper de audience '${KC_BACKEND_CLIENT_ID}' no client frontend..."
    "$KCADM" create "clients/${FRONTEND_CLIENT_UUID}/protocol-mappers/models" \
      -r "$KC_REALM" \
      -s "name=${AUDIENCE_MAPPER_NAME}" \
      -s 'protocol=openid-connect' \
      -s 'protocolMapper=oidc-audience-mapper' \
      -s "config.\"included.client.audience\"=${KC_BACKEND_CLIENT_ID}" \
      -s 'config."access.token.claim"=true' \
      -s 'config."id.token.claim"=false'
  else
    echo "Mapper de audience '${KC_BACKEND_CLIENT_ID}' já existe no client frontend."
  fi
fi

echo "Keycloak configurado: realm='${KC_REALM}', backend='${KC_BACKEND_CLIENT_ID}', frontend='${KC_FRONTEND_CLIENT_ID}'."
