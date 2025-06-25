import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timedelta
from typing import Optional


# Inicializa o cliente Supabase uma vez para ser reutilizado
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logging.info("Conexão com Supabase estabelecida com sucesso.")
except Exception as e:
    logging.error(f"Falha ao conectar com Supabase: {e}")
    supabase = None

# --- Funções para a tabela 'alertas_enviados' ---

def alerta_ja_existente(game_id: str) -> bool:
    """Verifica se um alerta para um 'game_id' específico já foi enviado e salvo."""
    if not supabase: 
        logging.error("Cliente Supabase não inicializado. Assumindo que o alerta existe para evitar duplicatas.")
        return True
    try:
        # Consulta a tabela de alertas para ver se já existe um registo com este game_id
        response = supabase.table("alertas_enviados").select("game_id").eq("game_id", game_id).execute()
        return len(response.data) > 0
    except Exception as e:
        logging.error(f"Erro ao verificar se alerta existe para game_id {game_id}: {e}")
        return True # Previne envio de alertas em caso de erro

def salvar_alerta_supabase(alerta_data: dict) -> bool:
    """Salva um dicionário completo do alerta na tabela 'alertas_enviados'."""
    if not supabase: 
        logging.error("Cliente Supabase não inicializado. Não foi possível salvar o alerta.")
        return False
    try:
        # Verifica se o alerta já existe para evitar duplicatas
        response = supabase.table("alertas_enviados").insert(alerta_data).execute()
        
        if len(response.data) > 0:
            logging.info(f"Alerta para game_id {alerta_data['game_id']} salvo no Supabase.")
            return True
        else:
            logging.error(f"Falha ao salvar alerta para game_id {alerta_data['game_id']}. Resposta: {response}")
            return False
    except Exception as e:
        logging.error(f"Exceção ao salvar alerta para game_id {alerta_data['game_id']}: {e}")
        return False

# --- Funções para a tabela 'jogos_em_observacao' ---

def add_game_to_observation(observation_data: dict):
    """Adiciona ou atualiza um jogo na tabela 'jogos_em_observacao'."""
    if not supabase: return False
    try:
        # Upsert garante que se o jogo já estiver lá, ele será atualizado, evitando erros.
        response = supabase.table("jogos_em_observacao").upsert(observation_data).execute()
        if len(response.data) > 0:
            logging.info(f"Jogo {observation_data['game_id']} adicionado/atualizado na lista de observação.")
            return True
        return False
    except Exception as e:
        logging.error(f"Erro ao adicionar jogo {observation_data.get('game_id')} à observação: {e}")
        return False


def get_observed_game(game_id: str) -> Optional[dict]:
    """Busca um jogo da tabela 'jogos_em_observacao'."""
    if not supabase: return None
    try:
        # Usamos .execute() que sempre retorna um objeto de resposta, tornando o código mais seguro
        response = supabase.table("jogos_em_observacao").select("*").eq("game_id", game_id).execute()
        
        # Verificamos se a resposta contém dados e retornamos o primeiro item (único) se existir
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logging.error(f"Erro ao buscar jogo {game_id} da observação: {e}")
        return None

def remove_game_from_observation(game_id: str):
    """Remove um jogo da tabela 'jogos_em_observacao' após o alerta ser gerado."""
    if not supabase: return False
    try:
        supabase.table("jogos_em_observacao").delete().eq("game_id", game_id).execute()
        logging.info(f"Jogo {game_id} removido da lista de observação.")
        return True
    except Exception as e:
        logging.error(f"Erro ao remover jogo {game_id} da observação: {e}")
        return False

# --- FUNÇÕES PARA A ATUALIZAÇÃO DO PLACAR FINAL ---

def get_alerts_to_update(time_window_hours: int = 3) -> list:
    """Busca no Supabase alertas enviados recentemente que ainda não têm um placar final."""
    if not supabase: return []
    try:
        # Define o limiar de tempo para buscar alertas (ex: últimas 3 horas)
        time_threshold = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        response = supabase.table("alertas_enviados") \
            .select("game_id, url") \
            .is_("placar_final", "null") \
            .gte("enviado_em", time_threshold.isoformat()) \
            .execute()
            
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Erro ao buscar alertas para atualização: {e}")
        return []

def update_alert_with_final_score(game_id: str, final_score: str):
    """Atualiza um alerta existente com o placar final."""
    if not supabase: return False
    try:
        response = supabase.table("alertas_enviados") \
            .update({"placar_final": final_score}) \
            .eq("game_id", game_id) \
            .execute()
            
        if len(response.data) > 0:
            logging.info(f"Placar final '{final_score}' atualizado para o jogo {game_id}.")
            return True
        return False
    except Exception as e:
        logging.error(f"Erro ao atualizar placar final para o jogo {game_id}: {e}")
        return False