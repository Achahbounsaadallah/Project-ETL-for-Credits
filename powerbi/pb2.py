import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# 1. Chargement des variables d'environnement (.env local ou Docker Airflow)
env_path_docker = Path("/opt/airflow/.env")
env_path_local = Path(__file__).resolve().parents[1] / ".env"

if env_path_docker.exists():
    load_dotenv(env_path_docker)
else:
    load_dotenv(env_path_local)


def get_access_token() -> str:
    """Récupère le jeton OAuth 2.0 via le Service Principal Azure AD."""
    tenant_id = os.environ["POWERBI_TENANT_ID"]
    client_id = os.environ["POWERBI_CLIENT_ID"]
    client_secret = os.environ["POWERBI_CLIENT_SECRET"]

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://analysis.windows.net/powerbi/api/.default",
    }

    token_response = requests.post(token_url, data=token_data, timeout=30)
    token_response.raise_for_status()

    return token_response.json()["access_token"]


def poll_refresh_status(workspace_id: str, dataset_id: str, access_token: str, poll_interval: int = 5):
    """Suit le statut du rafraîchissement jusqu'à sa fin (Completed ou Failed)."""
    history_url = (
        f"https://api.powerbi.com/v1.0/myorg/"
        f"groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top=1"
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    print("\nSuivi du statut du rafraîchissement en cours...")

    while True:
        response = requests.get(history_url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        refreshes = data.get("value", [])

        if not refreshes:
            print("Aucun historique de rafraîchissement trouvé.")
            break

        latest_refresh = refreshes[0]
        status = latest_refresh.get("status")
        start_time = latest_refresh.get("startTime")

        print(f"[{start_time}] Statut : {status}")

        if status == "Completed":
            print("\n Le rafraîchissement Power BI est terminé avec succès !")
            break
        elif status == "Failed":
            error_details = latest_refresh.get("serviceExceptionJson", "Pas de détails fournis")
            print(f"\n Échec du rafraîchissement Power BI !")
            print(f"Détails de l'erreur : {error_details}")
            # On lève une exception pour que la tâche Airflow passe en FAILED
            raise RuntimeError(f"Power BI Refresh Failed: {error_details}")
        elif status == "Disabled":
            print(f"\n Le rafraîchissement est désactivé sur ce semantic model.")
            raise RuntimeError("Power BI Refresh Disabled")

        # Tolère 'Unknown' et 'In Progress' puis patiente
        time.sleep(poll_interval)


def refresh_powerbi(max_retries: int = 3, backoff_factor: int = 60):
    """Déclenche le rafraîchissement du dataset avec gestion de la limite de requêtes 429."""
    workspace_id = os.environ["POWERBI_WORKSPACE_ID"]
    dataset_id = os.environ["POWERBI_DATASET_ID"]
    access_token = get_access_token()

    refresh_url = (
        f"https://api.powerbi.com/v1.0/myorg/"
        f"groups/{workspace_id}/datasets/{dataset_id}/refreshes"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, max_retries + 1):
        response = requests.post(refresh_url, headers=headers, timeout=30)

        if response.status_code == 202:
            print("Power BI refresh déclenché avec succès (202 Accepted).")
            # Attente initiale avant de vérifier l'historique
            time.sleep(5)
            poll_refresh_status(workspace_id, dataset_id, access_token)
            return

        elif response.status_code == 429:
            print(f"[Attention] Erreur 429 (Trop de requêtes). Tentative {attempt}/{max_retries}.")
            if attempt < max_retries:
                print(f"Attente de {backoff_factor} secondes avant de réessayer...")
                time.sleep(backoff_factor)
            else:
                response.raise_for_status()

        else:
            print(f"STATUS : {response.status_code}")
            print(f"RESPONSE : {response.text}")
            response.raise_for_status()


if __name__ == "__main__":
    print("Démarrage du refresh Power BI...")
    refresh_powerbi()