from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import PlatformUsers
from api_client import APIData
from dotenv import load_dotenv
import os
import pandas as pd
from parse import normalize_data

load_dotenv()
app = FastAPI()

# Configurar CORS
origins = [
    "http://127.0.0.1:5500",  # URL do frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Permitir apenas as origens especificadas
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos os cabeçalhos
)
# Endpoint de teste
@app.get("/")
async def root():
    return {"message": "active API"}

@app.post("/update")
async def fetch_data(platform_users: PlatformUsers):
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Token não configurado.")

    platforms_config = {
        "instagram": {
            "users": platform_users.instagram,
            "endpoint": "https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_l1vikfch901nx3by4&include_errors=true",
            "url_builder": lambda user: f"https://www.instagram.com/{user}/",
            "rename_columns": {
                "account": "account",
                "profile_name": "name",
                "followers": "followers_subscribers",
            },
        },
        "linkedin": {
            "users": platform_users.linkedin,
            "endpoint": "https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_l1vikfnt1wgvvqz95w&include_errors=true",
            "url_builder": lambda user: f"https://www.linkedin.com/company/{user}/",
            "rename_columns": {
                "id": "account",
                "name": "name",
                "followers": "followers_subscribers",
            },
        },
        "youtube": {
            "users": platform_users.youtube,
            "endpoint": "https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_lk538t2k2p1k3oos71&include_errors=true",
            "url_builder": lambda user: f"https://www.youtube.com/@{user}/about",
            "rename_columns": {
                "handle": "account",
                "name": "name",
                "subscribers": "followers_subscribers",
            },
        },
        "tiktok": {
            "users": platform_users.tiktok,
            "endpoint": "https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_l1villgoiiidt09ci&include_errors=true",
            "url_builder": lambda user: f"https://www.tiktok.com/@{user}",
            "rename_columns": {
                "handle": "account",
                "name": "name",
                "followers": "followers_subscribers",
            },
        },
    }

    api_data = APIData(token, platforms_config)
    api_data.generate_snapshots()

    final_data = []
    for platform_name, config in platforms_config.items():
        if platform_name in api_data.snapshots:
            try:
                # Obtém os dados do snapshot
                raw_data = api_data.get_snapshot_data(
                    api_data.snapshots[platform_name],
                    headers={"Authorization": f"Bearer {token}"}
                )
                # Normaliza os dados usando as configurações da plataforma
                normalized_data = normalize_data(
                    raw_data,
                    platform_name,
                    config["rename_columns"]
                )
                final_data.append(normalized_data)
            except Exception as e:
                print(f"Erro ao processar dados de {platform_name}: {e}")

    if final_data:
        # Concatena os DataFrames normalizados
        final_data = pd.concat(final_data, ignore_index=True)
        # Substitui valores inválidos antes de retornar o JSON
        final_data = final_data.replace([float('inf'), -float('inf')], 0)  # Substitui infinitos por 0
        final_data = final_data.fillna(0)  # Substitui NaN por 0
        return final_data.to_dict(orient="records")
    else:
        return {"message": "Nenhum dado retornado."}
