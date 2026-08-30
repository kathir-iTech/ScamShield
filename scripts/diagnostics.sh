#!/usr/bin/env bash
set -euo pipefail

echo "╔═══════════════════════════════════════════════╗"
echo "║         Kaaval — System Diagnostics           ║"
echo "╚═══════════════════════════════════════════════╝"

BASE_URL="${1:-http://localhost:8000}"

echo ""
echo "━━━ Timestamp ━━━"
echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

echo ""
echo "━━━ System Info ━━━"
if [[ "$(uname -s)" == "Linux" ]]; then
  echo "OS: $(uname -s) $(uname -r)"
  echo "CPU: $(nproc) cores"
  total_mem=$(free -m | awk '/Mem:/ {print $2}')
  free_mem=$(free -m | awk '/Mem:/ {print $7}')
  echo "Memory: ${free_mem}MB free / ${total_mem}MB total"
  echo "Disk: $(df -h / | awk 'NR==2 {print $4 " free / " $2 " total"}')"
  echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
elif [[ "$(uname -s)" == "Darwin" ]]; then
  echo "OS: $(sw_vers -productName) $(sw_vers -productVersion)"
  echo "CPU: $(sysctl -n hw.ncpu) cores"
  echo "Memory: $(vm_stat | awk '/free/ {free=$3} /active/ {active=$3} END {printf "%.0fMB free", free/256}')"
  echo "Disk: $(df -h / | awk 'NR==2 {print $4 " free / " $2 " total"}')"
else
  echo "OS: $(uname -s)"
  echo "CPU info unavailable"
fi

echo ""
echo "━━━ Docker Status ━━━"
if command -v docker &>/dev/null; then
  echo "Docker: available"
  docker info --format 'Server Version: {{.ServerVersion}}' 2>/dev/null || echo "Docker daemon: not accessible"
  echo ""
  docker compose ps 2>/dev/null || docker ps --filter "name=kaaval" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No kaaval containers found"
else
  echo "Docker: not available"
fi

echo ""
echo "━━━ Backend Diagnostics ━━━"
if health=$(curl -sf "$BASE_URL/health" 2>/dev/null); then
  echo "Health: OK"
  echo "$health" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"  Status: {data.get('status')}\")
print(f\"  Version: {data.get('build_version', data.get('version'))}\")
print(f\"  Uptime: {data.get('uptime_seconds', 0)}s\")
print(f\"  Model: {data.get('model_loaded')}\")
print(f\"  Active requests: {data.get('active_requests')}\")
print(f\"  Disk: {data.get('disk_usage')}\")
print(f\"  Memory: {data.get('memory_usage')}\")
print(f\"  Dependencies: {data.get('dependency_status')}\")
" 2>/dev/null || echo "$health" | python -m json.tool
else
  echo "FAIL: Cannot reach $BASE_URL/health"
fi

echo ""
echo "━━━ Recent Log Errors ━━━"
if command -v docker &>/dev/null; then
  docker compose logs --tail=100 backend 2>/dev/null | grep -i -E "(error|critical|exception|traceback)" | tail -20 || echo "No recent errors found"
else
  echo "Docker not available — check logs manually"
fi

echo ""
echo "━━━ Endpoint Check ━━━"
for endpoint in /health /ready /live /metrics /docs /openapi.json; do
  status=$(curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" 2>/dev/null || echo "FAIL")
  echo "  $endpoint: $status"
done

echo ""
echo "━━━ Diagnostics Complete ━━━"
