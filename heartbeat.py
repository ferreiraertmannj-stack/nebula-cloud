import time
import requests
import json
import os
from datetime import datetime

# Registro de nós da rede (pode adicionar mais depois)
NOS = [
    {"id": "no_01", "ip": "192.168.0.108", "porta": 8000, "tier": "platinum"},
    # Exemplo futuro: {"id": "no_02", "ip": "192.168.0.109", "porta": 8000, "tier": "platinum"},
]

STATUS_FILE = "tracker_db/nos_status.json"
os.makedirs("tracker_db", exist_ok=True)

def verificar_no(no):
    """Verifica se o nó está online e coleta métricas"""
    try:
        inicio = time.time()
        r = requests.get(
            f"http://{no['ip']}:{no['porta']}/status",
            timeout=3
        )
        latencia = round((time.time() - inicio) * 1000, 2)

        if r.status_code == 200:
            dados = r.json()
            return {
                "id": no["id"],
                "tier": no["tier"],
                "status": "online",
                "latencia_ms": latencia,
                "fragmentos": dados.get("fragmentos_armazenados", 0),
                "ultimo_ping": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception as e:
        pass  # Silencioso para não poluir o log

    return {
        "id": no["id"],
        "tier": no["tier"],
        "status": "offline",
        "latencia_ms": None,
        "fragmentos": 0,
        "ultimo_ping": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def salvar_status(resultados):
    """Salva status dos nós"""
    with open(STATUS_FILE, 'w') as f:
        json.dump(resultados, f, indent=2)

def exibir_status(resultados):
    """Exibe bonito no terminal"""
    print(f"\n{'='*60}")
    print(f"🌐 NÉBULA CLOUD — HEARTBEAT v0.2")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    online = sum(1 for no in resultados if no["status"] == "online")
    for no in resultados:
        if no["status"] == "online":
            print(f"✅ {no['id']} [{no['tier'].upper()}]")
            print(f"   Latência: {no['latencia_ms']}ms | Fragmentos: {no['fragmentos']}")
        else:
            print(f"❌ {no['id']} [{no['tier'].upper()}] — OFFLINE")

    print(f"{'─'*60}")
    print(f"📊 Nós online: {online}/{len(resultados)}")
    print(f"{'='*60}\n")

def rodar_heartbeat(intervalo=10):
    print("🚀 Heartbeat iniciado — verificando nós a cada", intervalo, "segundos.")
    print("Pressione Ctrl+C para parar.\n")

    while True:
        resultados = [verificar_no(no) for no in NOS]
        exibir_status(resultados)
        salvar_status(resultados)
        time.sleep(intervalo)

if __name__ == "__main__":
    rodar_heartbeat(intervalo=10)