import os
import json
from reedsolo import RSCodec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

K = 10  # dados
M = 4   # paridade → overhead 1.4x
rsc = RSCodec(M)

def criptografar(dados: bytes, senha: str) -> tuple[bytes, bytes]:
    chave = senha.encode().ljust(32)[:32]
    nonce = os.urandom(12)
    aesgcm = AESGCM(chave)
    return aesgcm.encrypt(nonce, dados, None), nonce

def descriptografar(dados_enc: bytes, nonce: bytes, senha: str) -> bytes:
    chave = senha.encode().ljust(32)[:32]
    aesgcm = AESGCM(chave)
    return aesgcm.decrypt(nonce, dados_enc, None)

def fragmentar_arquivo(caminho: str, senha: str, pasta_saida: str):
    os.makedirs(pasta_saida, exist_ok=True)
    with open(caminho, 'rb') as f:
        dados = f.read()

    dados_enc, nonce = criptografar(dados, senha)

    # Padding
    resto = len(dados_enc) % K
    if resto != 0:
        dados_enc += b'\x00' * (K - resto)

    tam_frag = len(dados_enc) // K
    fragmentos = [dados_enc[i*tam_frag:(i+1)*tam_frag] for i in range(K)]

    fragmentos_rs = [bytes(rsc.encode(frag)) for frag in fragmentos]

    for i, frag in enumerate(fragmentos_rs):
        with open(f"{pasta_saida}/frag_{i:02d}.bin", 'wb') as f:
            f.write(frag)

    meta = {
        "arquivo_original": os.path.basename(caminho),
        "tamanho_original": len(dados),
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
    with open(f"{pasta}/meta.json") as f:
        meta = json.load(f)

    fragmentos_rs = []
    for i in range(meta['fragmentos_dados']):
        with open(f"{pasta}/frag_{i:02d}.bin", 'rb') as f:
            fragmentos_rs.append(bytearray(f.read()))

    fragmentos_dec = [bytes(rsc.decode(frag)[0]) for frag in fragmentos_rs]
    dados_enc = b''.join(fragmentos_dec)[:meta['tamanho_original']]

    nonce = bytes.fromhex(meta['nonce'])
    dados = descriptografar(dados_enc, nonce, senha)

    with open(saida, 'wb') as f:
        f.write(dados)

    print(f"✅ Arquivo reconstruído: {saida}")

if __name__ == "__main__":
    # Teste rápido
    with open("teste.txt", 'w') as f:
        f.write("Nébula Cloud — Primeiro fragmento real! " * 50)
    fragmentar_arquivo("teste.txt", "senha-nebula-2026", "fragmentos")
    reconstruir_arquivo("fragmentos", "senha-nebula-2026", "reconstruido.txt")