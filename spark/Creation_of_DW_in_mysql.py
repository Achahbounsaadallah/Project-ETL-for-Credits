import sqlalchemy as sa
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

server = os.getenv('DB_HOST')
database = os.getenv('DW_NAME')

connection_string = (
    f"mssql+pyodbc://@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = sa.create_engine(connection_string)
with engine.connect() as conn:

    conn.execute(sa.text("""

    -- DIMENSIONS

    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DimTemps' AND xtype='U')
    CREATE TABLE DimTemps (
        DateKey BIGINT PRIMARY KEY,
        date DATE,
        annee INT,
        mois INT,
        trimestre INT
    );

    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DimGenre' AND xtype='U')
    CREATE TABLE DimGenre (
        GenreKey BIGINT PRIMARY KEY,
        genre NVARCHAR(50)
    );

    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DimRegion' AND xtype='U')
    CREATE TABLE DimRegion (
        RegionKey BIGINT PRIMARY KEY,
        region NVARCHAR(100)
    );

    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DimTypeCredit' AND xtype='U')
    CREATE TABLE DimTypeCredit (
        CreditKey BIGINT PRIMARY KEY,
        type_credit NVARCHAR(50)
    );

    -- FACT TABLE

    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FactCredit' AND xtype='U')
    CREATE TABLE FactCredit (
        DateKey BIGINT,
        GenreKey BIGINT,
        RegionKey BIGINT,
        CreditKey BIGINT,
        nb_menages INT,
        montant_mdhs FLOAT
    );

    """))

    conn.commit()

print("✅ Data Warehouse créé avec succès !")