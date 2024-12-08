from fastapi import FastAPI, HTTPException
from schemas import PlatformUsers
from api_client import APIData
from parse import normalize_data, merge_platforms
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

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

    headers = {"Authorization": f"Bearer {token}"}
    dataframes = {}

    for platform, config in platforms_config.items():
        if platform in api_data.snapshots:
            snapshot_id = api_data.snapshots[platform]
            raw_data = api_data.get_snapshot_data(snapshot_id, headers)
            normalized_data = normalize_data(raw_data, platform, config["rename_columns"])
            dataframes[platform] = normalized_data

    final_data = merge_platforms(dataframes)

    # **Tratamento de valores inválidos no DataFrame**
    if final_data.empty:
        return {"message": "Nenhum dado retornado."}
    
    # Substituindo valores inválidos por strings aceitáveis
    final_data = final_data.fillna("N/A")  # Substitui NaN por 'N/A'
    final_data.replace([float("inf"), -float("inf")], 0, inplace=True)  # Substitui infinitos por 0

    return final_data.to_dict(orient="records")
