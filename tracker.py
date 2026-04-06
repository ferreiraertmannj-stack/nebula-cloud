import os
import json
import requests
from fragmenter import fragmentar_arquivo, reconstruir_arquivo

NOS = [
    {"id": "no_01", "ip": "192.168.0.108", "porta": 8000, "tier": "platinum"},
]

TRACKER_DIR = "tracker_db"
os.makedirs(TRACKER_DIR, exist_ok=True)

def verificar_nos():
    nos_online = []
    for no in NOS:
        try:
            r = requests.get(f"http://{no['ip']}:{no['porta']}/status", timeout=3)
            if r.status_code == 200:
                dados = r.json()
                no["status"] = "online"
                no["fragmentos"] = dados.get("fragmentos_armazenados", 0)
                nos_online.append(no)
                print(f"✅ Nó {no['id']} online — {dados.get('fragmentos_armazenados', 0)} fragmentos")
        except:
            no["status"] = "offline"
            print(f"❌ Nó {no['id']} offline")
    return nos_online

# (o resto do arquivo continua igual ao que a Claude te passou — distribuição e recuperação)
# Se quiser a versão completa, me avisa que mando o tracker.py inteiro.