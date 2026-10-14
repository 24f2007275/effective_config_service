import os
from pathlib import Path
from typing import Any
import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent
DEFAULTS = {"port": 8000, "workers": 1, "debug": False, "log_level": "info", "api_key": "default-secret-000"}
ALIASES = {"num_workers": "workers"}
INT_KEYS = {"port", "workers"}

def norm(k):
    k = k.strip().lower()
    if k.startswith("app_"):
        k = k[4:]
    return ALIASES.get(k, k)

def coerce(k, v):
    if k in INT_KEYS:
        return int(v)
    if k == "debug":
        return v if isinstance(v, bool) else str(v).strip().lower() in {"true", "1", "yes", "on"}
    return str(v)

def load_config():
    cfg = dict(DEFAULTS)
    yp = ROOT / "config.development.yaml"
    if yp.exists():
        with yp.open(encoding="utf-8") as f:
            for k, v in (yaml.safe_load(f) or {}).items():
                k = norm(str(k))
                if k in cfg: cfg[k] = coerce(k, v)
    for k, v in dotenv_values(ROOT / ".env").items():
        if v is not None:
            k = norm(k)
            if k in cfg: cfg[k] = coerce(k, v)
    for k, v in os.environ.items():
        if k.upper().startswith("APP_"):
            k = norm(k)
            if k in cfg: cfg[k] = coerce(k, v)
    return cfg

app = FastAPI(title="Effective Config Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/effective-config")
async def effective_config(request: Request):
    cfg = load_config()
    for item in request.query_params.getlist("set"):
        if "=" not in item: continue
        raw_key, raw_value = item.split("=", 1)
        key = norm(raw_key)
        if key in cfg: cfg[key] = coerce(key, raw_value)
    cfg["api_key"] = "****"
    return cfg
