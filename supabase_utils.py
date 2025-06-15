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

def alerta_ja_existente(game_id: str, supabase: Client) -> bool:
    response = supabase.table("alertas_enviados").select("game_id").eq("game_id", game_id).execute()
    return len(response.data) > 0

def salvar_alerta_supabase(alerta, mensagem_html=""):
    campos_supabase = [
        "game_id",
        "liga",
        "times",
        "favorito",
        "odd_inicial_favorito",
        "odd_atual_favorito",
        "queda_odd_favorito",
        "linha_gols_inicial",
        "odd_linha_gols_inicial",
        "linha_gols_atual",
        "odd_linha_gols_atual",
        "drop_total",
        "placar",
        "tempo_jogo",
        "url",
        "mensagem_html"
    ]

    game_id = alerta[0]
    if not alerta_ja_existente(game_id, supabase):
        dados = {campo: alerta[i] if i < len(alerta) else None for i, campo in enumerate(campos_supabase)}
        dados["mensagem_html"] = mensagem_html 
        supabase.table("alertas_enviados").insert(dados).execute()