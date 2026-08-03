import pandas as pd
import os

def extraire_annee_mois(file_path):
    # récupérer année depuis le dossier
    annee = os.path.basename(os.path.dirname(file_path))

    # récupérer mois depuis nom fichier
    mois = os.path.basename(file_path).split("_")[0].lower()

    return annee, mois


def transformer_fichier(file_path):
    df = pd.read_excel(file_path, header=None)

    annee, mois = extraire_annee_mois(file_path)

    data = []
    genre = None

    for _, row in df.iterrows():

        values = [x for x in row if pd.notna(x)]

        if len(values) == 0:
            continue

        row_str = " ".join([str(x) for x in values])

        # détecter genre
        if "Masculin" in row_str:
            genre = "Homme"
            continue

        if "Féminin" in row_str:
            genre = "Femme"
            continue

        # ignorer titres
        if any(word in row_str for word in ["Régions", "Ménages", "FOGALOGE", "FOGARIM"]):
            continue

        # lignes valides
        if genre and len(values) >= 5:

            region = values[0]

            try:
                fogaloge_m = float(str(values[1]).replace(",", "."))
                fogaloge_c = float(str(values[2]).replace(",", "."))
                fogarim_m = float(str(values[3]).replace(",", "."))
                fogarim_c = float(str(values[4]).replace(",", "."))
            except:
                continue

            # 🔥 FORMAT LONG (2 lignes par région)

            data.append({
                "annee": annee,
                "mois": mois,
                "genre": genre,
                "region": region,
                "type_credit": "Fogaloge",
                "nb_menages": fogaloge_m,
                "montant_mdhs": fogaloge_c
            })

            data.append({
                "annee": annee,
                "mois": mois,
                "genre": genre,
                "region": region,
                "type_credit": "Fogarim",
                "nb_menages": fogarim_m,
                "montant_mdhs": fogarim_c
            })

    return pd.DataFrame(data)


list_paths = [
    
    "D:/stage 2026/projet sakane credit/data/raw/damane sakane genre/2024/decembre_2024.xls",
    "D:/stage 2026/projet sakane credit/data/raw/damane sakane genre/2024/novembre_2024.xls",
    "D:/stage 2026/projet sakane credit/data/raw/damane sakane genre/2024/octobre_2024.xls",
    "D:/stage 2026/projet sakane credit/data/raw/damane sakane genre/2024/septembre_2024.xls",
    "D:/stage 2026/projet sakane credit/data/raw/damane sakane genre/2025/JANV_2025.xls",
    "D:/stage 2026/projet sakane credit/data/raw/damane sakane genre/2025/mars_2025.xls"
    
]

all_data = []

def stg_collecte_2024_2025():
    for path in list_paths:
        df = transformer_fichier(path)
        all_data.extend(df.to_dict(orient="records"))

    return all_data

