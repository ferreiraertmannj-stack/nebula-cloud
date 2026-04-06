import os
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse

app = FastAPI(title="Nébula Node Daemon")

STORAGE_DIR = "node_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.get("/status")
def status():
    fragmentos = os.listdir(STORAGE_DIR)
    return {
        "status": "online",
        "node": "notebook-jean",
        "fragmentos_armazenados": len(fragmentos),
        "arquivos": fragmentos
    }

@app.post("/fragmento/{nome}")
async def receber_fragmento(nome: str, file: UploadFile = File(...)):
    caminho = f"{STORAGE_DIR}/{nome}"
    with open(caminho, 'wb') as f:
        f.write(await file.read())
    print(f"✅ Fragmento recebido: {nome}")
    return {"status": "salvo", "fragmento": nome}

@app.get("/fragmento/{nome}")
def enviar_fragmento(nome: str):
    caminho = f"{STORAGE_DIR}/{nome}"
    if os.path.exists(caminho):
        return FileResponse(caminho)
    return {"erro": "fragmento não encontrado"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)