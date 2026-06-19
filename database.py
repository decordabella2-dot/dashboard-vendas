import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / "faturamento.db"

CONTAS = [
    "Shopee",
    "Mercado Livre HL",
    "Mercado Livre Dabella",
    "Amazon HL",
    "TikTok Dabella",
    "TikTok HL",
]


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS faturamento (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                data  DATE    NOT NULL,
                conta TEXT    NOT NULL,
                valor REAL    NOT NULL DEFAULT 0,
                UNIQUE(data, conta)
            )
        """)
        conn.commit()


def inserir_ou_atualizar(data: str, conta: str, valor: float):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO faturamento (data, conta, valor)
            VALUES (?, ?, ?)
            ON CONFLICT(data, conta) DO UPDATE SET valor = excluded.valor
        """, (data, conta, valor))
        conn.commit()


def deletar_registro(data: str, conta: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM faturamento WHERE data = ? AND conta = ?", (data, conta))
        conn.commit()


def buscar_todos() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql("SELECT data, conta, valor FROM faturamento ORDER BY data DESC, conta", conn)
    if df.empty:
        return pd.DataFrame(columns=["data", "conta", "valor"])
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["valor"] = df["valor"].astype(float)
    return df


def buscar_por_periodo(data_inicio, data_fim) -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql(
            "SELECT data, conta, valor FROM faturamento WHERE data BETWEEN ? AND ? ORDER BY data, conta",
            conn,
            params=(str(data_inicio), str(data_fim)),
        )
    if df.empty:
        return pd.DataFrame(columns=["data", "conta", "valor"])
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["valor"] = df["valor"].astype(float)
    return df
