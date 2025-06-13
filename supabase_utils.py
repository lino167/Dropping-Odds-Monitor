import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import logging

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("SUPABASE_URL e SUPABASE_KEY devem estar definidas no arquivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def salvar_alerta_supabase(alerta: dict) -> bool:
    response = supabase.table("alertas_partidas").insert(alerta).execute()
    return response.status_code == 201

def salvar_dataframe_supabase(df: pd.DataFrame) -> None:
    registros = df.to_dict(orient="records")
    if registros:
        response = supabase.table("alertas_partidas").insert(registros).execute()
        if response.status_code != 201:
            raise Exception(f"Erro ao inserir registros: {response.data}")

def alerta_ja_existente(game_id: str) -> bool:
    response = supabase.table("alertas_partidas").select("game_id").eq("game_id", game_id).execute()
    return len(response.data) > 0

def registrar_alerta_supabase(game_id: str, alerta: dict) -> bool:
    if alerta_ja_existente(game_id):
        logging.info(f"Alerta para game_id {game_id} já registrado no Supabase. Ignorando.")
        return False
    return salvar_alerta_supabase(alerta)

def consultar_ultimos_alertas(limit: int = 10) -> list:
    response = supabase.table("alertas_partidas").select("*").order("created_at", desc=True).limit(limit).execute()
    return response.data

def salvar_com_fallback(alerta: dict) -> None:
    try:
        salvar_alerta_supabase(alerta)
    except Exception as e:
        with open("alertas_falhos.log", "a") as f:
            f.write(f"\n[{pd.Timestamp.now()}] Falha ao salvar alerta: {alerta}\nErro: {str(e)}")
        logging.error(f"Erro ao salvar alerta no Supabase. Registrado localmente.")

def importar_alertas_do_excel(excel_path: str = "alertas.xlsx") -> None:
    if not os.path.exists(excel_path):
        raise FileNotFoundError("Arquivo Excel não encontrado.")
    df = pd.read_excel(excel_path)
    salvar_dataframe_supabase(df)
