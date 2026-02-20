import os
from groq import Groq
import threading
from datetime import datetime
import time
import requests
import json

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

    def _verificar_excecoes_tecnicas(self, rsi, tendencia_str, preco, pivot):
        """Verifica regras de exceção para evitar bloqueios indevidos (Pipocadas)."""
        # Converte tendência para numérico (-1: Baixa, 1: Alta)
        tendencia = -1 if tendencia_str == "BAIXA" else (1 if tendencia_str == "ALTA" else 0)
        
        # REGRA 2: Exaustão de Venda (O "Pulo do Gato")
        if rsi < 30 and tendencia < 0:
            return True # "AUTORIZAR_EXCECAO"
        
        # REGRA 3: Super-Venda (Segurança Máxima)
        if rsi < 20:
            return True # "AUTORIZAR_EXCECAO"
            
        # REGRA 1: Força no Pivot
        if rsi < 70 and preco > pivot:
            return True # "AUTORIZAR_EXCECAO"

        return False

    def validar_sinal(self, sinal, historico_completo, contexto_tecnico=None, nota_aluna="", terreno="", regras_dinamicas=""):
        """
        Usa a IA da Groq para validar se um sinal de entrada é seguro.
        Retorna "PROCEED" ou "BLOCK".
        """
        if not self.client:
            return {"decision": "PROCEED", "source": "NO_API"}

        self.log_pensamento(f"Analisando sinal de '{sinal}' (Modo Ninja)...")

        if not historico_completo:
            return {"decision": "BLOCK", "source": "SYSTEM", "reason": "Histórico de velas insuficiente"}

        # --- LÓGICA DE EXCEÇÃO (ANTI-PIPOCADA) ---
        # Verifica regras técnicas antes de aplicar filtros da Aluna ou chamar a Groq.
        if contexto_tecnico and sinal == 'CALL': # Regras focadas em oportunidades de compra/reversão
            rsi = contexto_tecnico.get('rsi', 50)
            tendencia_str = contexto_tecnico.get('tendencia', 'NEUTRA')
            preco = contexto_tecnico.get('close', 0)
            pivot = contexto_tecnico.get('media_20', 0) # Usa SMA 20 como Pivot dinâmico
            
            if self._verificar_excecoes_tecnicas(rsi, tendencia_str, preco, pivot):
                self.log_pensamento(f"⚠️ Exceção Técnica Detectada! Ignorando filtros da Aluna para {sinal}.")
                return {"decision": "PROCEED", "source": "EXCEPTION_RULE", "reason": "Regra de Exceção Técnica (RSI/Pivot)"}

        # --- FILTRO DE ECONOMIA DE TOKENS (RALLY) ---
        # Se a Aluna detectou "BURACOS", nem incomoda o Professor (Groq).
        if "BURACOS" in terreno:
            self.log_pensamento(f"🛑 Aluna bloqueou chamada da API. Motivo: {terreno}")
            return {"decision": "BLOCK", "source": "ALUNA_FILTER", "reason": terreno}

        # Se a Aluna detectou "LAMA" (mercado lateral/sem direção), também bloqueia.
        # Isso equivale ao voto "NEUTRO" ou de baixa confiança.
        if "LAMA" in terreno:
            self.log_pensamento(f"🛑 Aluna bloqueou chamada da API. Motivo: {terreno}")
            return {"decision": "BLOCK", "source": "ALUNA_FILTER", "reason": terreno}

        # --- OTIMIZAÇÃO DE TOKENS (Prompt Ninja) ---
        # 1. Indicadores Técnicos (Calculados localmente em estrategias.py)
        indicadores_str = "N/A"
        if contexto_tecnico:
            rsi = contexto_tecnico.get('rsi', 50)
            tendencia = contexto_tecnico.get('tendencia', 'Indefinida')
            bb = contexto_tecnico.get('bb')
            bb_str = f"BB_Width: {bb['bandwidth']:.5f}" if bb else "BB: N/A"
            indicadores_str = f"RSI: {rsi:.1f}, Tendência: {tendencia}, {bb_str}, Terreno: {terreno}"

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
Nota da Aluna (Regra Local): {nota_aluna}
Regras Aprendidas (Exceções): {regras_dinamicas}
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
            
            reason = "Análise de fluxo e risco" if resultado_final == "BLOCK" else "Sinal confirmado"
            self._log_to_file(prompt, resultado_final, resposta) # Salva a análise completa no arquivo de log
            return {"decision": resultado_final, "source": "GROQ_API", "reason": reason}

        except Exception as e:
            print(f"🚨 Erro na chamada da API Groq: {e}")
            self.log_pensamento(f"Erro na API. Bloqueando por segurança: {e}")
            self._log_to_file(prompt, "BLOCK (API Error)", str(e))
            return {"decision": "BLOCK", "source": "API_ERROR", "reason": str(e)}

class StudentSLM:
    """
    IA Aluna (SLM Local - Qwen/Ollama):
    1. Classifica o Terreno (Asfalto, Lama, Buracos).
    2. Estuda o histórico recente e gera regras dinâmicas.
    """
    def __init__(self):
        self.arquivo_dados = "brain_training_data.csv"
        self.arquivo_regras = "regras_dinamicas.txt"
        self.regra_atual = "Nenhuma regra definida ainda. Opere com cautela."
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "deepseek-r1:1.5b" # Modelo leve sugerido
        self._lock = threading.Lock()
        self.regras_dinamicas = self._carregar_regras()

    def classificar_terreno(self, contexto):
        """
        Define o terreno atual baseado em indicadores técnicos.
        Retorna: 'ASFALTO' (Tendência), 'LAMA' (Lateral), 'BURACOS' (Volatilidade).
        """
        if not contexto:
            return "DESCONHECIDO"

        tendencia = contexto.get('tendencia', 'LATERAL')
        media_corpos = contexto.get('media_corpos', 0)
        bb = contexto.get('bb', {})
        bb_width = bb.get('bandwidth', 0) if bb else 0
        atr = contexto.get('atr', 0)
        
        # 1. BURACOS: Volatilidade extrema
        if bb_width > 0.00250 or (media_corpos > 0 and atr > media_corpos * 2.5):
            return "BURACOS (Alta Volatilidade/Risco)"
            
        # 2. LAMA: Mercado Lateral ou Bandas muito estreitas
        if tendencia == "LATERAL" or bb_width < 0.00030:
            return "LAMA (Lateral/Choppy)"
            
        # 3. ASFALTO: Tendência definida
        if tendencia in ["ALTA", "BAIXA"]:
            return f"ASFALTO ({tendencia})"
            
        return "LAMA"

    def estudar_professor(self):
        """Lê o histórico e gera regra via Ollama."""
        if not os.path.exists(self.arquivo_dados): return

        print("🎓 IA Aluna: Iniciando estudo do diário de trades (Ollama)...")
        try:
            with self._lock: # Protege a leitura para evitar conflito com a gravação de trades
                with open(self.arquivo_dados, "r", encoding="utf-8") as f:
                    linhas = f.readlines()
                    dados_recentes = linhas[-30:] # Janela de esquecimento

            if len(dados_recentes) < 5: return

            csv_texto = "".join(dados_recentes)
            prompt = f"""
Analise este histórico de trades (CSV):
{csv_texto}

O cabeçalho é: votos_call,votos_put,terreno,rsi,atr,bb_width,dist_sma,vol_rel,decisao_ia,resultado_real.
Novas métricas:
- dist_sma: Distância do preço para a Média Móvel (Se muito alto/baixo, preço esticou).
- vol_rel: Volume Relativo (Acima de 1.0 = Volume alto/Explosão).

Sistema de Pontuação:
LOSS = -10 pontos (Evitar a todo custo).
MISSED_WIN = -5 pontos (Evitar ficar de fora de movimentos bons).

Identifique padrões que causam perda de pontos.
Gere UMA regra técnica baseada em NÚMEROS (Ex: RSI > 70) para maximizar a pontuação.
NÃO use frases genéricas como "não ter prejuízo". Seja técnico.
Regra:
"""
            
            payload = {
                "model": self.model, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.3, "num_ctx": 2048}
            }
            
            # Aumentado para 900s (15 min) para evitar erro de Timeout com DeepSeek
            response = requests.post(self.ollama_url, json=payload, timeout=900)
            if response.status_code == 200:
                nova_regra = response.json().get("response", "").strip()
                if nova_regra:
                    self.regra_atual = nova_regra
                    print(f"🎓 IA Aluna (Nova Regra): {self.regra_atual}")
                    
                    # Salva a regra aprendida no arquivo permanente
                    with self._lock:
                        if nova_regra not in self.regras_dinamicas:
                            self.regras_dinamicas.append(nova_regra)
                            with open(self.arquivo_regras, "a", encoding="utf-8") as f:
                                f.write(f"{nova_regra}\n")
        except Exception as e:
            print(f"🚨 Falha ao estudar professor: {e}")

    def _carregar_regras(self):
        """Carrega regras dinâmicas do arquivo."""
        if not os.path.exists(self.arquivo_regras): return []
        try:
            with open(self.arquivo_regras, "r", encoding="utf-8") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except: return []

    def obter_regras_formatadas(self):
        """Retorna as últimas 3 regras aprendidas para injetar no prompt."""
        if not self.regras_dinamicas: return "Nenhuma regra extra."
        return " | ".join(self.regras_dinamicas[-3:])

    def refletir_sobre_erro(self, tipo_erro, sinal, contexto, historico_velas):
        """
        Motor de Auto-Reflexão: Analisa erros (MISSED_WIN ou PROCEED_LOSS)
        e gera novas regras de exceção usando a IA Local.
        """
        print(f"🤔 IA Aluna: Refletindo sobre erro {tipo_erro} em {sinal}...")
        
        # Prepara os dados para a IA
        rsi = contexto.get('rsi', 50)
        tendencia = contexto.get('tendencia', 'N/A')
        bb_width = contexto.get('bb', {}).get('bandwidth', 0)
        close = contexto.get('close', 0)
        media_20 = contexto.get('media_20', 0)
        dist_sma = close - media_20
        
        # Formata histórico recente para o prompt
        hist_str = ""
        for v in historico_velas:
            hist_str += f"[{v['open']:.4f}, {v['close']:.4f}, {v['max']:.4f}, {v['min']:.4f}] "

        prompt_reflexao = f"""
Você é um trader algorítmico.
Sistema de Pontuação:
LOSS = -10 pontos.
MISSED_WIN = -5 pontos.

Erro: {tipo_erro} (O robô errou ao decidir sobre um {sinal}).
Contexto Técnico: RSI={rsi:.2f}, Tendência={tendencia}, Distância SMA={dist_sma:.5f}, Volatilidade={bb_width:.5f}.
Últimas 15 velas: {hist_str}

Se bloqueou um WIN (MISSED_WIN), analise: o RSI estava em que nível? Teve pavio?
Crie uma regra de exceção técnica baseada em NÚMEROS para evitar perder pontos.
NÃO use frases genéricas.
Exemplo: "Se RSI < 30 e pavio > 2x corpo, autorizar CALL."
Nova Regra:
"""
        
        try:
            payload = {
                "model": self.model, 
                "prompt": prompt_reflexao, 
                "stream": False,
                "options": {"temperature": 0.4, "num_ctx": 2048}
            }
            
            # Aumentado para 900s (15 min) para evitar erro de Timeout
            response = requests.post(self.ollama_url, json=payload, timeout=900)
            if response.status_code == 200:
                nova_regra = response.json().get("response", "").strip().replace("\n", " ")
                if nova_regra:
                    with self._lock:
                        self.regras_dinamicas.append(nova_regra)
                        with open(self.arquivo_regras, "a", encoding="utf-8") as f:
                            f.write(f"{nova_regra}\n")
                    print(f"💡 IA Aluna (Insight): Nova regra aprendida -> {nova_regra}")
        except Exception as e:
            print(f"🚨 Erro na auto-reflexão: {e}")

    def _ensure_csv_header(self):
        """Cria o cabeçalho do CSV se o arquivo não existir ou estiver vazio."""
        header = "votos_call,votos_put,terreno,rsi,atr,bb_width,dist_sma,vol_rel,decisao_ia,resultado_real\n"
        
        # Verifica se precisa recriar o arquivo (se não existe ou se é o formato antigo)
        recriar = False
        if not os.path.exists(self.arquivo_dados) or os.path.getsize(self.arquivo_dados) == 0:
            recriar = True
        else:
            # Lê a primeira linha para ver se tem as novas colunas
            with open(self.arquivo_dados, "r", encoding="utf-8") as f:
                primeira_linha = f.readline()
                if "dist_sma" not in primeira_linha:
                    print("⚠️ Atualizando formato do cérebro (CSV) para incluir Volume e SMA...")
                    recriar = True
        
        if recriar:
            with open(self.arquivo_dados, "w", encoding="utf-8") as f:
                f.write(header)

    def registrar_telemetria(self, dados_mercado, contexto_tecnico, decisao_ia, resultado_real, terreno):
        """Salva dados enriquecidos com indicadores para a Aluna estudar."""
        arquivo = "brain_training_data.csv"
        with self._lock:
            self._ensure_csv_header()
            
            rsi = contexto_tecnico.get('rsi', 50)
            atr = contexto_tecnico.get('atr', 0)
            bb_width = contexto_tecnico.get('bb', {}).get('bandwidth', 0)
            
            # Novos Dados
            close = contexto_tecnico.get('close', 0)
            media_20 = contexto_tecnico.get('media_20', 0)
            volume = contexto_tecnico.get('volume', 0)
            vol_medio = contexto_tecnico.get('vol_medio', 1)
            
            dist_sma = close - media_20
            vol_rel = volume / vol_medio if vol_medio > 0 else 0

            linha = (f"{dados_mercado.get('votos_call',0)},"
                     f"{dados_mercado.get('votos_put',0)},"
                     f"{terreno},"
                     f"{rsi:.2f},"
                     f"{atr:.6f},"
                     f"{bb_width:.6f},"
                     f"{dist_sma:.6f},"
                     f"{vol_rel:.2f},"
                     f"{decisao_ia},"
                     f"{resultado_real}\n")
            try:
                with open(arquivo, "a", encoding="utf-8") as f:
                    f.write(linha)
            except: pass

    def prever(self, votos_call, votos_put):
        """
        Método de compatibilidade. Retorna 0.5 (Neutro) pois a decisão agora é via Regra/Terreno.
        """
        return 0.5