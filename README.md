# 🌐 Nébula Cloud - MVP

**Armazenamento Descentralizado Brasileiro**  
Ertmann Tech • Extrema/MG • Abril 2026

**Status atual:** MVP funcional (fragmentação + distribuição + recuperação + heartbeat)

### Tecnologias
- AES-256 + Reed-Solomon 10+4 (overhead 1.4x)
- FastAPI + Uvicorn
- Zero-Knowledge

### Como rodar (3 terminais)

```bash
source nebula-env/bin/activate

# Terminal 1 - Node Daemon
python3 node_daemon.py

# Terminal 2 - Tracker
python3 tracker.py

# Terminal 3 - Heartbeat
python3 heartbeat.py