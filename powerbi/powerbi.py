import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def get_access_token() -> str:
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


def list_datasets():
    workspace_id = os.environ["POWERBI_WORKSPACE_ID"]
    access_token = get_access_token()

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers, timeout=30)
    print("DATASETS STATUS:", response.status_code)
    print("DATASETS RESPONSE:")
    print(response.text)
    response.raise_for_status()


def poll_refresh_status(workspace_id: str, dataset_id: str, access_token: str, poll_interval: int = 5):
    """Vérifie périodiquement l'état du dernier rafraîchissement."""
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
            break
        elif status == "Disabled":
            print(f"\n Le rafraîchissement est désactivé sur ce semantic model.")
            break

        # On continue la boucle si le statut est 'Unknown' ou 'In Progress'
        time.sleep(poll_interval)


def refresh_powerbi():
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

    response = requests.post(refresh_url, headers=headers, timeout=30)
    print("STATUS :", response.status_code)
    print("URL :", response.url)

    response.raise_for_status()
    print("Power BI refresh déclenché avec succès.")

    # Attente de 3 secondes avant la première vérification pour laisser le temps au job de s'inscrire
    time.sleep(3)
    poll_refresh_status(workspace_id, dataset_id, access_token)


if __name__ == "__main__":
    print("Démarrage du refresh Power BI local...")
    refresh_powerbi()