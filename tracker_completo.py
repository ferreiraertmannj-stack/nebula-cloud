#!/usr/bin/env python3
"""
Nébula Cloud - Tracker Completo v1.0
Gerencia distribuição, recuperação e monitoramento de fragmentos
"""
import json
import os
import requests
from pqc_fragmenter import PQCFragmenter as Fragmenter; from pqc_fragmenter import PQCFragmenter as Fragmenter; from fragmenter_simple import fragmentar_arquivo, recuperar_arquivo
from datetime import datetime

NODES_FILE = "nodes.json"
METADATA_FILE = "files_metadata.json"

def carregar_nodes():
    """Carrega lista de nós"""
    if os.path.exists(NODES_FILE):
        with open(NODES_FILE, 'r') as f:
            return json.load(f)
    return {}

def carregar_metadata():
    """Carrega metadados de arquivos"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def salvar_metadata(metadata):
    """Salva metadados de arquivos"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def listar_nodes():
    """Lista nós online"""
    nodes = carregar_nodes()
    if not nodes:
        print("❌ Nenhum nó registrado!")
        return
    
    print("\n📍 Nós Online:")
    for node_id, info in nodes.items():
        try:
            resp = requests.get(f"http://{info['ip']}:{info['port']}/health", timeout=2 )
            status = "✅ Online" if resp.status_code == 200 else "❌ Offline"
        except:
            status = "❌ Offline"
        print(f"  {status} {node_id}: {info['ip']}:{info['port']}")

def distribuir_arquivo():
    """Distribui arquivo entre nós"""
    filepath = input("Caminho do arquivo: ").strip()
    if not os.path.exists(filepath):
        print(f"❌ Arquivo não encontrado: {filepath}")
        return
    
    password = input("Senha de criptografia: ").strip()
    
    nodes = carregar_nodes()
    if not nodes:
        print("❌ Nenhum nó disponível!")
        return
    
    # Fragmentar arquivo
    print(f"\n🔐 Fragmentando {filepath}...")
    fragments = fragmentar_arquivo(filepath, password)
    print(f"✅ {len(fragments)} fragmentos criados")
    
    # Distribuir entre nós
    node_list = list(nodes.items())
    distribution = {}
    success_count = 0
    
    for i, (frag_id, frag_data) in enumerate(fragments.items()):
        node_id, node_info = node_list[i % len(node_list)]
        url = f"http://{node_info['ip']}:{node_info['port']}/store"
        
        try:
            resp = requests.post(url, json={
                'fragment_id': frag_id,
                'content': frag_data
            }, timeout=5 )
            if resp.status_code == 200:
                print(f"  ✅ {frag_id} → {node_id}")
                distribution[frag_id] = node_id
                success_count += 1
            else:
                print(f"  ❌ {frag_id} → {node_id} (erro {resp.status_code})")
        except Exception as e:
            print(f"  ❌ {frag_id} → {node_id} (erro: {e})")
    
    # Salvar metadados
    if success_count > 0:
        metadata = carregar_metadata()
        file_id = os.path.basename(filepath).replace('.', '_')
        metadata[file_id] = {
            'original_path': filepath,
            'password': password,
            'fragments': distribution,
            'total_fragments': len(fragments),
            'success_fragments': success_count,
            'timestamp': datetime.now().isoformat()
        }
        salvar_metadata(metadata)
        print(f"\n✅ Arquivo distribuído com sucesso! ({success_count}/{len(fragments)} fragmentos)")
    else:
        print(f"\n❌ Falha ao distribuir arquivo!")

def recuperar_arquivo_menu():
    """Recupera arquivo a partir de fragmentos"""
    metadata = carregar_metadata()
    
    if not metadata:
        print("❌ Nenhum arquivo armazenado!")
        return
    
    print("\n📂 Arquivos Armazenados:")
    files_list = list(metadata.items())
    for i, (file_id, info) in enumerate(files_list, 1):
        print(f"  {i}. {file_id} ({info['success_fragments']}/{info['total_fragments']} fragmentos)")
    
    try:
        choice = int(input("\nEscolha um arquivo: ")) - 1
        if choice < 0 or choice >= len(files_list):
            print("❌ Opção inválida!")
            return
    except:
        print("❌ Entrada inválida!")
        return
    
    file_id, info = files_list[choice]
    output_path = input("Caminho de saída: ").strip()
    
    nodes = carregar_nodes()
    fragments = {}
    
    print(f"\n📥 Recuperando fragmentos...")
    for frag_id, node_id in info['fragments'].items():
        if node_id not in nodes:
            print(f"  ❌ {frag_id} - Nó {node_id} não encontrado")
            continue
        
        node_info = nodes[node_id]
        url = f"http://{node_info['ip']}:{node_info['port']}/retrieve/{frag_id}"
        
        try:
            resp = requests.get(url, timeout=5 )
            if resp.status_code == 200:
                data = resp.json()
                fragments[frag_id] = data['content']
                print(f"  ✅ {frag_id} ← {node_id}")
            else:
                print(f"  ❌ {frag_id} - Erro {resp.status_code}")
        except Exception as e:
            print(f"  ❌ {frag_id} - Erro: {e}")
    
    if len(fragments) == info['total_fragments']:
        try:
            recuperar_arquivo(fragments, info['password'], output_path)
            print(f"\n✅ Arquivo recuperado em: {output_path}")
        except Exception as e:
            print(f"\n❌ Erro ao recuperar arquivo: {e}")
    else:
        print(f"\n❌ Não foi possível recuperar todos os fragmentos ({len(fragments)}/{info['total_fragments']})")

def listar_arquivos():
    """Lista arquivos armazenados"""
    metadata = carregar_metadata()
    
    if not metadata:
        print("❌ Nenhum arquivo armazenado!")
        return
    
    print("\n📂 Arquivos Armazenados:")
    print(f"{'ID':<20} {'Fragmentos':<15} {'Data':<20}")
    print("-" * 55)
    
    for file_id, info in metadata.items():
        frag_status = f"{info['success_fragments']}/{info['total_fragments']}"
        timestamp = info['timestamp'][:10]
        print(f"{file_id:<20} {frag_status:<15} {timestamp:<20}")

def gerenciar_nodes():
    """Menu para gerenciar nós"""
    while True:
        print("\n⚙️  GERENCIAR NÓS")
        print("1 - Adicionar nó")
        print("2 - Remover nó")
        print("3 - Listar nós")
        print("4 - Voltar")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            node_id = input("ID do nó: ").strip()
            node_ip = input("IP do nó: ").strip()
            node_port = input("Porta (padrão 5000): ").strip() or "5000"
            
            nodes = carregar_nodes()
            nodes[node_id] = {
                'ip': node_ip,
                'port': int(node_port),
                'status': 'online'
            }
            
            with open(NODES_FILE, 'w') as f:
                json.dump(nodes, f, indent=2)
            print(f"✅ Nó {node_id} adicionado!")
        
        elif opcao == "2":
            node_id = input("ID do nó a remover: ").strip()
            nodes = carregar_nodes()
            if node_id in nodes:
                del nodes[node_id]
                with open(NODES_FILE, 'w') as f:
                    json.dump(nodes, f, indent=2)
                print(f"✅ Nó {node_id} removido!")
            else:
                print("❌ Nó não encontrado!")
        
        elif opcao == "3":
            listar_nodes()
        
        elif opcao == "4":
            break

def menu():
    """Menu principal"""
    while True:
        print("\n" + "="*50)
        print("🚀 NÉBULA CLOUD TRACKER v1.0")
        print("="*50)
        print("1 - Distribuir arquivo")
        print("2 - Recuperar arquivo")
        print("3 - Listar arquivos armazenados")
        print("4 - Ver nós online")
        print("5 - Gerenciar nós")
        print("6 - Sair")
        print("="*50)
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            distribuir_arquivo()
        elif opcao == "2":
            recuperar_arquivo_menu()
        elif opcao == "3":
            listar_arquivos()
        elif opcao == "4":
            listar_nodes()
        elif opcao == "5":
            gerenciar_nodes()
        elif opcao == "6":
            print("\n👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == '__main__':
    menu()
