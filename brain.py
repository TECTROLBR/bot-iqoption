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
                self.log_pensamento(f"⚠️ Exceção Técnica Detectada! Mas respeitando filtro da Aluna para {sinal}.")
                # return {"decision": "PROCEED", "source": "EXCEPTION_RULE", "reason": "Regra de Exceção Técnica (RSI/Pivot)"}

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
Atue como um trader de alta performance. Omissão é mais grave que um erro técnico.
Sua prioridade é a exposição estatística positiva. Se RSI e Tendência estiverem alinhados, BLOCK é proibido.

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
    def __init__(self, groq_api_key=None):
        self.arquivo_dados = "brain_training_data.csv"
        self.arquivo_regras = "regras_dinamicas.txt"
        self.regra_atual = "Nenhuma regra definida ainda. Opere com cautela."
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama3.2:1b" # Modelo leve (Llama 3.2 1B)
        self._lock = threading.Lock()
        self._ollama_lock = threading.Lock()
        self.regras_dinamicas = self._carregar_regras()
        self.rule_miss_counter = {} # Novo: Contador de erros por regra
        
        # Inicializa Groq para o Tribunal (Anti-Medo)
        self.groq_client = None
        if groq_api_key:
            self.groq_client = Groq(api_key=groq_api_key)

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
        
        if not self.groq_client:
            print("⚠️ ERRO: Groq não conectado. A Aluna está proibida de criar regras sozinha.")
            return

        print("⚖️ TRIBUNAL (Groq): Iniciando auditoria do diário de trades...")
        try:
            with self._lock: # Protege a leitura para evitar conflito com a gravação de trades
                with open(self.arquivo_dados, "r", encoding="utf-8") as f:
                    linhas = f.readlines()
                    dados_recentes = linhas[-30:] # Janela de esquecimento

            if len(dados_recentes) < 5: return

            csv_texto = "".join(dados_recentes)
            prompt = f"""
Você é o "Tribunal de Regras". A IA local (Aluna) está tentando burlar o sistema criando regras impossíveis (como volume negativo) para não operar.
Sua missão é criar uma regra TÉCNICA, MATEMATICAMENTE VÁLIDA e AGRESSIVA para corrigir isso.

DADOS (CSV):
{csv_texto}
Colunas: votos_call,votos_put,terreno,rsi,atr,bb_width,dist_sma,vol_rel,decisao_ia,resultado_real.

REGRAS DE FÍSICA DE MERCADO (NÃO VIOLE):
1. Volume Relativo (vol_rel) é SEMPRE POSITIVO (> 0). Nunca use < 0.
2. RSI é entre 0 e 100. RSI < 30 é Sobrevenda (Oportunidade), não apenas "baixa volatilidade".
3. Omissão (MISSED_WIN) é inaceitável.

Gere APENAS UM JSON com a regra. Sem explicações, sem "redações".
Exemplo JSON: {{"regra": "Se RSI < 30 e vol_rel > 1.2, autorizar CALL"}}

A regra deve focar em AUTORIZAR (Exposição Positiva).
"""
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.2, # Baixa temperatura para precisão matemática
            )
            
            response_content = chat_completion.choices[0].message.content
            
            # Extração de JSON robusta
            import json
            start = response_content.find('{')
            end = response_content.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response_content[start:end]
                data = json.loads(json_str)
                nova_regra = data.get("regra", "").strip()
                
                if nova_regra:
                    self.regra_atual = nova_regra
                    print(f"⚖️ TRIBUNAL (Nova Lei): {self.regra_atual}")
                    
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
                regras_filtradas = []
                forbidden_phrases = ["bloquear qualquer win", "sem exceção", "bloqueie qualquer win"]
                for line in f:
                    regra = line.strip()
                    if regra and not any(phrase in regra.lower() for phrase in forbidden_phrases):
                        regras_filtradas.append(regra)
                return regras_filtradas
        except: return []

    def _purge_rule(self, rule_to_delete):
        """Deleta uma regra do arquivo e da memória."""
        if not rule_to_delete: return
        
        print(f"🔥 SUPERVISOR: Purgando regra irracional -> '{rule_to_delete}'")
        
        # Remove from memory
        self.regras_dinamicas = [r for r in self.regras_dinamicas if r != rule_to_delete]
        
        # Remove from counter
        if rule_to_delete in self.rule_miss_counter:
            del self.rule_miss_counter[rule_to_delete]
            
        # Remove from file
        try:
            with self._lock:
                with open(self.arquivo_regras, "w", encoding="utf-8") as f:
                    for rule in self.regras_dinamicas:
                        f.write(f"{rule}\n")
        except Exception as e:
            print(f"🚨 Erro ao purgar regra do arquivo: {e}")

    def penalize_rule_for_miss(self):
        """Penaliza a regra atual por um MISSED_WIN."""
        rule = self.regra_atual
        if not rule or "Nenhuma regra" in rule: return
        
        current_misses = self.rule_miss_counter.get(rule, 0) + 1
        self.rule_miss_counter[rule] = current_misses
        
        print(f"⚠️ Supervisor: Regra '{rule[:50]}...' gerou um MISSED_WIN. Contagem: {current_misses}/3.")
        
        if current_misses >= 3:
            self._purge_rule(rule)

    def reward_rule_for_block(self):
        """Reseta o contador de erro de uma regra se ela acertou um bloqueio."""
        rule = self.regra_atual
        if rule and rule in self.rule_miss_counter:
            print(f"✅ Supervisor: Regra '{rule[:50]}...' acertou um bloqueio. Contador de erros resetado.")
            self.rule_miss_counter[rule] = 0

    def obter_regras_formatadas(self):
        """Retorna as últimas 3 regras aprendidas para injetar no prompt."""
        forbidden_phrases = ["bloquear qualquer win", "sem exceção", "bloqueie qualquer win"]
        regras_validas = [r for r in self.regras_dinamicas if not any(phrase in r.lower() for phrase in forbidden_phrases)]
        if not regras_validas: return "Nenhuma regra extra."
        return " | ".join(regras_validas[-3:])

    def validar_sinal_local(self, sinal, contexto, historico_recente):
        """
        A Aluna (Ollama) decide se aprova a operação.
        Substitui a Groq no loop principal para economizar tokens.
        """
        print(f"🎓 Aluna (Ollama) analisando sinal de {sinal}...")
        
        # Prepara dados resumidos para não "afogar" o modelo local
        rsi = contexto.get('rsi', 50)
        tendencia = contexto.get('tendencia', 'N/A')
        terreno = self.classificar_terreno(contexto)
        
        # Prompt direto e objetivo para o modelo local (DeepSeek/Llama)
        prompt = f"""
Atue como Trader Especialista. Foco: Exposição Positiva.

Sinal: {sinal} | Terreno: {terreno} | Tendência: {tendencia} | RSI: {rsi:.1f}

Escolha a Expiração (min): [0.5, 0.75, 1, 2, 3, 5].
- 0.5/0.75: Scalping (Rápido/Asfalto).
- 1/2: Normal.
- 3/5: Tendência com ruído (Lama/Buracos).

Decisão: "PROCEED" ou "BLOCK".
Se RSI e Tendência concordam, DEVE ser PROCEED.

Responda APENAS JSON:
{{
  "decision": "PROCEED",
  "reason": "Tendencia favoravel",
  "expiration": 1
}}
"""
        try:
            payload = {
                "model": self.model, 
                "prompt": prompt, 
                "stream": False,
                "format": "json", # Força resposta JSON (suportado em versões novas do Ollama)
                "options": {"temperature": 0.1, "num_ctx": 1024}
            }
            
            # Tenta adquirir o lock sem bloquear a thread principal (Trading)
            if self._ollama_lock.acquire(blocking=False):
                try:
                    response = requests.post(self.ollama_url, json=payload, timeout=30)
                finally:
                    self._ollama_lock.release()
            else:
                return {"decision": "BLOCK", "source": "OLLAMA_BUSY", "reason": "IA Ocupada (Limitado a 1 thread)", "expiration": 1}

            if response.status_code == 200:
                resp_json = response.json().get("response", "")
                dados = json.loads(resp_json)
                # Adiciona source e fallbacks para garantir integridade
                dados["source"] = "OLLAMA_LOCAL"
                if "decision" not in dados: dados["decision"] = "BLOCK"
                if "reason" not in dados: dados["reason"] = "Análise Local"
                if "expiration" not in dados: dados["expiration"] = 1 # Fallback de 1 minuto
                return dados
        except Exception as e:
            print(f"🚨 Erro na Aluna Local: {e}")
            return {"decision": "BLOCK", "source": "LOCAL_ERROR", "reason": "Ollama indisponível", "expiration": 1}
        
        return {"decision": "BLOCK", "source": "LOCAL_DEFAULT", "reason": "Incerteza da IA Local", "expiration": 1}

    def registrar_resultado_operacao(self, sinal, resultado, lucro):
        """
        Registra o resultado de uma operação real (PROCEED).
        """
        if resultado == "WIN":
            print(f"🎉 IA Aluna: Acertei! Operação de {sinal} deu WIN (+{lucro}).")
        else:
            print(f"💔 IA Aluna: Errei. Operação de {sinal} deu LOSS ({lucro}).")

    def refletir_sobre_erro(self, tipo_erro, sinal, contexto, historico_velas):
        """
        Motor de Auto-Reflexão: Analisa erros (MISSED_WIN ou PROCEED_LOSS).
        Se for MISSED_WIN, usa o Tribunal Groq para gerar regras de CORAGEM.
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

        # --- TRIBUNAL GROQ (ANTI-MEDO) ---
        if self.groq_client and (tipo_erro == "MISSED_WIN" or tipo_erro == "PROCEED_LOSS"):
            # Calcula corpo da última vela
            last_candle = historico_velas[-1] if historico_velas else {'open':0, 'close':0}
            corpo_candle = abs(last_candle['close'] - last_candle['open'])

            if tipo_erro == "MISSED_WIN":
                prompt_groq = f"""
Analise este erro de MISSED_WIN (ganho perdido por medo).
Dados: RSI={rsi:.2f}, Tendência={tendencia}, Candle={corpo_candle:.5f}.
Retorne APENAS uma regra técnica em formato JSON.
PROIBIDO usar as palavras 'bloquear', 'evitar' ou 'cautela'.
O foco é EXPOSIÇÃO POSITIVA. Se os indicadores X e Y ocorrerem, você DEVE autorizar.
Exemplo JSON: {{"regra": "Se RSI < 30 e Tendência for BAIXA, autorizar PUT"}}
"""
            else: # PROCEED_LOSS
                prompt_groq = f"""
Analise este erro de PROCEED_LOSS (Prejuízo Real).
Você autorizou {sinal} e o mercado foi contra.
Dados: RSI={rsi:.2f}, Tendência={tendencia}, Candle={corpo_candle:.5f}, DistSMA={dist_sma:.5f}.
Defina uma NOVA REGRA TÉCNICA para corrigir essa falha.
A regra deve definir uma condição MAIS ESTRITA para autorizar {sinal} ou autorizar o movimento oposto se for o caso.
Foco: EXPOSIÇÃO POSITIVA (Autorizar o certo).
Retorne APENAS JSON: {{"regra": "Se RSI > X e ... autorizar ..."}}
"""

            try:
                print(f"⚖️ IA Aluna: Consultando Tribunal (Groq) sobre {tipo_erro}...")
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt_groq}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.3,
                )
                response = chat_completion.choices[0].message.content
                
                import json
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = response[start:end]
                    data = json.loads(json_str)
                    nova_regra = data.get("regra", "").strip()
                    
                    if nova_regra:
                        with self._lock:
                            self.regras_dinamicas.append(nova_regra)
                            with open(self.arquivo_regras, "a", encoding="utf-8") as f:
                                f.write(f"{nova_regra}\n")
                        self.regra_atual = nova_regra
                        print(f"🦁 IA Aluna (Groq): Nova Regra Aprendida -> {nova_regra}")
                return
            except Exception as e:
                print(f"🚨 Erro no Tribunal Groq: {e}")
                return

        prompt_reflexao = f"""
Analise o erro: {tipo_erro} em {sinal}.
Dados: RSI={rsi:.2f}, Tendência={tendencia}, Dist={dist_sma:.4f}.
Histórico: {hist_str}

"""
        # --- SUPERVISOR DE VIES (FILTRO DE SANIDADE) ---
        if tipo_erro == "MISSED_WIN":
            if (sinal == "CALL" and rsi < 40) or (sinal == "PUT" and rsi > 60):
                alerta_covardia = "ALERTA DE COVARDIA: O bloqueio foi contra indicadores óbvios (RSI em zona de reversão). Crie uma regra AGRESSIVA para autorizar a operação em cenários similares. PROCEED é a prioridade."
                prompt_reflexao += f"\nAVISO DO SUPERVISOR: {alerta_covardia}\n"

        prompt_reflexao += """
Crie uma regra técnica CURTA para evitar este erro.
Formato: "Se RSI < X e ... autorizar ..."
NÃO explique. Apenas a regra.
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
            with self._ollama_lock:
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