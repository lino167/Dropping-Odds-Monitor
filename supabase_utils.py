import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Inicializa o cliente Supabase uma vez
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logging.info("Conexão com Supabase estabelecida com sucesso.")
except Exception as e:
    logging.error(f"Falha ao conectar com Supabase: {e}")
    supabase = None

def alerta_ja_existente(game_id: str) -> bool:
    """Verifica no Supabase se um alerta para o game_id já foi enviado."""
    if not supabase:
        logging.error("Cliente Supabase não inicializado. Não foi possível verificar o alerta.")
        return True # Previne envio de alertas se o BD estiver offline

    try:
        response = supabase.table("alertas_enviados").select("game_id").eq("game_id", game_id).execute()
        return len(response.data) > 0
    except Exception as e:
        logging.error(f"Erro ao verificar se alerta existe para game_id {game_id}: {e}")
        return True # Assume que já existe em caso de erro para evitar duplicatas

def salvar_alerta_supabase(alerta_data: dict) -> bool:
    """
    Salva um dicionário completo do alerta no Supabase.
    Retorna True se bem-sucedido, False caso contrário.
    """
    if not supabase:
        logging.error("Cliente Supabase não inicializado. Não foi possível salvar o alerta.")
        return False
        
    try:
        response = supabase.table("alertas_enviados").insert(alerta_data).execute()
        
        if len(response.data) > 0:
            logging.info(f"Alerta para game_id {alerta_data['game_id']} salvo no Supabase.")
            return True
        else:
            # A API do Supabase pode retornar um erro HTTP que é capturado na exceção
            logging.error(f"Falha ao salvar alerta para game_id {alerta_data['game_id']}. Resposta Supabase: {response}")
            return False
            
    except Exception as e:
        logging.error(f"Exceção ao salvar alerta para game_id {alerta_data['game_id']}: {e}")
        return False