import os
from groq import Groq
import threading
from datetime import datetime
import time

class BrainAI:
    def __init__(self, api_key):
        self.mensagens = []
        self._lock = threading.Lock()
        self.log_file = "ia_decisions.log"

        if not api_key or api_key == "SUA_CHAVE_AQUI":
            print("⚠️  AVISO: A chave da API da Groq não foi definida. O filtro de IA estará desativado.")
            print("    Obtenha uma chave em https://console.groq.com/keys e insira em app.py.")
            self.client = None
            return
            
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def log_pensamento(self, mensagem):
        """Adiciona uma mensagem ao log de pensamentos da IA para o front-end."""
        with self._lock:
            agora = datetime.now().strftime("%H:%M:%S")
            texto_formatado = f"🧠 [GROQ AI - {agora}]: {mensagem}"
            self.mensagens.append(texto_formatado)
            print(texto_formatado) # Loga também no console
            # Mantém apenas as últimas 50 mensagens
            if len(self.mensagens) > 50:
                self.mensagens.pop(0)

    def obter_mensagens(self):
        """Retorna as mensagens pendentes e limpa a lista."""
        with self._lock:
            msgs = self.mensagens[:]
            self.mensagens.clear()
            return msgs

    def _log_to_file(self, prompt_content, decision, raw_response):
        """Salva a análise completa em um arquivo de log para auditoria."""
        try:
            with self._lock: # Garante que a escrita no arquivo seja segura entre threads
                with open(self.log_file, "a", encoding="utf-8") as f:
                    log_entry = f"""
================================================================================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Decision: {decision}
Raw AI Response: {raw_response}
--------------------------------- PROMPT ---------------------------------
{prompt_content}
================================================================================

"""
                    f.write(log_entry)
        except Exception as e:
            print(f"🚨 CRÍTICO: Falha ao escrever no arquivo de log '{self.log_file}': {e}")

    def registrar_experiencia(self, dados_mercado, decisao_ia, resultado_real):
        """
        Salva dados estruturados para treinamento do modelo local (Random Forest).
        Arquivo: brain_training_data.csv
        """
        arquivo = "brain_training_data.csv"
        try:
            with self._lock:
                # Cria cabeçalho se arquivo não existir
                if not os.path.exists(arquivo) or os.path.getsize(arquivo) == 0:
                    with open(arquivo, "w", encoding="utf-8") as f:
                        f.write("votos_call,votos_put,historico_csv,decisao_groq,resultado_real\n")
                
                # Prepara a linha
                linha = f"{dados_mercado['votos_call']},{dados_mercado['votos_put']},\"{dados_mercado['historico_csv']}\",{decisao_ia},{resultado_real}\n"
                
                with open(arquivo, "a", encoding="utf-8") as f:
                    f.write(linha)
        except Exception as e:
            print(f"🚨 Erro ao registrar experiência para ML: {e}")

    def _gerar_resumo_estatistico(self, historico_longo):
        """Cria um resumo estatístico local para economizar tokens."""
        if not historico_longo:
            return "Histórico insuficiente."
        
        precos = [v['close'] for v in historico_longo]
        topo = max(precos)
        fundo = min(precos)
        media = sum(precos) / len(precos)
        tendencia = 'Alta' if precos[-1] > precos[0] else 'Baixa'
        
        return f"Resumo de {len(historico_longo)} velas: Max:{topo:.5f}, Min:{fundo:.5f}, Média:{media:.5f}. Tendência Geral: {tendencia}."

    def _compactar_historico_csv(self, historico):
        """Transforma a lista de velas em uma string CSV compacta."""
        if not historico:
            return ""
        
        # Cabeçalho
        csv_string = "horario,open,high,low,close,volume\n"
        
        # Linhas de dados
        for vela in historico:
            # Formata o horário para remover ':' (ex: 21:00:00 -> 2100)
            horario_compacto = vela.get('horario_formatado', '00:00:00').split(':')[0] + vela.get('horario_formatado', '00:00:00').split(':')[1]
            linha = (
                f"{horario_compacto},"
                f"{vela['open']:.5f},"
                f"{vela['max']:.5f},"
                f"{vela['min']:.5f},"
                f"{vela['close']:.5f},"
                f"{int(vela['volume'])}\n"
            )
            csv_string += linha
            
        return csv_string

    def validar_sinal(self, sinal, historico_completo, contexto_tecnico=None):
        """
        Usa a IA da Groq para validar se um sinal de entrada é seguro.
        Retorna "PROCEED" ou "BLOCK".
        """
        if not self.client:
            return "PROCEED" # Se a API não está configurada, permite a passagem.

        self.log_pensamento(f"Analisando sinal de '{sinal}' (Modo Ninja)...")

        if not historico_completo:
            return "BLOCK" # Não operar sem contexto

        # --- OTIMIZAÇÃO DE TOKENS (Prompt Ninja) ---
        # 1. Indicadores Técnicos (Calculados localmente em estrategias.py)
        indicadores_str = "N/A"
        if contexto_tecnico:
            rsi = contexto_tecnico.get('rsi', 50)
            tendencia = contexto_tecnico.get('tendencia', 'Indefinida')
            bb = contexto_tecnico.get('bb')
            bb_str = f"BB_Width: {bb['bandwidth']:.5f}" if bb else "BB: N/A"
            indicadores_str = f"RSI: {rsi:.1f}, Tendência: {tendencia}, {bb_str}"

        # 2. Price Action Recente (Apenas últimas 3 velas para contexto visual imediato)
        ultimas_velas = historico_completo[-3:]
        velas_str = ""
        for v in ultimas_velas:
            # Formato ultra-compacto: [O C H L]
            velas_str += f"[{v['open']:.5f} {v['close']:.5f} {v['max']:.5f} {v['min']:.5f}] "

        prompt = f"""
Atue como trader algorítmico.
Indicadores: {indicadores_str}
Price Action (3 velas): {velas_str}
Sinal: {sinal}
Ação (PROCEED/BLOCK)?
"""

        try:
            self.log_pensamento("Comparando cenário com padrões de risco...")
            print("🧠 Consultando IA da Groq para validação de sinal...")
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=10,
            )
            resposta = chat_completion.choices[0].message.content.strip().upper()
            
            resultado_final = "PROCEED" if "PROCEED" in resposta else "BLOCK"
            self.log_pensamento(f"Decisão: {resultado_final}. Motivo: Análise de fluxo e risco de reversão.")
            
            # Salva a análise completa no arquivo de log
            self._log_to_file(prompt, resultado_final, resposta)
            return resultado_final

        except Exception as e:
            print(f"🚨 Erro na chamada da API Groq: {e}")
            self.log_pensamento(f"Erro na API. Bloqueando por segurança: {e}")
            self._log_to_file(prompt, "BLOCK (API Error)", str(e))
            return "BLOCK" # Em caso de erro, bloqueia por segurança