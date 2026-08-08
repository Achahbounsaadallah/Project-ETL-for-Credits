import os
import pandas as pd


# 📅 Extraire année + mois depuis le chemin
def extraire_annee_mois(file_path):
    annee = os.path.basename(os.path.dirname(file_path))
    
    nom_fichier = os.path.basename(file_path).lower()

    mois_map = {
        "janvier": "janvier",
        "janv": "janvier",
        "fev": "fevrier",
        "février": "fevrier",
        "mars": "mars",
        "avril": "avril",
        "mai": "mai",
        "juin": "juin",
        "juillet": "juillet",
        "aout": "aout",
        "août": "aout",
        "sept": "septembre",
        "septembre": "septembre",
        "oct": "octobre",
        "nov": "novembre",
        "dec": "decembre",
        "décembre": "decembre"
    }

    mois = None
    for key in mois_map:
        if key in nom_fichier:
            mois = mois_map[key]
            break

    return int(annee), mois


# 🔢 convertir string -> float
def to_float(val):
    val = str(val).replace(" ", "").replace(",", ".")
    return float(val)


# 🧠 Transformation principale
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

        row_str = " ".join(values).upper()

        # 🔥 détecter produit
        if "FOGALOGE" in row_str:
            produit_actuel = "Fogaloge"
            continue

        elif "FOGARIM" in row_str:
            produit_actuel = "Fogarim"
            continue

        # 🔥 détecter genre
        if "FÉMININ" in row_str or "FEMININ" in row_str:
            genre_actuel = "Femme"
            continue

        elif "MASCULIN" in row_str:
            genre_actuel = "Homme"
            continue

        # 🚫 ignorer headers
        if any(x in row_str for x in ["RÉGION", "REGION", "MÉNAGES", "MENAGES", "CRÉDIT", "CREDIT"]):
            continue

        # 🎯 extraction data
        if produit_actuel and genre_actuel:

            try:
                # cas : region | nb | montant
                if len(values) == 3:
                    region = values[0]
                    nb = values[1]
                    mt = values[2]

                # cas : produit | region | nb | montant
                elif len(values) == 4:
                    region = values[1]
                    nb = values[2]
                    mt = values[3]

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


# 🔁 TRAITEMENT DE PLUSIEURS FICHIERS
list_paths = [
    "/opt/airflow/data/raw/damane sakane genre/2026/juin_2026.xls",
    "/opt/airflow/data/raw/damane sakane genre/2026/mai_2026.xls",
    "/opt/airflow/data/raw/damane sakane genre/2026/Mars_2026.xls",
]


all_data = []

def stg_collecte_2026_v2():
    for path in list_paths:
        df = transformer_fichier(path)
        all_data.extend(df.to_dict(orient="records"))

    return all_data


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
data = stg_collecte_2026_v2()
df_final = pd.DataFrame(data)

# trier les données
df_final = df_final.sort_values(by=["annee", "mois", "region", "type_credit"])

# reset index
df_final = df_final.reset_index(drop=True)

#print(df_final)
print(df_final)






