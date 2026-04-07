import os
import json
import requests

NOS = [
    {"id": "no_02_infinix", "ip": "192.168.0.102", "porta": 8000},
]

TRACKER_DIR = "tracker_db"
os.makedirs(TRACKER_DIR, exist_ok=True)

def verificar_nos():
    nos_online = []
    for no in NOS:
        try:
            r = requests.get(f"http://{no['ip']}:{no['porta']}/status", timeout=10)
            if r.status_code == 200:
                dados = r.json()
                print(f"✅ {no['id']} ONLINE → {dados.get('fragmentos_armazenados', 0)} fragmentos")
                nos_online.append(no)
            else:
                print(f"❌ {no['id']} respondeu {r.status_code}")
        except Exception as e:
            print(f"❌ {no['id']} offline - {str(e)[:100]}")
    return nos_online

def distribuir_arquivo(caminho: str, senha: str):
    nos_online = verificar_nos()
    if not nos_online:
        print("❌ Nenhum nó disponível!")
        return

    pasta_frags = f"{TRACKER_DIR}/temp_frags"
    os.makedirs(pasta_frags, exist_ok=True)

    from fragmenter import fragmentar_arquivo
    fragmentar_arquivo(caminho, senha, pasta_frags)

    with open(f"{pasta_frags}/meta.json") as f:
        meta = json.load(f)

    mapa = {}
    fragmentos = sorted([f for f in os.listdir(pasta_frags) if f.endswith('.bin')])

    for i, frag in enumerate(fragmentos):
        no = nos_online[0]
        caminho_frag = f"{pasta_frags}/{frag}"

        with open(caminho_frag, 'rb') as f:
            r = requests.post(
                f"http://{no['ip']}:{no['porta']}/fragmento/{frag}",
                files={"file": f}
            )
        if r.status_code == 200:
            mapa[frag] = {"no_id": no["id"]}
            print(f"📤 {frag} → {no['id']}")
        else:
            print(f"❌ Erro ao enviar {frag}")

    nome_arquivo = os.path.basename(caminho)
    registro = {"arquivo": nome_arquivo, "senha_hint": senha[:3]+"***", "meta": meta, "mapa": mapa}
    with open(f"{TRACKER_DIR}/{nome_arquivo}.map.json", 'w') as f:
        json.dump(registro, f, indent=2)

    print(f"\n✅ Sucesso! Arquivo '{nome_arquivo}' distribuído.")

def recuperar_arquivo(nome_arquivo: str, senha: str, saida: str):
    mapa_path = f"{TRACKER_DIR}/{nome_arquivo}.map.json"
    if not os.path.exists(mapa_path):
        print(f"❌ Mapa do arquivo não encontrado")
        return

    with open(mapa_path) as f:
        registro = json.load(f)

    pasta_rec = f"{TRACKER_DIR}/recuperando"
    os.makedirs(pasta_rec, exist_ok=True)

    print("🔄 Recuperando fragmentos do Infinix...")
    for frag in registro["mapa"]:
        try:
            r = requests.get(f"http://192.168.0.102:8000/fragmento/{frag}")
            if r.status_code == 200:
                with open(f"{pasta_rec}/{frag}", 'wb') as f:
                    f.write(r.content)
                print(f"✅ {frag} recuperado")
            else:
                print(f"❌ Falha ao recuperar {frag}")
        except Exception as e:
            print(f"❌ Erro ao recuperar {frag}: {e}")

    from fragmenter import reconstruir_arquivo
    try:
        reconstruir_arquivo(pasta_rec, senha, saida)
        print(f"\n✅ Arquivo recuperado com sucesso: {saida}")
    except Exception as e:
        print(f"❌ Erro na reconstrução: {e}")

if __name__ == "__main__":
    print("\n🚀 NÉBULA CLOUD TRACKER SIMPLE - Versão Completa")
    print("1 - Distribuir arquivo (enviar)")
    print("2 - Recuperar arquivo")
    print("3 - Ver nós online")
    op = input("\nEscolha: ")

    if op == "1":
        caminho = input("Caminho do arquivo: ")
        senha = input("Senha de criptografia: ")
        distribuir_arquivo(caminho, senha)
    elif op == "2":
        nome = input("Nome do arquivo original (ex: teste.txt): ")
        senha = input("Senha de criptografia: ")
        saida = input("Nome do arquivo recuperado (ex: recuperado.txt): ")
        recuperar_arquivo(nome, senha, saida)
    elif op == "3":
        verificar_nos()
