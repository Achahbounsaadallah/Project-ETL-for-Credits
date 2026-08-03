import os
import pandas as pd


def extraire_annee_mois(file_path):
    annee = os.path.basename(os.path.dirname(file_path))
    mois = os.path.basename(file_path).split("_")[0].lower()
    return annee, mois

def to_float(val):
    val = val.replace(" ", "").replace(",", ".")
    return float(val)


def transformer_fichier(file_path):

    df = pd.read_excel(file_path, header=None)

    annee, mois = extraire_annee_mois(file_path)

    data = []
    produit_actuel = None
    genre_actuel = None

    for _, row in df.iterrows():

        values = [str(x).strip() for x in row if str(x) != "nan"]

        if not values:
            continue

        row_str = " ".join(values)

        # Produit
        if "FOGALOGE" in row_str.upper():
            produit_actuel = "Fogaloge"
            continue
        elif "FOGARIM" in row_str.upper():
            produit_actuel = "Fogarim"
            continue

        # Genre (persistant)
        if "Féminin" in row_str:
            genre_actuel = "Femme"
            continue
        elif "Masculin" in row_str:
            genre_actuel = "Homme"
            continue

        # ignorer header
        if any(x in row_str for x in ["Régions", "Dossiers", "Montant", "Genre"]):
            continue

        # data
        if produit_actuel and genre_actuel:

            try:
                if len(values) == 4:
                    region = values[1]
                    nb = values[2]
                    mt = values[3]
                elif len(values) == 3:
                    region = values[0]
                    nb = values[1]
                    mt = values[2]
                else:
                    continue

                data.append({
                    "annee": annee,
                    "mois": mois,
                    "genre": genre_actuel,
                    "region": region,
                    "type_credit": produit_actuel,
                    "nb_menages": to_float(nb),
                    "montant_mdhs": to_float(mt),
                })

            except:
                continue

    return pd.DataFrame(data)

# 🔥 TEST
list_paths = [
    "D:/stage 2026/projet sakane credit/data/raw/damane sakane genre/2026/avril_2026.xls",
    "D:/stage 2026/projet sakane credit/data/raw/damane sakane genre/2026/fev_2026.xlsx",
    "D:/stage 2026/projet sakane credit/data/raw/damane sakane genre/2026/janvier_2026.xlsx",
    

]

all_data = []

def stg_collecte_2026():
    for path in list_paths:
        df = transformer_fichier(path)
        all_data.extend(df.to_dict(orient="records"))

    return all_data



