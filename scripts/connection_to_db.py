import sqlalchemy as sa
from All_stg_data import stg_collecte_all
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

server = os.getenv('DB_HOST')
database = os.getenv('DB_NAME')
print(f"Server: {server}, Database: {database}")

connection_string = (
    f"mssql+pyodbc://@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = sa.create_engine(connection_string)
with engine.connect() as conn:
    print("Connexion réussie ✅")
create_table_sql = """
IF OBJECT_ID('dbo.stg_credit', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.stg_credit (
        annee INT,
        mois NVARCHAR(50),
        genre NVARCHAR(100),
        region NVARCHAR(200),
        type_credit NVARCHAR(200),
        nb_menages FLOAT,
        montant_mdhs DECIMAL(18,2)
    )
END
"""
with engine.begin() as conn:
    conn.execute(sa.text(create_table_sql))

data = stg_collecte_all()
df_final = pd.DataFrame(data)

df_final.to_sql(
    name="stg_credit",
    con=engine,
    if_exists="replace",  # supprime + recrée
    index=False
)
