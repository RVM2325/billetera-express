#!/usr/bin/env bash
# Script para iniciar Billetera Express y generar un enlace público gratuito con Cloudflare

PUERTO=8000
CLOUDFLARED="/home/rvm/.local/bin/cloudflared"

echo "============================================================"
echo "🇵🇪 Iniciando Billetera Express con Enlace Público Gratuito"
echo "============================================================"

# Matar procesos previos si existen
pkill -f "python3.*main.py" 2>/dev/null
pkill -f "cloudflared.*tunnel" 2>/dev/null
sleep 1

# Iniciar servidor local Python en segundo plano
cd /home/rvm/GestorFinanzas || exit
python3 main.py > /tmp/billetera_server.log 2>&1 &
SERVER_PID=$!

echo "⏳ Conectando túnel seguro de Cloudflare..."
sleep 2

# Iniciar túnel de Cloudflare y capturar la URL
$CLOUDFLARED tunnel --url "http://127.0.0.1:$PUERTO" > /tmp/cloudflare_tunnel.log 2>&1 &
TUNNEL_PID=$!

# Esperar a que se genere el link
for i in {1..20}; do
    URL=$(grep -o 'https://[a-zA-Z0-9.-]*\.trycloudflare\.com' /tmp/cloudflare_tunnel.log | head -n 1)
    if [ -n "$URL" ]; then
        break
    fi
    sleep 1
done

if [ -n "$URL" ]; then
    echo ""
    echo "============================================================"
    echo "🎉 ¡LISTO! Tu aplicación ya está en internet y es 100% GRATIS:"
    echo ""
    echo "👉 $URL"
    echo ""
    echo "📱 Pásale este enlace a tu familia por WhatsApp."
    echo "   Podrán entrar desde cualquier celular o laptop con internet."
    echo "============================================================"
    echo "Presiona Ctrl + C en cualquier momento para detener el servicio."
    echo ""
else
    echo "⚠️ No se pudo obtener el enlace de Cloudflare. Revisa /tmp/cloudflare_tunnel.log"
fi

# Mantener activo y limpiar al salir
trap 'echo ""; echo "🛑 Deteniendo servicios..."; kill $SERVER_PID $TUNNEL_PID 2>/dev/null; exit 0' SIGINT SIGTERM
wait
