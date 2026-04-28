#!/usr/bin/env bash
# Deploy Tools Library en el VPS.
# Ejecutar UNA VEZ como usuario debian en ~/tools/:
#   cd ~/tools && bash deploy.sh
#
# Prerequisitos en el VPS:
#   sudo apt-get install -y python3-pip
#   pip install gdown

set -euo pipefail

DRIVE_FOLDER_ID="1Lm_fx1LgVgjNRYAho-hv0ScfCcFELEvk"
NPM_URL="http://localhost:81"

# ── Colores ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✔ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠ $*${NC}"; }
die()  { echo -e "${RED}✘ $*${NC}"; exit 1; }

# ── 1. Descargar archivos desde Google Drive ─────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════"
echo " [1/4] Descargando archivos desde Google Drive "
echo "═══════════════════════════════════════════════"

pip install -q gdown 2>/dev/null || warn "pip install gdown falló, asegúrate de que pip esté disponible"

mkdir -p html
TMP_DOWNLOAD=$(mktemp -d)

gdown --folder "https://drive.google.com/drive/folders/${DRIVE_FOLDER_ID}" \
      -O "${TMP_DOWNLOAD}/" 2>&1 || die "Error descargando desde Google Drive. ¿La carpeta es pública?"

# Mover archivos descargados a ./html/
INNER=$(ls -d "${TMP_DOWNLOAD}/*/" 2>/dev/null | head -1 || echo "${TMP_DOWNLOAD}")
rsync -a "${INNER}/" ./html/ 2>/dev/null || cp -r "${INNER}/." ./html/
rm -rf "${TMP_DOWNLOAD}"
ok "Archivos copiados a ~/tools/html/"

# ── 2. Levantar contenedor Docker ─────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════"
echo " [2/4] Levantando contenedor Docker            "
echo "═══════════════════════════════════════════════"

sudo docker compose pull nginx 2>/dev/null || true
sudo docker compose up -d
ok "Contenedor tools-library levantado en puerto 4001"

# Verificar que responde
sleep 2
curl -sf http://localhost:4001 > /dev/null && ok "nginx responde en :4001" || warn "nginx aún no responde, revisa: sudo docker logs tools-library"

# ── 3. Configurar NPM via API ─────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════"
echo " [3/4] Configurando Nginx Proxy Manager        "
echo "═══════════════════════════════════════════════"

if [[ -z "${NPM_EMAIL:-}" ]] || [[ -z "${NPM_PASSWORD:-}" ]]; then
  echo ""
  warn "Necesito las credenciales de NPM para configurar el proxy automáticamente."
  read -rp "  Email NPM [admin@cesarheredero.com]: " NPM_EMAIL
  NPM_EMAIL="${NPM_EMAIL:-admin@cesarheredero.com}"
  read -rsp "  Password NPM: " NPM_PASSWORD
  echo ""
fi

# Obtener token
TOKEN=$(curl -sf -X POST "${NPM_URL}/api/tokens" \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"${NPM_EMAIL}\",\"secret\":\"${NPM_PASSWORD}\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null) \
  || die "No se pudo obtener token de NPM. Verifica email/password."

ok "Token NPM obtenido"

# Comprobar si ya existe el proxy host
EXISTING=$(curl -sf "${NPM_URL}/api/proxy-hosts" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c "
import sys, json
hosts = json.load(sys.stdin)
for h in hosts:
    if 'tools.cesarheredero.com' in h.get('domain_names', []):
        print(h['id'])
        break
" 2>/dev/null || echo "")

if [[ -n "${EXISTING}" ]]; then
  warn "El proxy host tools.cesarheredero.com ya existe (ID: ${EXISTING}). Saltando creación."
else
  # Crear proxy host con SSL Let's Encrypt
  RESULT=$(curl -sf -X POST "${NPM_URL}/api/proxy-hosts" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "domain_names": ["tools.cesarheredero.com"],
      "forward_scheme": "http",
      "forward_host": "127.0.0.1",
      "forward_port": 4001,
      "access_list_id": 0,
      "certificate_id": "new",
      "ssl_forced": true,
      "http2_support": true,
      "block_exploits": true,
      "allow_websocket_upgrade": false,
      "caching_enabled": false,
      "advanced_config": "",
      "meta": {
        "letsencrypt_agree": true,
        "dns_challenge": false,
        "letsencrypt_email": "cesar@cesarheredero.com"
      }
    }') || die "Error creando proxy host en NPM."

  HOST_ID=$(echo "${RESULT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
  ok "Proxy host creado (ID: ${HOST_ID}) → tools.cesarheredero.com → :4001 con SSL"
fi

# ── 4. Resumen ────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════"
echo " [4/4] Deploy completado                       "
echo "═══════════════════════════════════════════════"
echo ""
ok "https://tools.cesarheredero.com está listo"
echo ""
echo "  Comandos útiles:"
echo "    sudo docker ps --filter name=tools-library"
echo "    sudo docker logs -f tools-library"
echo "    sudo docker compose -f ~/tools/docker-compose.yml restart"
echo ""
