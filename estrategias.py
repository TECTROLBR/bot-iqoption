import copy

class GerenteEstrategia:
    def __init__(self):
        self.global_wins = 0 # Placar Geral da Sessão
        self.global_loss = 0 # Placar Geral da Sessão
        self.min_assertividade = 0 # Assertividade mínima para operar (IA decide)
        self.config_tendencia = {"periodo": 20}  # Configuração global de tendência (SMA)
        # Estrutura para armazenar o estado de cada estratégia
        self.estrategias = {
            "3_Outside_Down": {
                "nome": "3 Por Fora de Baixa",
                "status": "idle",  # idle, waiting, active
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Three_Black_Crows": {
                "nome": "Três Corvos Pretos",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Three_White_Soldiers": {
                "nome": "Três Soldados Brancos",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Three_Inside_Up": {
                "nome": "3 Inside Up",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Bullish_Abandoned_Baby": {
                "nome": "Bebê Abandonado de Alta",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Bearish_Abandoned_Baby": {
                "nome": "Bebê Abandonado de Baixa",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Momentum": {
                "nome": "Candle de Força",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0,
                "direction": None # CALL ou PUT
            },
            "Bullish_Kicker": {
                "nome": "Chute de Alta",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Bearish_Kicker": {
                "nome": "Chute de Baixa",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Short_Day": {
                "nome": "Dia Curto (Filtro)",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Long_Day": {
                "nome": "Dia Longo",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0,
                "direction": None
            },
            "Doji_Standard": {
                "nome": "Doji (Indecisão)",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Dragonfly_Doji": {
                "nome": "Doji Libélula",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Gravestone_Doji": {
                "nome": "Doji Lápide",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "High_Wave": {
                "nome": "High Wave (Volatilidade)",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Morning_Star": {
                "nome": "Estrela da Manhã",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Evening_Star": {
                "nome": "Estrela da Noite",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Bullish_Engulfing": {
                "nome": "Engolfo de Alta",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Bearish_Engulfing": {
                "nome": "Engolfo de Baixa",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Shooting_Star": {
                "nome": "Estrela Cadente",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Hammer": {
                "nome": "Martelo",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Upside_Tasuki": {
                "nome": "Tasuki de Alta",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Downside_Tasuki": {
                "nome": "Tasuki de Baixa",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Hanging_Man": {
                "nome": "Homem Enforcado",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Inverted_Hammer": {
                "nome": "Martelo Invertido",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Marubozu": {
                "nome": "Marubozu",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0,
                "direction": None
            },
            "Harami": {
                "nome": "Harami",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0,
                "direction": None
            },
            "Dark_Cloud_Cover": {
                "nome": "Nuvem Negra",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Piercing_Line": {
                "nome": "Piercing Line",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Rising_Three_Methods": {
                "nome": "Rising Three Methods",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Falling_Three_Methods": {
                "nome": "Falling Three Methods",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Spinning_Top": {
                "nome": "Peão (Filtro)",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Tweezers_Top": {
                "nome": "Pinça de Topo",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Tweezers_Bottom": {
                "nome": "Pinça de Fundo",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Three_Line_Strike_Bull": {
                "nome": "Strike de Alta (Rev)",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            },
            "Stick_Sandwich": {
                "nome": "Vela Prensada",
                "status": "idle",
                "wins": 0,
                "loss": 0,
                "entry_price": 0
            }
        }

        # Inicializa configurações padrão para todas as estratégias (Conceito Camaleão)
        for k in self.estrategias:
            # Define o caminho da imagem local baseada na chave da estratégia
            self.estrategias[k]["id"] = k # Identificador único para o Analista
            
            self.estrategias[k]["config"] = {
                "min_body": 1.0,   # Multiplicador Mínimo da Média de Corpos
                "max_body": 4.0,   # Multiplicador Máximo (Exaustão)
                "max_wick": 0.2,   # Tamanho máximo do pavio (20% do corpo)
                "use_trend": False, # Se deve respeitar a tendência global
                "use_rsi": False,   # Filtro de RSI (Sobrecompra/Sobrevenda)
                "use_sr": False,    # Filtro de Suporte e Resistência
                "use_bb": False,    # Filtro de Bollinger Bands
                "use_m5": False,    # Filtro de Tendência M5 (Multitemporal)
                "expiration": 1,   # Tempo de expiração em minutos (Padrão)
                "use_volume": False, # Filtro de Volume (Fluxo)
                "trend_period": 20 # Período da Média Móvel específico desta estratégia
            }
            # Inicializa contadores totais
            self.estrategias[k]["total_wins"] = 0
            self.estrategias[k]["total_loss"] = 0
            self.estrategias[k]["ultimo_contexto"] = {} # Armazena dados para o Analista
            self.estrategias[k]["contexto_ml"] = {} # Armazena dados para o Treinamento da IA Local
            self.estrategias[k]["expiration_count"] = 0 # Contador para expiração multi-vela
        
        # --- PERSONALIZAÇÃO DOS PADRÕES (Restaurando lógica original) ---
        
        # 1. Dia Longo: Originalmente 1.5x a 3.5x, Trend ON
        self.estrategias["Long_Day"]["config"].update({
            "min_body": 1.5, "max_body": 3.5, "use_trend": True, "max_wick": 0.2
        })

        # 2. Momentum (Candle de Força): Originalmente 2.0x a 4.0x, Pavio < 10%, Trend ON
        self.estrategias["Momentum"]["config"].update({
            "min_body": 2.0, "max_body": 4.0, "use_trend": True, "max_wick": 0.1
        })

        # 3. Dia Curto (Filtro): Originalmente < 0.5x, Pavio < 100% (1.0)
        # Nota: min_body 0.0 pois só importa o teto
        self.estrategias["Short_Day"]["config"].update({
            "min_body": 0.0, "max_body": 0.5, "use_trend": False, "max_wick": 1.0
        })
        
        # Carrega estatísticas salvas (Histórico Vitalício)
        self.carregar_stats()

    def carregar_stats(self):
        import json
        import os
        if os.path.exists("estatisticas.json"):
            try:
                with open("estatisticas.json", "r") as f:
                    dados = json.load(f)
                    
                    # Carrega Config Global (Tendência)
                    if "_global_config" in dados:
                        self.config_tendencia = dados["_global_config"]
                    
                    self.min_assertividade = dados.get("_global_assertividade", 60)

                    for nome, stats in dados.items():
                        if nome in self.estrategias:
                            self.estrategias[nome]["total_wins"] = stats.get("wins", 0)
                            self.estrategias[nome]["total_loss"] = stats.get("loss", 0)
                            # Carrega Configurações da Estratégia
                            if "config" in stats:
                                self.estrategias[nome]["config"].update(stats["config"])
            except Exception as e:
                print(f"Erro ao carregar estatísticas: {e}")

    def salvar_stats(self):
        import json
        dados = {k: {"wins": v.get("total_wins", 0), "loss": v.get("total_loss", 0), "config": v.get("config", {})} 
                 for k, v in self.estrategias.items()}
        dados["_global_config"] = self.config_tendencia
        dados["_global_assertividade"] = self.min_assertividade
        try:
            with open("estatisticas.json", "w") as f:
                json.dump(dados, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar estatísticas: {e}")

    def resetar_para_padrao(self):
        """Reseta todas as configurações e estatísticas para o padrão de fábrica."""
        print("--- RESETANDO ESTRATÉGIAS PARA O PADRÃO ---")
        
        # 1. Reseta Configurações Globais
        self.min_assertividade = 60
        self.config_tendencia = {"periodo": 20}
        self.global_wins = 0
        self.global_loss = 0

        # 2. Reseta cada estratégia
        for k in self.estrategias:
            self.estrategias[k]["config"] = {
                "min_body": 1.0, "max_body": 4.0, "max_wick": 0.2,
                "use_trend": False, "use_rsi": False, "use_sr": False,
                "use_bb": False, "use_m5": False, "expiration": 1,
                "use_volume": False, "trend_period": 20
            }
            # Zera histórico
            self.estrategias[k]["total_wins"] = 0
            self.estrategias[k]["total_loss"] = 0
            self.estrategias[k]["wins"] = 0
            self.estrategias[k]["loss"] = 0
            self.estrategias[k]["status"] = "idle"

        # 3. Re-aplica personalizações específicas (Hardcoded)
        if "Long_Day" in self.estrategias:
            self.estrategias["Long_Day"]["config"].update({
                "min_body": 1.5, "max_body": 3.5, "use_trend": True, "max_wick": 0.2
            })
        if "Momentum" in self.estrategias:
            self.estrategias["Momentum"]["config"].update({
                "min_body": 2.0, "max_body": 4.0, "use_trend": True, "max_wick": 0.1
            })
        if "Short_Day" in self.estrategias:
            self.estrategias["Short_Day"]["config"].update({
                "min_body": 0.0, "max_body": 0.5, "use_trend": False, "max_wick": 1.0
            })

        self.salvar_stats()

    def registrar_win(self, st, info="", atualizar_global=True):
        st["wins"] += 1
        st["total_wins"] = st.get("total_wins", 0) + 1
        if atualizar_global:
            self.global_wins += 1 # Incrementa placar geral
        self.salvar_stats()
        # Notifica o Analista imediatamente
        # Win não precisa de ajuste imediato, time que ganha não se mexe (por enquanto)
        msg = f"WIN na estratégia {st['nome']}"
        if info: msg += f" ({info})"
        print(msg)

    def registrar_loss(self, st, info="", atualizar_global=True, historico=None):
        st["loss"] += 1
        st["total_loss"] = st.get("total_loss", 0) + 1
        if atualizar_global:
            self.global_loss += 1 # Incrementa placar geral
        self.salvar_stats()
        # Notifica o Analista imediatamente
        msg = f"LOSS na estratégia {st['nome']}"
        if info: msg += f" ({info})"
        print(msg)

    def ativar_estrategia(self, nome_estrategia):
        """Marca a estratégia como ativa (Operando)"""
        if nome_estrategia in self.estrategias:
            self.estrategias[nome_estrategia]["status"] = "active"

    def processar_resultado_votacao(self, estrategias_vencedoras):
        """
        Atualiza o status das estratégias após a votação.
        Vencedoras -> 'active'
        Perdedoras (que estavam 'waiting') -> 'idle'
        """
        vencedoras_set = set(estrategias_vencedoras) if estrategias_vencedoras else set()
        
        for nome, st in self.estrategias.items():
            if st["status"] == "waiting":
                if nome in vencedoras_set:
                    st["status"] = "active"
                else:
                    st["status"] = "idle"

    def notificar_resultado_api(self, nome_estrategia, win, lucro):
        """Recebe o resultado oficial da API e atualiza estatísticas/Analista"""
        # Lógica desativada para usar contagem simplificada por cor de vela (Solicitação do usuário)
        pass
        # if nome_estrategia in self.estrategias:
        #     st = self.estrategias[nome_estrategia]
        #     if win:
        #         self.registrar_win(st, f"API: {lucro}")
        #     else:
        #         self.registrar_loss(st, f"API: {lucro}")
        #     # Libera a estratégia para operar novamente
        #     st["status"] = "idle"

    def resetar(self):
        """Reseta os estados ao trocar de ativo"""
        for chave in self.estrategias:
            self.estrategias[chave]["status"] = "idle"
            self.estrategias[chave]["entry_price"] = 0
            # Nota: Não resetamos wins/loss para manter o histórico da sessão

    def detectar_tendencia(self, historico, periodo=None):
        """Calcula a tendência baseada na SMA (Simple Moving Average)"""
        if periodo is None:
            periodo = self.config_tendencia["periodo"]
            
        if len(historico) < periodo:
            return "INDETERMINADO"
        
        # Pega os fechamentos das últimas X velas
        fechamentos = [v['close'] for v in historico[-periodo:]]
        media = sum(fechamentos) / periodo
        preco_atual = historico[-1]['close']
        
        if preco_atual > media:
            return "ALTA"
        elif preco_atual < media:
            return "BAIXA"
        return "LATERAL"

    def calcular_rsi(self, historico, periodo=14):
        """Calcula o RSI (Relative Strength Index)"""
        if len(historico) < periodo + 1:
            return 50 # Neutro se não tiver dados
        
        ganhos = 0
        perdas = 0
        
        # CORREÇÃO: O RSI deve usar a variação entre fechamentos (Close - PrevClose)
        # Pega as velas necessárias (periodo + 1 para calcular variações)
        fatia = historico[-(periodo+1):]
        
        for i in range(1, len(fatia)):
            diff = fatia[i]['close'] - fatia[i-1]['close']
            if diff > 0: ganhos += diff
            else: perdas += abs(diff)
            
        if perdas == 0: return 100
        
        rs = ganhos / perdas
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calcular_atr(self, historico, periodo=14):
        """Calcula o Average True Range (Volatilidade Real)"""
        if len(historico) < periodo + 1:
            return 0.0
        
        tr_sum = 0.0
        # Pega as velas necessárias (periodo + 1 para calcular variações)
        fatia = historico[-(periodo+1):]
        
        for i in range(1, len(fatia)):
            atual = fatia[i]
            anterior = fatia[i-1]
            
            hl = atual['max'] - atual['min']
            hc = abs(atual['max'] - anterior['close'])
            lc = abs(atual['min'] - anterior['close'])
            
            tr = max(hl, hc, lc)
            tr_sum += tr
            
        return tr_sum / periodo

    def calcular_suporte_resistencia(self, historico, periodo=50):
        """Identifica zonas de S/R baseadas em máximas e mínimas recentes"""
        if len(historico) < periodo:
            return {"suporte": 0, "resistencia": float('inf')}
            
        fatia = historico[-periodo:]
        maxima = max(v['max'] for v in fatia)
        minima = min(v['min'] for v in fatia)
        
        return {"suporte": minima, "resistencia": maxima}

    def calcular_media_volume(self, historico, periodo=20):
        """Calcula a média de volume das últimas velas"""
        if len(historico) < periodo: return 0
        vols = [v['volume'] for v in historico[-periodo:]]
        return sum(vols) / len(vols)

    def calcular_bollinger(self, historico, periodo=20, desvio=2):
        """Calcula Bandas de Bollinger (SMA 20 +/- 2 StdDev)"""
        if len(historico) < periodo:
            return None
        
        fechamentos = [v['close'] for v in historico[-periodo:]]
        sma = sum(fechamentos) / periodo
        
        # Variância e Desvio Padrão
        variancia = sum((x - sma) ** 2 for x in fechamentos) / periodo
        std_dev = variancia ** 0.5
        
        upper = sma + (desvio * std_dev)
        lower = sma - (desvio * std_dev)
        
        return {"upper": upper, "lower": lower, "sma": sma, "bandwidth": upper - lower}

    def calcular_tendencia_m5(self, historico_m1):
        """Simula tendência de M5 agregando velas de M1 (Multitemporal)"""
        if len(historico_m1) < 100: # Precisa de histórico razoável
            return "INDETERMINADO"
            
        velas_m5 = []
        # Pega os últimos 100 minutos
        recentes = list(historico_m1)[-100:]
        
        # Agrega de 5 em 5
        for i in range(0, len(recentes), 5):
            chunk = recentes[i:i+5]
            if chunk: velas_m5.append({"close": chunk[-1]['close']})
            
        return self.detectar_tendencia(velas_m5, periodo=20)

    def analisar_contexto(self, historico):
        """Calcula métricas de contexto: Média Móvel 20 e Média dos Corpos"""
        periodo = self.config_tendencia["periodo"]
        
        if len(historico) < periodo: 
            return {"tendencia": "neutra", "media_corpos": 0, "media_20": 0}
        
        fechamentos = [v['close'] for v in list(historico)[-periodo:]]
        media_20 = sum(fechamentos) / periodo
        
        corpos = [abs(v['open'] - v['close']) for v in list(historico)[-10:]]
        media_corpos = sum(corpos) / 10 if corpos else 0
        
        # Novos Indicadores
        rsi = self.calcular_rsi(historico)
        sr = self.calcular_suporte_resistencia(historico)
        vol_med = self.calcular_media_volume(historico)
        bb = self.calcular_bollinger(historico)
        trend_m5 = self.calcular_tendencia_m5(historico)
        atr = self.calcular_atr(historico) # Sensor de Volatilidade
        
        return {
            "media_20": media_20,
            "media_corpos": media_corpos,
            "tendencia": "ALTA" if historico[-1]['close'] > media_20 else "BAIXA",
            "rsi": rsi,
            "sr": sr,
            "vol_medio": vol_med,
            "bb": bb,
            "tendencia_m5": trend_m5,
            "atr": atr,
            "close": historico[-1]['close'],
            "volume": historico[-1]['volume']
        }

    def validar_filtros(self, vela, config, contexto, tendencia_requerida=None, tendencia_especifica=None):
        """
        Validação unificada:
        AGORA: Retorna True para deixar a IA decidir (Filtros matemáticos removidos).
        """
        return True

    def processar(self, historico, simulacao=False):
        """
        Analisa o histórico de velas em busca de padrões.
        Estratégia implementada: 3 Por Fora de Baixa (Three Outside Down)
        """
        sinais = []
        resultados_finalizados = []
        if len(historico) < 6: # Aumentado para garantir histórico para filtros
            return sinais, {}, resultados_finalizados
            
        # --- LÓGICA DE CONTABILIZAÇÃO SIMPLIFICADA ---
        # Verifica estratégias que operaram na vela anterior e define Win/Loss pela cor da vela atual.
        v_atual = historico[-1]
        
        # Flag para garantir que o placar GERAL só seja incrementado uma vez por vela (evita duplicação em consensos)
        placar_movimentado = False
        
        for nome, st in self.estrategias.items():
            if st["status"] == "active":
                # Decrementa contador de expiração (se for > 1, aguarda próximas velas)
                if st.get("expiration_count", 0) > 1:
                    st["expiration_count"] -= 1
                    continue

                direction = st.get("direction")
                if direction:
                    win = False
                    # CALL: Win se a vela fechou Verde (Close > Open)
                    if direction == "CALL" and v_atual['close'] > v_atual['open']:
                        win = True
                    # PUT: Win se a vela fechou Vermelha (Close < Open)
                    elif direction == "PUT" and v_atual['close'] < v_atual['open']:
                        win = True
                    
                    # Define se deve atualizar o placar global (apenas o primeiro da lista atualiza)
                    atualizar_global = not placar_movimentado
                    
                    if win:
                        self.registrar_win(st, "Vela a favor", atualizar_global and not simulacao)
                        if atualizar_global and not simulacao:
                            placar_movimentado = True
                        resultados_finalizados.append({"contexto": st['ultimo_contexto'], "resultado": "WIN", "contexto_ml": st.get('contexto_ml', {})})
                    else:
                        # Passa o histórico para o analista poder rodar o backtest
                        self.registrar_loss(st, "Vela contra", atualizar_global and not simulacao, historico=historico)
                        if atualizar_global and not simulacao:
                            placar_movimentado = True
                        resultados_finalizados.append({"contexto": st['ultimo_contexto'], "resultado": "LOSS", "contexto_ml": st.get('contexto_ml', {})})
                
                # Reseta o status para idle e limpa direção
                st["status"] = "idle"
                st["direction"] = None

        # Helper para calcular tendência específica da estratégia
        def get_trend(st_obj):
            return self.detectar_tendencia(historico, st_obj["config"].get("trend_period", 20))

        # Função auxiliar para adicionar sinal com o tempo de expiração configurado
        def add_sinal(st_obj, direcao):
            # --- FILTRO RSI (GLOBAL PER CONFIG) ---
            if st_obj["config"].get("use_rsi", False):
                rsi_val = ctx.get("rsi", 50)
                # Impede compra se RSI > 70 (Sobrecomprado - fim da festa de alta)
                if direcao == "CALL" and rsi_val > 70:
                    if not simulacao: print(f"⛔ {st_obj['nome']} (CALL) bloqueado por RSI alto ({rsi_val:.1f}).")
                    return
                # Impede venda se RSI < 30 (Sobrevendido - fim da festa de baixa)
                if direcao == "PUT" and rsi_val < 30:
                    if not simulacao: print(f"⛔ {st_obj['nome']} (PUT) bloqueado por RSI baixo ({rsi_val:.1f}).")
                    return

            # Adiciona o sinal à lista de votação sem restrições (IA decide depois)
            exp = st_obj["config"].get("expiration", 1)
            sinais.append({"sinal": direcao, "expiracao": exp, "nome": st_obj["nome"], "id": st_obj["id"]})
            if not simulacao: print(f"🗳️ VOTO REGISTRADO: {st_obj['nome']} votou {direcao}.")
            
            # A estratégia fica "ativa" para registrar o resultado (win/loss) independentemente de ter votado ou não.
            st_obj["status"] = "active"
            st_obj["direction"] = direcao
            
            # Define contador de expiração (Mínimo 1 vela)
            exp_val = st_obj["config"].get("expiration", 1)
            st_obj["expiration_count"] = int(exp_val) if exp_val >= 1 else 1
            
            # --- SNAPSHOT PARA O ANALISTA ---
            # Salva o contexto ATUAL (Tendência, Volume, etc) dentro da estratégia.
            # Se der Loss, o Analista vai ler isso aqui para saber "o que estava acontecendo" quando entrou.
            st_obj["ultimo_contexto"] = {
                "sinal": direcao,
                "tendencia": tendencia_atual,
                "media_corpos": ctx["media_corpos"],
                "corpo_vela": abs(historico[-1]['open'] - historico[-1]['close'])
            }

        # --- 3. CHECK DE VELOCIDADE & TENDÊNCIA ESTÁVEL ---
        # Pré-calcula a tendência global usando 50 velas para evitar "ruído" (mudanças bruscas)
        # CORREÇÃO: Unificação da tendência para evitar "esquizofrenia" (usa config padrão, ex: 20)
        # Mantemos a global apenas para referência do contexto geral, mas cada estratégia calculará a sua.
        tendencia_global_ctx = self.detectar_tendencia(historico)
        tendencia_atual = tendencia_global_ctx # Fallback para estratégias antigas/simples
        
        # Analisa contexto (Média de corpos) para uso global nos filtros
        ctx = self.analisar_contexto(historico)

        # --- FILTROS DE BLOQUEIO (ESTRATÉGIAS 10, 12 e 15) ---
        # Verifica se o mercado está com baixa volatilidade antes de processar entradas
        mercado_parado = False
        if len(historico) >= 6:
            v_atual = historico[-1]
            corpo = abs(v_atual['open'] - v_atual['close'])
            amplitude = v_atual['max'] - v_atual['min']
            
            # Média dos corpos das 5 velas anteriores (excluindo a atual)
            media_corpos = sum(abs(v['open'] - v['close']) for v in historico[-6:-1]) / 5
            
            # 10. Dia Curto (Short Day)
            if "Short_Day" in self.estrategias:
                st_short = self.estrategias["Short_Day"]
                cfg_short = st_short["config"]
                pavio_total = (v_atual['max'] - v_atual['min']) - corpo
                
                # Usa max_body (ex: 0.5) e max_wick (ex: 1.0 = 100%)
                if media_corpos > 0 and corpo < (media_corpos * cfg_short["max_body"]) and pavio_total < (corpo * cfg_short["max_wick"]):
                    st_short["status"] = "waiting"
                    # mercado_parado = True # Desativado: Deixa a IA decidir
                    if not simulacao: print(f"ALERTA: {st_short['nome']} detectado. Baixa volatilidade.")
                else:
                    st_short["status"] = "idle"

            # 12. Doji Padrão (Indecisão)
            if "Doji_Standard" in self.estrategias:
                st_doji = self.estrategias["Doji_Standard"]
                # Regra: Corpo <= 5% da amplitude total
                if amplitude > 0 and corpo <= (amplitude * 0.05):
                    st_doji["status"] = "waiting"
                    # mercado_parado = True # Desativado: Deixa a IA decidir
                    if not simulacao: print(f"ALERTA: {st_doji['nome']} detectado. Mercado indeciso.")
                else:
                    st_doji["status"] = "idle"

            # 15. High Wave (Sombras Longas - Alta Volatilidade sem direção)
            if "High_Wave" in self.estrategias:
                st_high = self.estrategias["High_Wave"]
                # Sombras
                sombra_sup = v_atual['max'] - max(v_atual['open'], v_atual['close'])
                sombra_inf = min(v_atual['open'], v_atual['close']) - v_atual['min']
                
                # Regra: Corpo pequeno (< 50% média) E Sombras > 2x Corpo
                # Nota: Se corpo for 0, qualquer sombra ativa, então adicionamos verificação de amplitude mínima
                if media_corpos > 0 and corpo < (media_corpos * 0.5) and \
                   sombra_sup > (corpo * 2) and sombra_inf > (corpo * 2):
                    st_high["status"] = "waiting"
                    # mercado_parado = True # Desativado: Deixa a IA decidir
                    if not simulacao: print(f"ALERTA: {st_high['nome']} detectado. Mercado 'louco'.")
                else:
                    st_high["status"] = "idle"

            # 36 e 40. Peão (Spinning Top) - Filtro
            if "Spinning_Top" in self.estrategias:
                st_spin = self.estrategias["Spinning_Top"]
                # Corpo pequeno (mas maior que Doji) e sombras presentes
                if media_corpos > 0 and corpo < (media_corpos * 0.5) and corpo > (amplitude * 0.05):
                    st_spin["status"] = "waiting"
                    # mercado_parado = True # Desativado: Deixa a IA decidir
                    if not simulacao: print(f"ALERTA: {st_spin['nome']} detectado. Indecisão.")
                else:
                    st_spin["status"] = "idle"

        # -----------------------------------------------------------
        # ESTRATÉGIA 1: 3 OUTSIDE DOWN
        # -----------------------------------------------------------

        # Dados da estratégia
        if "3_Outside_Down" in self.estrategias:
            st = self.estrategias["3_Outside_Down"]
            
            # Última vela fechada (que acabou de acontecer)
            v_atual = historico[-1]
            # Vela anterior a ela
            v_anterior = historico[-2]

            # --- LÓGICA DE CONFIRMAÇÃO (Se estava esperando) ---
            if st["status"] == "waiting":
                # Precisa ser vermelha e fechar abaixo da anterior (que era a do engolfo)
                is_red = v_atual['close'] < v_atual['open']
                continues_down = v_atual['close'] < v_anterior['close']
                
                if is_red and continues_down:
                    st["entry_price"] = v_atual['close']
                    if not simulacao: print(f"CONFIRMADO: {st['nome']} -> VENDIDO em {st['entry_price']}")
                    add_sinal(st, "PUT") # Sinal para o bot
                else:
                    # Falhou a confirmação, volta para idle
                    st["status"] = "idle"
                    if not simulacao: print(f"Cancelado: {st['nome']} não confirmou.")

            # --- LÓGICA DE SETUP (Se está livre) ---
            if st["status"] == "idle" and not mercado_parado:
                # Verifica Engolfo de Baixa nas duas últimas velas (v_anterior e v_atual)
                v1_verde = v_anterior['close'] > v_anterior['open']
                v2_vermelha = v_atual['close'] < v_atual['open']
                
                # Engolfo: v2 abre acima/igual v1 fecha E v2 fecha abaixo v1 abre
                engolfo = (v_atual['open'] >= v_anterior['close']) and (v_atual['close'] < v_anterior['open'])
                
                if v1_verde and v2_vermelha and engolfo:
                    st["status"] = "waiting"
                    if not simulacao: print(f"SETUP: {st['nome']} identificado. Aguardando confirmação...")

        # -----------------------------------------------------------
        # ESTRATÉGIA 2: TRÊS CORVOS PRETOS (Three Black Crows)
        # -----------------------------------------------------------
        if len(historico) >= 3 and "Three_Black_Crows" in self.estrategias:
            st_crows = self.estrategias["Three_Black_Crows"]
            t_crows = get_trend(st_crows)
            
            # --- LÓGICA DE SETUP (Se está livre) ---
            # Requer Tendência de BAIXA (Continuação)
            if st_crows["status"] == "idle" and not mercado_parado:
                v1 = historico[-3]
                v2 = historico[-2]
                v3 = historico[-1] # Vela recém fechada

                # 1. Cor das Velas (As 3 devem ser vermelhas)
                todas_vermelhas = (v1['close'] < v1['open']) and \
                                  (v2['close'] < v2['open']) and \
                                  (v3['close'] < v3['open'])

                # 2. O Fechamento (Abaixo da mínima anterior)
                fechamentos_baixos = (v2['close'] < v1['min']) and (v3['close'] < v2['min'])

                # 3. O Início (Alinhado com o corpo anterior - sem gap excessivo)
                aberturas_alinhadas = (v1['open'] > v2['open'] > v1['close']) and \
                                      (v2['open'] > v3['open'] > v2['close'])

                # 4. Filtros Unificados (Tendência + Força Dinâmica)
                # Verifica se as 3 velas respeitam o tamanho mínimo configurado e a tendência
                filtros_ok = self.validar_filtros(v1, st_crows["config"], ctx, "BAIXA", t_crows) and \
                             self.validar_filtros(v2, st_crows["config"], ctx, "BAIXA", t_crows) and \
                             self.validar_filtros(v3, st_crows["config"], ctx, "BAIXA", t_crows)

                if todas_vermelhas and fechamentos_baixos and aberturas_alinhadas and filtros_ok:
                    st_crows["entry_price"] = v3['close']
                    if not simulacao: print(f"PADRÃO: {st_crows['nome']} IDENTIFICADO. CONFIABILIDADE ALTA. VENDER!")
                    add_sinal(st_crows, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 3: TRÊS SOLDADOS BRANCOS (Three White Soldiers)
        # -----------------------------------------------------------
        if len(historico) >= 3 and "Three_White_Soldiers" in self.estrategias:
            st_soldiers = self.estrategias["Three_White_Soldiers"]
            t_soldiers = get_trend(st_soldiers)
            
            # --- LÓGICA DE SETUP (Se está livre) ---
            # Requer Tendência de ALTA (Continuação)
            if st_soldiers["status"] == "idle" and not mercado_parado:
                v1 = historico[-3]
                v2 = historico[-2]
                v3 = historico[-1] # Vela recém fechada

                # 1. Cor das Velas (As 3 devem ser verdes)
                todas_verdes = (v1['close'] > v1['open']) and \
                               (v2['close'] > v2['open']) and \
                               (v3['close'] > v3['open'])

                # 2. O Fechamento (Acima da máxima anterior - subindo escada)
                fechamentos_altos = (v2['close'] > v1['max']) and (v3['close'] > v2['max'])

                # 3. O Início (Alinhado com o corpo anterior - abre dentro do corpo da anterior)
                # Como são verdes (Open < Close), a abertura da próxima deve estar entre Open e Close da anterior.
                aberturas_alinhadas = (v1['open'] < v2['open'] < v1['close']) and \
                                      (v2['open'] < v3['open'] < v2['close'])

                # 4. Filtros Unificados (Tendência + Força Dinâmica)
                # Substitui o is_strong antigo e aplica a config da interface
                filtros_ok = self.validar_filtros(v1, st_soldiers["config"], ctx, "ALTA", t_soldiers) and \
                             self.validar_filtros(v2, st_soldiers["config"], ctx, "ALTA", t_soldiers) and \
                             self.validar_filtros(v3, st_soldiers["config"], ctx, "ALTA", t_soldiers)

                if todas_verdes and fechamentos_altos and aberturas_alinhadas and filtros_ok:
                    st_soldiers["entry_price"] = v3['close']
                    if not simulacao: print(f"PADRÃO: {st_soldiers['nome']} IDENTIFICADO. CONFIABILIDADE ALTA. COMPRAR!")
                    add_sinal(st_soldiers, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 4: 3 INSIDE UP
        # -----------------------------------------------------------
        if len(historico) >= 3 and "Three_Inside_Up" in self.estrategias:
            st_inside = self.estrategias["Three_Inside_Up"]
            
            # --- LÓGICA DE SETUP (Se está livre) ---
            if st_inside["status"] == "idle" and not mercado_parado:
                v1 = historico[-3] # A Mãe (Vermelha Grande)
                v2 = historico[-2] # O Bebê (Harami)
                v3 = historico[-1] # A Confirmação (Estopim)

                # Passo 1: Identificar o Harami (Vela 2 dentro da Vela 1)
                # v1 deve ser vermelha, v2 verde e contida no corpo da v1
                eh_harami = (v1['close'] < v1['open']) and \
                            (v2['close'] > v2['open']) and \
                            (v2['open'] > v1['close']) and \
                            (v2['close'] < v1['open'])

                # Passo 2: Confirmar o rompimento da Vela 3
                # v3 deve ser verde e fechar acima da abertura da v1 (rompendo o topo do padrão)
                confirmado = (v3['close'] > v3['open']) and \
                             (v3['close'] > v1['open'])

                if eh_harami and confirmado:
                    st_inside["entry_price"] = v3['close']
                    if not simulacao: print(f"PADRÃO: {st_inside['nome']} IDENTIFICADO. TENDÊNCIA DE ALTA CONFIRMADA. COMPRAR!")
                    add_sinal(st_inside, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 5: BEBÊ ABANDONADO DE ALTA (Bullish Abandoned Baby)
        # -----------------------------------------------------------
        if len(historico) >= 3 and "Bullish_Abandoned_Baby" in self.estrategias:
            st_baby = self.estrategias["Bullish_Abandoned_Baby"]
            t_baby = get_trend(st_baby)
            
            # --- LÓGICA DE SETUP (Se está livre) ---
            # Requer Tendência de BAIXA (Reversão para Alta)
            if st_baby["status"] == "idle" and not mercado_parado and t_baby == "BAIXA":
                v1 = historico[-3] # Vela de Baixa
                v2 = historico[-2] # Bebê (Doji)
                v3 = historico[-1] # Vela de Alta

                # 1. A Descida (Vela 1) - Vermelha forte
                v1_baixa = v1['close'] < v1['open']

                # 2. O Gap de Baixa (V1 para V2)
                # Máxima da V2 menor que Mínima da V1 (Ilha isolada abaixo)
                gap_descida = v2['max'] < v1['min']

                # 3. O Bebê (Vela 2 - Indecisão/Doji)
                # Corpo menor que 10% da amplitude total
                amplitude_v2 = v2['max'] - v2['min']
                corpo_v2 = abs(v2['open'] - v2['close'])
                # Se amplitude for 0, é um doji perfeito, senão calcula a %
                eh_doji = (corpo_v2 < (amplitude_v2 * 0.1)) if amplitude_v2 > 0 else True

                # 4. O Gap de Alta e a Retomada (Vela 3)
                # Mínima da V3 maior que Máxima da V2 (Salto para cima)
                gap_subida = v3['min'] > v2['max']
                vela_alta = v3['close'] > v3['open']

                if v1_baixa and gap_descida and eh_doji and gap_subida and vela_alta:
                    st_baby["entry_price"] = v3['close']
                    if not simulacao: print(f"PADRÃO RARO: {st_baby['nome']} IDENTIFICADO. COMPRAR!")
                    add_sinal(st_baby, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 5 (NOVA): BEBÊ ABANDONADO DE BAIXA
        # -----------------------------------------------------------
        if len(historico) >= 3 and "Bearish_Abandoned_Baby" in self.estrategias:
            st_bear_baby = self.estrategias["Bearish_Abandoned_Baby"]
            t_bear_baby = get_trend(st_bear_baby)
            
            # Requer Tendência de ALTA (Reversão para Baixa)
            if st_bear_baby["status"] == "idle" and not mercado_parado and t_bear_baby == "ALTA":
                v1 = historico[-3] # Vela Verde
                v2 = historico[-2] # Doji/Peão
                v3 = historico[-1] # Vela Vermelha

                # 1. Vela 1 (Verde)
                v1_verde = v1['close'] > v1['open']

                # 2. Gap de Alta (V2 acima de V1)
                gap_alta = v2['min'] > v1['max']

                # 3. Vela 2 (Doji/Peão - Corpo pequeno)
                amplitude_v2 = v2['max'] - v2['min']
                corpo_v2 = abs(v2['open'] - v2['close'])
                eh_doji = (corpo_v2 < (amplitude_v2 * 0.1)) if amplitude_v2 > 0 else True

                # 4. Gap de Baixa (V2 acima de V3)
                gap_baixa = v2['min'] > v3['max']

                # 5. Vela 3 (Vermelha)
                v3_vermelha = v3['close'] < v3['open']

                if v1_verde and gap_alta and eh_doji and gap_baixa and v3_vermelha:
                    st_bear_baby["entry_price"] = v3['close']
                    if not simulacao: print(f"PADRÃO: {st_bear_baby['nome']} IDENTIFICADO. VENDER!")
                    add_sinal(st_bear_baby, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 6 e 7: CANDLES DE FORÇA (MOMENTUM)
        # -----------------------------------------------------------
        if len(historico) >= 6 and "Momentum" in self.estrategias:
            st_mom = self.estrategias["Momentum"]
            cfg = st_mom["config"] # Carrega configuração dinâmica
            t_mom = get_trend(st_mom)
            
            # Lógica Melhorada com Filtros de Contexto
            if st_mom["status"] == "idle" and not mercado_parado:
                
                v_atual = historico[-1]
                corpo_atual = abs(v_atual['open'] - v_atual['close'])

                # 1. Filtro de Tamanho (Dinâmico) - REMOVIDO PARA IA
                # if media_corpos > 0 and (media_corpos * cfg["min_body"]) < corpo_atual < (media_corpos * cfg["max_body"]):
                if True:
                    
                    # 2. Filtro de Tendência e 3. Filtro de Rejeição (Pavio)
                    # CALL: Tendência de Alta + Pavio superior pequeno (< 10%)
                    if (not cfg["use_trend"] or t_mom == "ALTA") and v_atual['close'] > v_atual['open']:
                        # if (v_atual['max'] - v_atual['close']) < (corpo_atual * cfg["max_wick"]):
                        if True:
                            st_mom["entry_price"] = v_atual['close']
                            if not simulacao: print(f"PADRÃO: {st_mom['nome']} DE ALTA (FILTRADO). COMPRAR!")
                            add_sinal(st_mom, "CALL")
                    
                    # PUT: Tendência de Baixa + Pavio inferior pequeno (< 10%)
                    elif (not cfg["use_trend"] or t_mom == "BAIXA") and v_atual['close'] < v_atual['open']:
                        # if (v_atual['close'] - v_atual['min']) < (corpo_atual * cfg["max_wick"]):
                        if True:
                            st_mom["entry_price"] = v_atual['close']
                            if not simulacao: print(f"PADRÃO: {st_mom['nome']} DE BAIXA (FILTRADO). VENDER!")
                            add_sinal(st_mom, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 8: CHUTE DE ALTA (KICKER)
        # -----------------------------------------------------------
        if len(historico) >= 2 and "Bullish_Kicker" in self.estrategias:
            st_kicker_up = self.estrategias["Bullish_Kicker"]
            
            if st_kicker_up["status"] == "idle" and not mercado_parado:
                v1 = historico[-2] # Vermelha
                v2 = historico[-1] # Verde

                v1_vermelha = v1['close'] < v1['open']
                v2_verde = v2['close'] > v2['open']

                # Gap Explosivo: Abertura da V2 >= Abertura da V1
                gap_explosivo = v2['open'] >= v1['open']

                # Filtro Sem Sombra Inferior: Open == Min
                sem_sombra = v2['open'] == v2['min']

                if v1_vermelha and v2_verde and gap_explosivo and sem_sombra:
                    st_kicker_up["entry_price"] = v2['close']
                    if not simulacao: print(f"PADRÃO: {st_kicker_up['nome']} IDENTIFICADO. COMPRAR!")
                    add_sinal(st_kicker_up, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 9: CHUTE DE QUEDA (KICKER)
        # -----------------------------------------------------------
        if len(historico) >= 2 and "Bearish_Kicker" in self.estrategias:
            st_kicker_down = self.estrategias["Bearish_Kicker"]
            
            if st_kicker_down["status"] == "idle" and not mercado_parado:
                v1 = historico[-2] # Verde
                v2 = historico[-1] # Vermelha

                v1_verde = v1['close'] > v1['open']
                v2_vermelha = v2['close'] < v2['open']

                # Gap Explosivo: Abertura da V2 <= Abertura da V1
                gap_explosivo = v2['open'] <= v1['open']

                # Filtro Sem Sombra Superior: Open == Max
                sem_sombra = v2['open'] == v2['max']

                if v1_verde and v2_vermelha and gap_explosivo and sem_sombra:
                    st_kicker_down["entry_price"] = v2['close']
                    if not simulacao: print(f"PADRÃO: {st_kicker_down['nome']} IDENTIFICADO. VENDER!")
                    add_sinal(st_kicker_down, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 11: DIA LONGO (LONG DAY)
        # -----------------------------------------------------------
        if len(historico) >= 6 and "Long_Day" in self.estrategias:
            st_long = self.estrategias["Long_Day"]
            cfg = st_long["config"] # Carrega configuração dinâmica
            t_long = get_trend(st_long)
            
            # Lógica Melhorada com Filtros de Contexto
            if st_long["status"] == "idle" and not mercado_parado:
                
                v_atual = historico[-1]
                corpo_atual = abs(v_atual['open'] - v_atual['close'])

                # 1. Filtro de Tamanho Dinâmico (Camaleão) - REMOVIDO PARA IA
                # if media_corpos > 0 and (media_corpos * cfg["min_body"]) < corpo_atual < (media_corpos * cfg["max_body"]):
                if True:
                    
                    # 2. Filtro de Tendência e 3. Filtro de Rejeição (Marubozu check)
                    # Se use_trend for True, só entra se a tendência for ALTA
                    if (not cfg["use_trend"] or t_long == "ALTA") and v_atual['close'] > v_atual['open']:
                        # Verifica pavio superior (rejeição)
                        # if (v_atual['max'] - v_atual['close']) < (corpo_atual * cfg["max_wick"]):
                        if True:
                            st_long["entry_price"] = v_atual['close']
                            if not simulacao: print(f"PADRÃO: {st_long['nome']} DE ALTA. FORÇA CONFIRMADA.")
                            add_sinal(st_long, "CALL")
                            
                    elif (not cfg["use_trend"] or t_long == "BAIXA") and v_atual['close'] < v_atual['open']:
                        # Verifica pavio inferior (rejeição)
                        # if (v_atual['close'] - v_atual['min']) < (corpo_atual * cfg["max_wick"]):
                        if True:
                            st_long["entry_price"] = v_atual['close']
                            if not simulacao: print(f"PADRÃO: {st_long['nome']} DE BAIXA. FORÇA CONFIRMADA.")
                            add_sinal(st_long, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 13: DOJI LIBÉLULA (DRAGONFLY DOJI)
        # -----------------------------------------------------------
        if len(historico) >= 4 and "Dragonfly_Doji" in self.estrategias:
            st_dragon = self.estrategias["Dragonfly_Doji"]
            
            if st_dragon["status"] == "idle" and not mercado_parado:
                # Contexto: 3 velas anteriores vermelhas
                v1 = historico[-4]
                v2 = historico[-3]
                v3 = historico[-2]
                v_atual = historico[-1] # O Doji

                tres_vermelhas = (v1['close'] < v1['open']) and (v2['close'] < v2['open']) and (v3['close'] < v3['open'])
                
                # Características do Dragonfly
                corpo = abs(v_atual['open'] - v_atual['close'])
                sem_sombra_sup = v_atual['max'] == v_atual['open'] or v_atual['max'] == v_atual['close'] # Tolerância zero ou muito baixa
                # Usando tolerância pequena para "quase igual"
                sem_sombra_sup = (v_atual['max'] - max(v_atual['open'], v_atual['close'])) < 0.00005
                
                sombra_inf = v_atual['open'] - v_atual['min'] # Aproximado, pois open ~= close
                sombra_longa = sombra_inf > (corpo * 5)

                if tres_vermelhas and sem_sombra_sup and sombra_longa:
                    st_dragon["entry_price"] = v_atual['close']
                    if not simulacao: print(f"PADRÃO: {st_dragon['nome']} (REVERSÃO). COMPRAR!")
                    add_sinal(st_dragon, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 14: DOJI LÁPIDE (GRAVESTONE DOJI)
        # -----------------------------------------------------------
        if len(historico) >= 4 and "Gravestone_Doji" in self.estrategias:
            st_grave = self.estrategias["Gravestone_Doji"]
            
            if st_grave["status"] == "idle" and not mercado_parado:
                # Contexto: 3 velas anteriores verdes
                v1 = historico[-4]
                v2 = historico[-3]
                v3 = historico[-2]
                v_atual = historico[-1]

                tres_verdes = (v1['close'] > v1['open']) and (v2['close'] > v2['open']) and (v3['close'] > v3['open'])
                
                # Características do Gravestone
                corpo = abs(v_atual['open'] - v_atual['close'])
                
                # Sem sombra inferior (Min == Open/Close)
                sem_sombra_inf = (min(v_atual['open'], v_atual['close']) - v_atual['min']) < 0.00005
                
                sombra_sup = v_atual['max'] - v_atual['open']
                sombra_longa = sombra_sup > (corpo * 5)

                if tres_verdes and sem_sombra_inf and sombra_longa:
                    st_grave["entry_price"] = v_atual['close']
                    if not simulacao: print(f"PADRÃO: {st_grave['nome']} (REVERSÃO). VENDER!")
                    add_sinal(st_grave, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 16: MORNING STAR (ESTRELA DA MANHÃ)
        # -----------------------------------------------------------
        if len(historico) >= 3 and "Morning_Star" in self.estrategias:
            st_mstar = self.estrategias["Morning_Star"]
            t_mstar = get_trend(st_mstar)
            
            # Requer Tendência de BAIXA (Reversão no fundo)
            if st_mstar["status"] == "idle" and not mercado_parado and t_mstar == "BAIXA":
                v1 = historico[-3] # Vermelha forte
                v2 = historico[-2] # Doji
                v3 = historico[-1] # Verde forte

                v1_red = v1['close'] < v1['open']
                corpo_v1 = abs(v1['open'] - v1['close'])
                
                corpo_v2 = abs(v2['open'] - v2['close'])
                v2_doji = corpo_v2 < (corpo_v1 * 0.1)
                
                v3_green = v3['close'] > v3['open']
                midpoint_v1 = (v1['open'] + v1['close']) / 2
                v3_piercing = v3['close'] > midpoint_v1

                if v1_red and v2_doji and v3_green and v3_piercing:
                    st_mstar["entry_price"] = v3['close']
                    if not simulacao: print(f"PADRÃO: {st_mstar['nome']} IDENTIFICADO. COMPRAR!")
                    add_sinal(st_mstar, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 17: EVENING STAR (ESTRELA DA NOITE)
        # -----------------------------------------------------------
        if len(historico) >= 3 and "Evening_Star" in self.estrategias:
            st_estar = self.estrategias["Evening_Star"]
            t_estar = get_trend(st_estar)
            
            # Requer Tendência de ALTA (Reversão no topo)
            if st_estar["status"] == "idle" and not mercado_parado and t_estar == "ALTA":
                v1 = historico[-3] # Verde forte
                v2 = historico[-2] # Doji acima
                v3 = historico[-1] # Vermelha forte

                v1_green = v1['close'] > v1['open']
                
                # Doji acima do fechamento da v1
                v2_acima = min(v2['open'], v2['close']) > v1['close']
                
                v3_red = v3['close'] < v3['open']
                midpoint_v1 = (v1['open'] + v1['close']) / 2
                v3_piercing = v3['close'] < midpoint_v1

                if v1_green and v2_acima and v3_red and v3_piercing:
                    st_estar["entry_price"] = v3['close']
                    if not simulacao: print(f"PADRÃO: {st_estar['nome']} IDENTIFICADO. VENDER!")
                    add_sinal(st_estar, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 18: ENGOLFO DE ALTA
        # -----------------------------------------------------------
        if len(historico) >= 2 and "Bullish_Engulfing" in self.estrategias:
            st_eng_up = self.estrategias["Bullish_Engulfing"]
            t_eng_up = get_trend(st_eng_up)
            
            # Requer Tendência de BAIXA (Reversão para Alta)
            # Correção: Usa validar_filtros ou verifica config['use_trend'] explicitamente
            if st_eng_up["status"] == "idle" and not mercado_parado:
                v1 = historico[-2] # Vermelha
                v2 = historico[-1] # Verde

                # v2 engole v1
                engolfo = (v2['open'] < v1['close']) and (v2['close'] > v1['open'])
                
                # Verifica tendência (se ativada) e tamanho do corpo da vela de força (v2)
                if engolfo and self.validar_filtros(v2, st_eng_up["config"], ctx, "BAIXA", t_eng_up):
                    st_eng_up["entry_price"] = v2['close']
                    if not simulacao: print(f"PADRÃO: {st_eng_up['nome']} IDENTIFICADO. COMPRAR!")
                    add_sinal(st_eng_up, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 19: ENGOLFO DE BAIXA
        # -----------------------------------------------------------
        if len(historico) >= 2 and "Bearish_Engulfing" in self.estrategias:
            st_eng_down = self.estrategias["Bearish_Engulfing"]
            t_eng_down = get_trend(st_eng_down)
            
            # Requer Tendência de ALTA (Reversão para Baixa)
            if st_eng_down["status"] == "idle" and not mercado_parado:
                v1 = historico[-2] # Verde
                v2 = historico[-1] # Vermelha

                # v2 engole v1
                engolfo = (v2['open'] > v1['close']) and (v2['close'] < v1['open'])
                
                if engolfo and self.validar_filtros(v2, st_eng_down["config"], ctx, "ALTA", t_eng_down):
                    st_eng_down["entry_price"] = v2['close']
                    if not simulacao: print(f"PADRÃO: {st_eng_down['nome']} IDENTIFICADO. VENDER!")
                    add_sinal(st_eng_down, "PUT")

        # -----------------------------------------------------------
        # AUXILIAR: TENDÊNCIA (Para estratégias 20, 24, 27, 28)
        # -----------------------------------------------------------

        # -----------------------------------------------------------
        # ESTRATÉGIA 20: ESTRELA CADENTE (SHOOTING STAR)
        # -----------------------------------------------------------
        if "Shooting_Star" in self.estrategias:
            st_shoot = self.estrategias["Shooting_Star"]
            t_shoot = get_trend(st_shoot)

            # Só entra se a tendência for de ALTA (para reverter para baixo)
            if st_shoot["status"] == "idle" and not mercado_parado and t_shoot == "ALTA":
                v = historico[-1]
                corpo = abs(v['open'] - v['close'])
                sombra_sup = v['max'] - max(v['open'], v['close'])
                sombra_inf = min(v['open'], v['close']) - v['min']
                
                # Sombra superior >= 2x corpo E Sombra inferior quase zero
                if sombra_sup >= (corpo * 2) and sombra_inf < (corpo * 0.2):
                    st_shoot["entry_price"] = v['close']
                    if not simulacao: print(f"PADRÃO: {st_shoot['nome']} IDENTIFICADO. VENDER!")
                    add_sinal(st_shoot, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 27: MARTELO (HAMMER)
        # -----------------------------------------------------------
        if "Hammer" in self.estrategias:
            st_hammer = self.estrategias["Hammer"]
            t_hammer = get_trend(st_hammer)

            # Só entra se a tendência for de BAIXA (para reverter para cima)
            if st_hammer["status"] == "idle" and not mercado_parado and t_hammer == "BAIXA":
                v = historico[-1]
                corpo = abs(v['open'] - v['close'])
                sombra_sup = v['max'] - max(v['open'], v['close'])
                sombra_inf = min(v['open'], v['close']) - v['min']
                
                # Sombra inferior >= 2x corpo E Sombra superior quase zero
                if sombra_inf >= (corpo * 2) and sombra_sup < (corpo * 0.2):
                    st_hammer["entry_price"] = v['close']
                    if not simulacao: print(f"PADRÃO: {st_hammer['nome']} IDENTIFICADO. COMPRAR!")
                    add_sinal(st_hammer, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 24: HOMEM ENFORCADO (HANGING MAN)
        # -----------------------------------------------------------
        if "Hanging_Man" in self.estrategias:
            st_hang = self.estrategias["Hanging_Man"]
            t_hang = get_trend(st_hang)

            if st_hang["status"] == "idle" and not mercado_parado and t_hang == "ALTA":
                v = historico[-1]
                corpo = abs(v['open'] - v['close'])
                sombra_sup = v['max'] - max(v['open'], v['close'])
                sombra_inf = min(v['open'], v['close']) - v['min']
                
                # Anatomia igual ao Martelo, mas em tendência de alta
                if sombra_inf >= (corpo * 2) and sombra_sup < (corpo * 0.2):
                    st_hang["entry_price"] = v['close']
                    if not simulacao: print(f"PADRÃO: {st_hang['nome']} IDENTIFICADO. VENDER!")
                    add_sinal(st_hang, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 28: MARTELO INVERTIDO
        # -----------------------------------------------------------
        if "Inverted_Hammer" in self.estrategias:
            st_inv_hammer = self.estrategias["Inverted_Hammer"]
            t_inv_hammer = get_trend(st_inv_hammer)

            if st_inv_hammer["status"] == "idle" and not mercado_parado and t_inv_hammer == "BAIXA":
                v = historico[-1]
                corpo = abs(v['open'] - v['close'])
                sombra_sup = v['max'] - max(v['open'], v['close'])
                sombra_inf = min(v['open'], v['close']) - v['min']
                
                # Anatomia igual à Estrela Cadente, mas em tendência de baixa
                if sombra_sup >= (corpo * 2) and sombra_inf < (corpo * 0.2):
                    st_inv_hammer["entry_price"] = v['close']
                    if not simulacao: print(f"PADRÃO: {st_inv_hammer['nome']} IDENTIFICADO. COMPRAR!")
                    add_sinal(st_inv_hammer, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 22 e 23: GAPS TASUKI
        # -----------------------------------------------------------
        if len(historico) >= 3:
            # Tasuki de Alta
            if "Upside_Tasuki" in self.estrategias:
                st_tasuki_up = self.estrategias["Upside_Tasuki"]
                t_tasuki_up = get_trend(st_tasuki_up)

                # Requer Tendência de ALTA (Continuação)
                if st_tasuki_up["status"] == "idle" and not mercado_parado and t_tasuki_up == "ALTA":
                    v1 = historico[-3] # Verde
                    v2 = historico[-2] # Verde com Gap
                    v3 = historico[-1] # Vermelha

                    v1_green = v1['close'] > v1['open']
                    v2_green = v2['close'] > v2['open']
                    gap_up = v2['open'] > v1['close']
                    
                    v3_red = v3['close'] < v3['open']
                    v3_opens_inside_v2 = v2['open'] < v3['open'] < v2['close']
                    v3_closes_above_v1 = v3['close'] > v1['close'] # Fecha no gap, não abaixo de v1

                    if v1_green and v2_green and gap_up and v3_red and v3_opens_inside_v2 and v3_closes_above_v1:
                        st_tasuki_up["entry_price"] = v3['close']
                        if not simulacao: print(f"PADRÃO: {st_tasuki_up['nome']} IDENTIFICADO. COMPRAR!")
                        add_sinal(st_tasuki_up, "CALL")

            # Tasuki de Baixa
            if "Downside_Tasuki" in self.estrategias:
                st_tasuki_down = self.estrategias["Downside_Tasuki"]
                t_tasuki_down = get_trend(st_tasuki_down)

                # Requer Tendência de BAIXA (Continuação)
                if st_tasuki_down["status"] == "idle" and not mercado_parado and t_tasuki_down == "BAIXA":
                    v1 = historico[-3] # Vermelha
                    v2 = historico[-2] # Vermelha com Gap
                    v3 = historico[-1] # Verde

                    v1_red = v1['close'] < v1['open']
                    v2_red = v2['close'] < v2['open']
                    gap_down = v2['open'] < v1['close']
                    
                    v3_green = v3['close'] > v3['open']
                    v3_opens_inside_v2 = v2['close'] < v3['open'] < v2['open']
                    v3_closes_below_v1 = v3['close'] < v1['close']

                    if v1_red and v2_red and gap_down and v3_green and v3_opens_inside_v2 and v3_closes_below_v1:
                        st_tasuki_down["entry_price"] = v3['close']
                        if not simulacao: print(f"PADRÃO: {st_tasuki_down['nome']} IDENTIFICADO. VENDER!")
                        add_sinal(st_tasuki_down, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 29: MARUBOZU
        # -----------------------------------------------------------
        if "Marubozu" in self.estrategias:
            st_maru = self.estrategias["Marubozu"]
            t_maru = get_trend(st_maru)

            if st_maru["status"] == "idle" and not mercado_parado:
                v = historico[-1]
                tol = 0.00005 # Tolerância pequena
                
                # Marubozu de Alta (Open=Min, Close=Max) - Requer Tendência de ALTA
                if abs(v['open'] - v['min']) < tol and abs(v['close'] - v['max']) < tol and t_maru == "ALTA":
                    st_maru["entry_price"] = v['close']
                    if not simulacao: print(f"PADRÃO: {st_maru['nome']} DE ALTA. COMPRAR!")
                    add_sinal(st_maru, "CALL")
                
                # Marubozu de Baixa (Open=Max, Close=Min) - Requer Tendência de BAIXA
                elif abs(v['open'] - v['max']) < tol and abs(v['close'] - v['min']) < tol and t_maru == "BAIXA":
                    st_maru["entry_price"] = v['close']
                    if not simulacao: print(f"PADRÃO: {st_maru['nome']} DE BAIXA. VENDER!")
                    add_sinal(st_maru, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 30 e 31: HARAMI
        # -----------------------------------------------------------
        if len(historico) >= 2 and "Harami" in self.estrategias:
            st_harami = self.estrategias["Harami"]
            t_harami = get_trend(st_harami)

            if st_harami["status"] == "idle" and not mercado_parado:
                v1 = historico[-2] # Mãe
                v2 = historico[-1] # Bebê

                # Harami de Baixa (Reversão para Queda): v1 Verde, v2 contida. Requer Tendência de ALTA.
                if v1['close'] > v1['open'] and t_harami == "ALTA":
                    # v2 contida entre open e close da v1
                    if v2['max'] < v1['close'] and v2['min'] > v1['open']:
                        st_harami["entry_price"] = v2['close']
                        if not simulacao: print(f"PADRÃO: {st_harami['nome']} DE BAIXA. VENDER!")
                        add_sinal(st_harami, "PUT")
                
                # Harami de Alta (Reversão para Subida): v1 Vermelha, v2 contida. Requer Tendência de BAIXA.
                elif v1['close'] < v1['open'] and t_harami == "BAIXA":
                    # v2 contida entre open e close da v1
                    if v2['max'] < v1['open'] and v2['min'] > v1['close']:
                        st_harami["entry_price"] = v2['close']
                        if not simulacao: print(f"PADRÃO: {st_harami['nome']} DE ALTA. COMPRAR!")
                        add_sinal(st_harami, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 33: NUVEM NEGRA (DARK CLOUD COVER)
        # -----------------------------------------------------------
        if len(historico) >= 2 and "Dark_Cloud_Cover" in self.estrategias:
            st_dark = self.estrategias["Dark_Cloud_Cover"]
            t_dark = get_trend(st_dark)

            # Requer Tendência de ALTA (Reversão no topo)
            if st_dark["status"] == "idle" and not mercado_parado and t_dark == "ALTA":
                v1 = historico[-2] # Verde Longa
                v2 = historico[-1] # Vermelha
                
                v1_green = v1['close'] > v1['open']
                v2_red = v2['close'] < v2['open']
                
                # Abre acima do fechamento de v1
                opens_above = v2['open'] > v1['close']
                
                # Fecha abaixo de 50% de v1, mas acima da abertura
                midpoint = (v1['open'] + v1['close']) / 2
                closes_below_mid = v2['close'] < midpoint
                closes_above_open = v2['close'] > v1['open']
                
                if v1_green and v2_red and opens_above and closes_below_mid and closes_above_open:
                    st_dark["entry_price"] = v2['close']
                    if not simulacao: print(f"PADRÃO: {st_dark['nome']} IDENTIFICADO. VENDER!")
                    add_sinal(st_dark, "PUT")

        # -----------------------------------------------------------
        # ESTRATÉGIA 37: PIERCING LINE (PADRÃO PERFURANTE)
        # -----------------------------------------------------------
        if len(historico) >= 2 and "Piercing_Line" in self.estrategias:
            st_piercing = self.estrategias["Piercing_Line"]
            t_piercing = get_trend(st_piercing)

            # Requer Tendência de BAIXA (Reversão no fundo)
            if st_piercing["status"] == "idle" and not mercado_parado and t_piercing == "BAIXA":
                v1 = historico[-2] # Vermelha Longa
                v2 = historico[-1] # Verde
                
                v1_red = v1['close'] < v1['open']
                v2_green = v2['close'] > v2['open']
                
                # Abre abaixo da mínima de v1
                opens_below_min = v2['open'] < v1['min']
                
                # Fecha acima de 50% de v1
                midpoint = (v1['open'] + v1['close']) / 2
                closes_above_mid = v2['close'] > midpoint
                closes_below_open = v2['close'] < v1['open']

                if v1_red and v2_green and opens_below_min and closes_above_mid and closes_below_open:
                    st_piercing["entry_price"] = v2['close']
                    if not simulacao: print(f"PADRÃO: {st_piercing['nome']} IDENTIFICADO. COMPRAR!")
                    add_sinal(st_piercing, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 34 e 35: PADRÕES DE 3 DIAS (RISING/FALLING THREE METHODS)
        # -----------------------------------------------------------
        if len(historico) >= 5:
            # Falling (Venda)
            if "Falling_Three_Methods" in self.estrategias:
                st_fall = self.estrategias["Falling_Three_Methods"]
                t_fall = get_trend(st_fall)

                # Requer Tendência de BAIXA (Continuação)
                if st_fall["status"] == "idle" and not mercado_parado and t_fall == "BAIXA":
                    v1 = historico[-5] # Vermelha Longa
                    v2, v3, v4 = historico[-4], historico[-3], historico[-2] # Verdes Pequenas
                    v5 = historico[-1] # Vermelha Longa

                    v1_red = v1['close'] < v1['open']
                    # As 3 intermediárias devem estar dentro do range da v1
                    inside_range = all(v['max'] < v1['max'] and v['min'] > v1['min'] for v in [v2, v3, v4])
                    
                    v5_red = v5['close'] < v5['open']
                    v5_breakout = v5['close'] < v1['min'] # Fecha abaixo da mínima da v1

                    if v1_red and inside_range and v5_red and v5_breakout:
                        st_fall["entry_price"] = v5['close']
                        if not simulacao: print(f"PADRÃO: {st_fall['nome']} IDENTIFICADO. VENDER!")
                        add_sinal(st_fall, "PUT")

            # Rising (Compra)
            if "Rising_Three_Methods" in self.estrategias:
                st_rise = self.estrategias["Rising_Three_Methods"]
                t_rise = get_trend(st_rise)

                # Requer Tendência de ALTA (Continuação)
                if st_rise["status"] == "idle" and not mercado_parado and t_rise == "ALTA":
                    v1 = historico[-5] # Verde Longa
                    v2, v3, v4 = historico[-4], historico[-3], historico[-2] # Vermelhas Pequenas
                    v5 = historico[-1] # Verde Longa

                    v1_green = v1['close'] > v1['open']
                    inside_range = all(v['max'] < v1['max'] and v['min'] > v1['min'] for v in [v2, v3, v4])
                    
                    v5_green = v5['close'] > v5['open']
                    v5_breakout = v5['close'] > v1['max'] # Fecha acima da máxima da v1

                    if v1_green and inside_range and v5_green and v5_breakout:
                        st_rise["entry_price"] = v5['close']
                        if not simulacao: print(f"PADRÃO: {st_rise['nome']} IDENTIFICADO. COMPRAR!")
                        add_sinal(st_rise, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 38 e 39: PINÇAS (TWEEZERS)
        # -----------------------------------------------------------
        if len(historico) >= 2:
            tol = 0.00005
            # Topo (Venda)
            if "Tweezers_Top" in self.estrategias:
                st_ttop = self.estrategias["Tweezers_Top"]

                if st_ttop["status"] == "idle" and not mercado_parado:
                    v1 = historico[-2]
                    v2 = historico[-1]
                    # Máximas iguais
                    if abs(v1['max'] - v2['max']) < tol:
                        st_ttop["entry_price"] = v2['close']
                        if not simulacao: print(f"PADRÃO: {st_ttop['nome']} IDENTIFICADO. VENDER!")
                        add_sinal(st_ttop, "PUT")

            # Fundo (Compra)
            if "Tweezers_Bottom" in self.estrategias:
                st_tbot = self.estrategias["Tweezers_Bottom"]

                if st_tbot["status"] == "idle" and not mercado_parado:
                    v1 = historico[-2]
                    v2 = historico[-1]
                    # Mínimas iguais
                    if abs(v1['min'] - v2['min']) < tol:
                        st_tbot["entry_price"] = v2['close']
                        if not simulacao: print(f"PADRÃO: {st_tbot['nome']} IDENTIFICADO. COMPRAR!")
                        add_sinal(st_tbot, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 41: STRIKE DE BAIXA (REVERSÃO PARA ALTA)
        # -----------------------------------------------------------
        if len(historico) >= 4 and "Three_Line_Strike_Bull" in self.estrategias:
            st_strike = self.estrategias["Three_Line_Strike_Bull"]

            if st_strike["status"] == "idle" and not mercado_parado:
                v1, v2, v3 = historico[-4], historico[-3], historico[-2] # 3 Vermelhas
                v4 = historico[-1] # Verde Gigante

                tres_vermelhas = (v1['close'] < v1['open']) and (v2['close'] < v2['open']) and (v3['close'] < v3['open'])
                v4_engolfa = v4['close'] > v1['open'] # Fecha acima da abertura da primeira

                if tres_vermelhas and v4_engolfa:
                    st_strike["entry_price"] = v4['close']
                    if not simulacao: print(f"PADRÃO: {st_strike['nome']} IDENTIFICADO. COMPRAR!")
                    add_sinal(st_strike, "CALL")

        # -----------------------------------------------------------
        # ESTRATÉGIA 43: VELA PRENSADA (STICK SANDWICH)
        # -----------------------------------------------------------
        if len(historico) >= 3 and "Stick_Sandwich" in self.estrategias:
            st_sand = self.estrategias["Stick_Sandwich"]

            if st_sand["status"] == "idle" and not mercado_parado:
                v1 = historico[-3] # Vermelha
                v3 = historico[-1] # Vermelha
                # Fechamentos iguais (Suporte)
                if (v1['close'] < v1['open']) and (v3['close'] < v3['open']) and abs(v1['close'] - v3['close']) < 0.00005:
                    st_sand["entry_price"] = v3['close']
                    if not simulacao: print(f"PADRÃO: {st_sand['nome']} IDENTIFICADO. COMPRAR!")
                    add_sinal(st_sand, "CALL")

        return sinais, ctx, resultados_finalizados