import os
import re
import pandas as pd


def extraire_mois_annee(file_path):
    """Extrait le mois et l'année à partir du nom du fichier."""
    nom = os.path.basename(file_path).lower()
    match = re.search(r"(20\d{2})", nom)
    annee = int(match.group(1)) if match else None

    mois = next(
        (
            m
            for m in [
                "janvier",
                "février",
                "mars",
                "avril",
                "mai",
                "juin",
                "juillet",
                "août",
                "septembre",
                "octobre",
                "novembre",
                "décembre",
            ]
            if m in nom
        ),
        None,
    )

    return annee, mois


def nettoyer_montant(val):
    """Nettoie et convertit les montants en Millions de DH (MDHS)."""
    try:
        val = str(val).replace(" ", "").replace(".", "").replace(",", ".")
        return float(val) / 1_000_000
    except:
        return None


def transformer_pivot(file_path):
    df = pd.read_excel(file_path, header=None)
    annee, mois = extraire_mois_annee(file_path)

    data = []
    genre = None
    produit = None

    for _, row in df.iterrows():
        # Extrait les valeurs non vides de la ligne
        values = [x for x in row if pd.notna(x)]

        if not values:
            continue

        values_str = [str(v).strip() for v in values]
        row_str = " ".join(values_str).lower()

        # 1️⃣ Détection du Genre (Femme / Homme)
        if "féminin" in row_str:
            genre = "Femme"
            continue
        elif "masculin" in row_str:
            genre = "Homme"
            continue

        # 2️⃣ Ignorer les en-têtes de colonnes et les totaux
        if (
            "région" in row_str
            or "produit" in row_str
            or "total" in row_str
            or "totale" in row_str
        ):
            continue

        region, produit_ligne, nb, montant = None, None, None, None

        # 3️⃣ CAS A : Format Octobre (4 colonnes -> [Région, Produit, Ménages, Crédits])
        if len(values) == 4 and any("foga" in str(v).lower() for v in values):
            region = values[0]
            produit_ligne = values[1]
            nb = values[2]
            montant = values[3]
        
        # 4️⃣ CAS B : Format Mai/Novembre (5+ colonnes -> [Genre, Région, Produit, ...])
        elif len(values) >= 5 and any("foga" in str(v).lower() for v in values):
            produit_ligne = [v for v in values if "foga" in str(v).lower()][0]
            region = values[1] if values[0] in ["Femme", "Masculin", "Féminin"] else values[2]
            nb = values[3]
            montant = values[4]

        # 5️⃣ CAS C : Ligne région seule (3 colonnes)
        elif len(values) == 3 and produit:
            region = values[0]
            nb = values[1]
            montant = values[2]
            produit_ligne = produit

        else:
            continue

        # Sauvegarde du dernier produit rencontré
        if produit_ligne:
            produit = produit_ligne

        # Validation numérique du nombre de ménages
        try:
            nb = float(nb)
        except:
            continue

        # Conversion du montant
        montant_nettoye = nettoyer_montant(montant)

        # Ajout aux résultats
        data.append(
            {
                "annee": annee,
                "mois": mois,
                "genre": genre,
                "region": region,
                "type_credit": str(produit_ligne).capitalize(),
                "nb_menages": int(nb),
                "montant_mdhs": montant_nettoye,
            }
        )

    return pd.DataFrame(data)



liste_paths = [
    "/opt/airflow/data/raw/damane sakane genre/2025/main new not like others_2025.xlsx",
    "/opt/airflow/data/raw/damane sakane genre/2025/novembre not like others_2025.xls",
    "/opt/airflow/data/raw/damane sakane genre/2025/Octobre_ not like others_2025.xlsx",
    "/opt/airflow/data/raw/damane sakane genre/2025/septembre not like others_2025.xls",
    "/opt/airflow/data/raw/damane sakane genre/2025/juillet not like others v3nn_2025.xlsx",
    "/opt/airflow/data/raw/damane sakane genre/2025/JUIN not like others v3nnn_2025.xlsx",

]

all_data = []

def stg_collecte_not_like_others_2025():
    for path in liste_paths:
        df = transformer_pivot(path)
        all_data.extend(df.to_dict(orient="records"))

    return all_data


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
data = stg_collecte_not_like_others_2025()
df_final = pd.DataFrame(data)

# trier les données
df_final = df_final.sort_values(by=["annee", "mois", "region", "type_credit"])

# reset index
df_final = df_final.reset_index(drop=True)

#print(df_final)
print(df_final)

