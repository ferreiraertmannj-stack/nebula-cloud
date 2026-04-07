import os
import json
from reedsolo import RSCodec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

K = 10  # dados
M = 4   # paridade → overhead 1.4x
rsc = RSCodec(M)

# Salt fixo para derivação de chave consistente
SALT = b'nebula-cloud-2026'

def derivar_chave(senha: str) -> bytes:
    """Deriva uma chave de 256 bits (32 bytes) a partir da senha"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    return kdf.derive(senha.encode())

def criptografar(dados: bytes, senha: str) -> tuple[bytes, bytes]:
    """Criptografa dados com AES-256-GCM"""
    chave = derivar_chave(senha)
    nonce = os.urandom(12)
    aesgcm = AESGCM(chave)
    dados_criptografados = aesgcm.encrypt(nonce, dados, None)
    return dados_criptografados, nonce

def descriptografar(dados_enc: bytes, nonce: bytes, senha: str) -> bytes:
    """Descriptografa dados com AES-256-GCM"""
    chave = derivar_chave(senha)
    aesgcm = AESGCM(chave)
    return aesgcm.decrypt(nonce, dados_enc, None)

def fragmentar_arquivo(caminho: str, senha: str, pasta_saida: str):
    """Fragmenta arquivo em K+M pedaços com Reed-Solomon e criptografia AES-256"""
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    
    os.makedirs(pasta_saida, exist_ok=True)
    
    # Ler arquivo
    with open(caminho, 'rb') as f:
        dados = f.read()

    # Criptografar
    dados_enc, nonce = criptografar(dados, senha)
    
    tamanho_original = len(dados)
    tamanho_criptografado = len(dados_enc)

    # Calcular tamanho de cada fragmento
    # Todos os K fragmentos devem ter o mesmo tamanho
    tam_frag = (tamanho_criptografado + K - 1) // K
    
    # Fazer padding para que o tamanho total seja divisível por K
    tamanho_total_padded = tam_frag * K
    dados_enc_padded = dados_enc + b'\x00' * (tamanho_total_padded - tamanho_criptografado)

    # Dividir em K fragmentos
    fragmentos = [dados_enc_padded[i*tam_frag:(i+1)*tam_frag] for i in range(K)]

    # Aplicar Reed-Solomon para adicionar redundância
    fragmentos_rs = [bytes(rsc.encode(frag)) for frag in fragmentos]

    # Salvar fragmentos
    for i, frag in enumerate(fragmentos_rs):
        with open(f"{pasta_saida}/frag_{i:02d}.bin", 'wb') as f:
            f.write(frag)

    # Salvar metadados
    meta = {
        "arquivo_original": os.path.basename(caminho),
        "tamanho_original": tamanho_original,
        "tamanho_criptografado": tamanho_criptografado,
        "total_fragmentos": K + M,
        "fragmentos_dados": K,
        "fragmentos_paridade": M,
        "nonce": nonce.hex(),
        "tam_fragmento": tam_frag
    }
    with open(f"{pasta_saida}/meta.json", 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"✅ Arquivo fragmentado em {K+M} pedaços — overhead 1.4x")
    print(f"📁 Salvos em: {pasta_saida}")

def reconstruir_arquivo(pasta: str, senha: str, saida: str):
    """Reconstrói arquivo a partir de fragmentos Reed-Solomon"""
    meta_path = f"{pasta}/meta.json"
    
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Metadados não encontrados em: {meta_path}")
    
    with open(meta_path) as f:
        meta = json.load(f)

    # Carregar fragmentos de dados
    fragmentos_rs = []
    for i in range(meta['fragmentos_dados']):
        frag_path = f"{pasta}/frag_{i:02d}.bin"
        if not os.path.exists(frag_path):
            raise FileNotFoundError(f"Fragmento não encontrado: {frag_path}")
        with open(frag_path, 'rb') as f:
            fragmentos_rs.append(bytearray(f.read()))

    # Decodificar Reed-Solomon
    try:
        fragmentos_dec = [bytes(rsc.decode(frag)[0]) for frag in fragmentos_rs]
    except Exception as e:
        raise ValueError(f"Erro ao decodificar fragmentos Reed-Solomon: {e}")
    
    # Reconstruir dados criptografados
    dados_enc = b''.join(fragmentos_dec)[:meta['tamanho_criptografado']]

    # Descriptografar
    nonce = bytes.fromhex(meta['nonce'])
    try:
        dados = descriptografar(dados_enc, nonce, senha)
    except Exception as e:
        raise ValueError(f"Erro ao descriptografar: {e}. Verifique a senha.")

    # Remover padding de tamanho original
    dados = dados[:meta['tamanho_original']]

    # Salvar arquivo reconstruído
    with open(saida, 'wb') as f:
        f.write(dados)

    print(f"✅ Arquivo reconstruído com sucesso: {saida}")

if __name__ == "__main__":
    # Teste rápido
    with open("teste.txt", 'w') as f:
        f.write("Nébula Cloud — Primeiro fragmento real! " * 50)
    fragmentar_arquivo("teste.txt", "senha-nebula-2026", "fragmentos")
    reconstruir_arquivo("fragmentos", "senha-nebula-2026", "reconstruido.txt")
