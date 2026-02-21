import time
import threading
import os
import logging
import webview
from collections import deque
from flask import Flask, render_template, jsonify, request
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
from brain import BrainAI, StudentSLM
from estrategias import GerenteEstrategia
from financas import GerenteFinancas

app = Flask(__name__)
app.json.sort_keys = False # Garante que o JSON respeite a ordem de prioridade (Flask 3.x)

# Desativa logs de requisição do Flask (Werkzeug) para limpar o console
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# --- CONFIGURAÇÕES ---
# IMPORTANTE: Substitua pelas suas credenciais ou use variáveis de ambiente
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

# Variáveis Globais
api = None
historico_velas = deque(maxlen=1000) # Aumentado para 1000 para suportar backtests e análises longas
ativo_atual = None
thread_atualizacao = None
ordens_em_andamento = [] # Lista de ordens abertas para checagem via API
cache_ativos_otc = []
trading_enabled = False # Começa desligado por segurança (Vermelho)
ultima_vela_analisada = None
tipo_opcao = 'BLITZ' # 'BLITZ' (Binária/Turbo) ou 'DIGITAL'

# --- SHADOW TRACKING (RASTREAMENTO FANTASMA) ---
# Placar de Validação da IA
score_ia = {"acertos_bloqueio": 0, "erros_bloqueio": 0}
bloqueios_pendentes = [] # Fila de sinais bloqueados aguardando validação
consecutive_errors = 0 # Contador para recalibração de humor da IA

gerente_estrategia = GerenteEstrategia()
gerente_financas = GerenteFinancas()
ia_brain = BrainAI(api_key=os.getenv("GROQ_API_KEY")) # Carrega a chave do ambiente (bot_load.bat)
ia_aluna = StudentSLM() # Inicializa a IA Local (SLM)

def conectar_api():
    global api
    print("Tentando conectar...")
    api = IQ_Option(EMAIL, PASSWORD)
    check, reason = api.connect()
    if check:
        print("Conectado com sucesso!")
    else:
        print(f"Erro na conexão: {reason}")
    return check

def formatar_vela(vela, ativo):
    """Formata a vela conforme solicitado (ID, from, to, open, close, etc)"""
    return {
        "id": vela['id'],
        "ativo": ativo,
        "fromTimestamp": vela['from'], # Segundo exato abertura
        "toTimestamp": vela['to'],     # Segundo exato fechamento
        "open": vela['open'],
        "close": vela['close'],
        "min": vela['min'],
        "max": vela['max'],
        "volume": vela['volume'],
        "horario_formatado": datetime.fromtimestamp(vela['from']).strftime('%H:%M:%S')
    }

def loop_checagem_resultados():
    """
    Thread dedicada a verificar o resultado das ordens na API.
    Evita slippage e garante que o resultado seja o oficial da corretora.
    """
    global ordens_em_andamento
    while True:
        if not api or not ordens_em_andamento:
            time.sleep(1)
            continue
            
        for ordem in ordens_em_andamento[:]:
            try:
                tipo = ordem.get('tipo', 'BINARY')
                fechada = False
                lucro = 0.0
                
                if tipo == 'DIGITAL':
                    # Digital usa check_win_digital_v2 (bloqueia até fechar)
                    check, lucro = api.check_win_digital_v2(ordem['id'])
                    if check:
                        fechada = True
                else:
                    # Binária/Blitz usa check_win_v3 (bloqueia até fechar)
                    resultado, lucro = api.check_win_v3(ordem['id'])
                    if resultado:
                        fechada = True
                
                if fechada:
                    win = lucro > 0
                    print(f"Ordem {ordem['id']} ({tipo}) finalizada. Lucro: {lucro}")
                    
                    # Notifica o Gerente de Estratégias (Auditoria do Analista)
                    for nome_st in ordem.get('estrategias', []):
                        gerente_estrategia.notificar_resultado_api(nome_st, win, lucro)
                    
                    # --- TREINAMENTO PARALELO (ML) ---
                    if 'contexto_ml' in ordem:
                        resultado_real = "WIN" if win else "LOSS"
                        # Salva telemetria rica para a Aluna estudar
                        terreno_op = ordem['contexto_ml'].get('terreno', 'DESCONHECIDO')
                        contexto_tecnico_op = ordem.get('contexto_tecnico', {})
                        ia_aluna.registrar_telemetria(ordem['contexto_ml'], contexto_tecnico_op, ordem['contexto_ml']['decisao_groq'], resultado_real, terreno_op)
                        print(f"📝 Aprendizado Registrado: ID {ordem['id']} | Decisão IA: {ordem['contexto_ml']['decisao_groq']} | Resultado: {resultado_real}")

                        # --- AUTO-REFLEXÃO (PROCEED_LOSS) ---
                        if not win:
                            threading.Thread(target=ia_aluna.refletir_sobre_erro, args=("PROCEED_LOSS", ordem.get('sinal', 'UNKNOWN'), contexto_tecnico_op, list(historico_velas)[-15:])).start()
                        
                    ordens_em_andamento.remove(ordem)
            except Exception as e:
                print(f"Erro ao checar ordem {ordem['id']}: {e}")
        
        time.sleep(2) # Verifica a cada 2 segundos

def loop_atualizacao_velas():
    """
    Loop que roda em background.
    Sincroniza com o horário do servidor e busca a vela assim que ela fecha.
    """
    global ativo_atual, historico_velas, ultima_vela_analisada, bloqueios_pendentes, score_ia, consecutive_errors
    
    while True:
        if not api or not ativo_atual:
            time.sleep(1)
            continue

        try:
            # Pega horário do servidor para referência
            server_time = api.get_server_timestamp()
            
            # Busca as últimas 10 velas (leve e rápido)
            velas = api.get_candles(ativo_atual, 60, 10, server_time)
            
            if velas:
                # Lógica Robusta:
                # Calculamos o inicio do minuto atual (Vela Viva)
                # Qualquer vela com horário ANTERIOR a isso é uma vela FECHADA.
                ts_minuto_atual = (server_time // 60) * 60
                
                vela_fechada_nova = None
                
                # Procura de trás para frente a primeira vela que já fechou
                for v in reversed(velas):
                    if v['from'] < ts_minuto_atual:
                        vela_fechada_nova = v
                        break
                
                # Se achamos uma vela fechada e ela é nova (ainda não processada)
                if vela_fechada_nova:
                    if ultima_vela_analisada is None or vela_fechada_nova['from'] > ultima_vela_analisada:
                        ultima_vela_analisada = vela_fechada_nova['from']
                        
                        dados_formatados = formatar_vela(vela_fechada_nova, ativo_atual)
                        historico_velas.append(dados_formatados)
                        print(f"--- NOVA VELA FECHADA: {dados_formatados['horario_formatado']} ---")
                        time.sleep(1) # Trava de segurança: Evita spam de requests no mesmo segundo
                        
                        # --- SHADOW TRACKING: VALIDAÇÃO DOS BLOQUEIOS ANTERIORES ---
                        # Verifica se a vela que acabou de fechar confirmou ou negou o bloqueio da IA
                        if bloqueios_pendentes:
                            fechamento_atual = dados_formatados['close']
                            for bloqueio in bloqueios_pendentes:
                                entrada = bloqueio['preco_entrada']
                                sinal_bloqueado = bloqueio['sinal']
                                contexto_do_bloqueio = bloqueio['contexto']
                                contexto_ml_bloqueio = bloqueio.get('contexto_ml', {})
                                
                                # Lógica: Se bloqueou CALL, torcemos para cair (Loss evitado). Se subir, IA errou.
                                if sinal_bloqueado == "CALL":
                                    if fechamento_atual < entrada:
                                        score_ia['acertos_bloqueio'] += 1
                                        ia_brain.log_pensamento(f"✅ Validação: Bloqueio de CALL correto. Preço caiu (Loss evitado).")
                                        consecutive_errors = 0 # Reset: IA acertou
                                        if contexto_ml_bloqueio: ia_aluna.registrar_telemetria(contexto_ml_bloqueio, contexto_do_bloqueio, "BLOCK", "LOSS", contexto_ml_bloqueio.get('terreno'))
                                    elif fechamento_atual > entrada:
                                        score_ia['erros_bloqueio'] += 1
                                        ia_brain.log_pensamento(f"❌ Validação: Bloqueio de CALL incorreto. Preço subiu (Win perdido).")
                                        consecutive_errors += 1 # Erro: IA foi medrosa
                                        if contexto_ml_bloqueio: ia_aluna.registrar_telemetria(contexto_ml_bloqueio, contexto_do_bloqueio, "BLOCK", "WIN", contexto_ml_bloqueio.get('terreno'))
                                        # Aciona Auto-Reflexão (MISSED_WIN)
                                        threading.Thread(target=ia_aluna.refletir_sobre_erro, args=("MISSED_WIN", "CALL", contexto_do_bloqueio, list(historico_velas)[-15:])).start()
                                
                                # Lógica: Se bloqueou PUT, torcemos para subir (Loss evitado). Se cair, IA errou.
                                elif sinal_bloqueado == "PUT":
                                    if fechamento_atual > entrada:
                                        score_ia['acertos_bloqueio'] += 1
                                        ia_brain.log_pensamento(f"✅ Validação: Bloqueio de PUT correto. Preço subiu (Loss evitado).")
                                        consecutive_errors = 0 # Reset: IA acertou
                                        if contexto_ml_bloqueio: ia_aluna.registrar_telemetria(contexto_ml_bloqueio, contexto_do_bloqueio, "BLOCK", "LOSS", contexto_ml_bloqueio.get('terreno'))
                                    elif fechamento_atual < entrada:
                                        score_ia['erros_bloqueio'] += 1
                                        ia_brain.log_pensamento(f"❌ Validação: Bloqueio de PUT incorreto. Preço caiu (Win perdido).")
                                        consecutive_errors += 1 # Erro: IA foi medrosa
                                        if contexto_ml_bloqueio: ia_aluna.registrar_telemetria(contexto_ml_bloqueio, contexto_do_bloqueio, "BLOCK", "WIN", contexto_ml_bloqueio.get('terreno'))
                                        # Aciona Auto-Reflexão (MISSED_WIN)
                                        threading.Thread(target=ia_aluna.refletir_sobre_erro, args=("MISSED_WIN", "PUT", contexto_do_bloqueio, list(historico_velas)[-15:])).start()
                            
                            bloqueios_pendentes = [] # Limpa a fila após validar

                        # Processa estratégias e verifica se houve sinal de entrada
                        lista_sinais, contexto_atual, resultados_finalizados = gerente_estrategia.processar(list(historico_velas))

                        # Salva o resultado das operações simuladas (Trading OFF) que acabaram de finalizar
                        for res in resultados_finalizados:
                            if 'contexto_ml' in res and res['contexto_ml']:
                                terreno_sim = res['contexto_ml'].get('terreno', 'DESCONHECIDO')
                                ia_aluna.registrar_telemetria(res['contexto_ml'], contexto_atual, "PROCEED", res['resultado'], terreno_sim)

                        resultado_op = gerente_financas.autorizar_operacao(lista_sinais)
                        # Se houver algum sinal detectado, processa cada um individualmente
                        votos_call = sum(1 for s in lista_sinais if s['sinal'] == 'CALL')
                        votos_put = sum(1 for s in lista_sinais if s['sinal'] == 'PUT')
                        historico_para_ml = list(historico_velas)[-200:]
                        historico_compactado_ml = ia_brain._compactar_historico_csv(historico_para_ml)
                        
                        # --- CLASSIFICAÇÃO DE TERRENO (IA ALUNA) ---
                        terreno_atual = ia_aluna.classificar_terreno(contexto_atual)
                        
                        contexto_ml_atual = {
                            "votos_call": votos_call,
                            "votos_put": votos_put,
                            "historico_csv": historico_compactado_ml,
                            "terreno": terreno_atual,
                            "decisao_groq": "PENDING"
                        }
                        
                        if resultado_op:
                            sinal = resultado_op['sinal']
                            expiracao = resultado_op['expiracao']
                            estrategias_ativas = resultado_op['estrategias']
                            
                            # --- LÓGICA DE RECALIBRAÇÃO (MEMÓRIA CURTA) ---
                            historico_analise = list(historico_velas)
                            if consecutive_errors >= 3:
                                print(f"⚠️ MODO RECALIBRAÇÃO: Ignorando histórico longo devido a {consecutive_errors} erros consecutivos. Focando no Price Action recente.")
                                historico_analise = historico_analise[-15:] # Foca apenas nas últimas 15 velas

                            # --- INJEÇÃO DE CONTEXTO DA ALUNA (RALLY) ---
                            print(f"🎓 IA Aluna: Terreno identificado -> {terreno_atual}")
                            print(f"📝 Nota da Aluna para o Professor: {ia_aluna.regra_atual}")

                            # --- NOVA VALIDAÇÃO: OLLAMA É O CHEFE ---
                            # Substituída a chamada da Groq pela IA Local (Aluna)
                            parecer_obj = ia_aluna.validar_sinal_local(
                                sinal=sinal,
                                contexto=contexto_atual,
                                historico_recente=historico_analise
                            )
                            
                            parecer_ia = parecer_obj.get("decision", "BLOCK")
                            
                            # Registra quem tomou a decisão (Ollama agora)
                            contexto_ml_atual["decisao_groq"] = f"{parecer_ia} (Ollama)"

                            # LÓGICA DE DECISÃO FINAL (Híbrida)
                            
                            if parecer_ia == "BLOCK":
                                source = parecer_obj.get("source", "UNKNOWN")
                                reason = parecer_obj.get("reason", "Risco não especificado.")

                                if source == "OLLAMA_LOCAL":
                                    print(f"🛡️ Aluna (Ollama) BLOQUEOU a operação de {sinal}. Motivo: {reason}.")
                                else: # GROQ_API, API_ERROR, etc.
                                    print(f"🛑 Bloqueio Técnico/Erro: {reason}.")

                                # Registra para validação na próxima vela (Shadow Tracking)
                                bloqueios_pendentes.append({
                                    "sinal": sinal,
                                    "preco_entrada": list(historico_velas)[-1]['close'], # Preço de fechamento da vela que gerou o sinal
                                    "horario": list(historico_velas)[-1]['horario_formatado'],
                                    "contexto": contexto_atual, # Salva o contexto do momento do bloqueio
                                    "contexto_ml": contexto_ml_atual # Salva dados para ML
                                })
                                # Libera as estratégias que votaram para não ficarem presas
                                gerente_estrategia.processar_resultado_votacao([])
                            else: # PROCEED
                                exp_txt = f"{int(expiracao*60)}s" if expiracao < 1 else f"{int(expiracao)}m"
                                print(f"SINAL CONFIRMADO PELA IA: {sinal} - Enviando ordem ({tipo_opcao} / {exp_txt})...")

                                if trading_enabled:
                                    check, order_id = False, None
                                    
                                    if tipo_opcao == 'DIGITAL':
                                        check, order_id = api.buy_digital_spot(ativo_atual, gerente_financas.valor_aposta, sinal.lower(), expiracao)
                                    else: # BLITZ ou BINARY
                                        check, order_id = api.buy(gerente_financas.valor_aposta, ativo_atual, sinal.lower(), expiracao)

                                    if check:
                                        print(f"Ordem executada! ID: {order_id}")
                                        # Registra para monitoramento
                                        ordens_em_andamento.append({
                                            "id": order_id,
                                            "sinal": sinal, # Salva o sinal para reflexão futura
                                            "estrategias": estrategias_ativas,
                                            "tipo": tipo_opcao,
                                            "contexto_ml": contexto_ml_atual, # Anexa contexto para salvar no final
                                            "contexto_tecnico": contexto_atual # Anexa contexto TÉCNICO para salvar no final
                                        })
                                        # Atualiza status: Vencedoras -> Active, Perdedoras -> Idle
                                        gerente_estrategia.processar_resultado_votacao(estrategias_ativas)
                                    else:
                                        print(f"Erro na ordem: {order_id}")
                                        # Se falhou o envio, libera todas as estratégias
                                        gerente_estrategia.processar_resultado_votacao([])
                                else:
                                    print(f"SIMULAÇÃO: Sinal {sinal} detectado, mas Trading está OFF. Apenas analisando.")
                                    # Anexa o contexto de ML nas estratégias para logar o resultado simulado na próxima vela
                                    for strat_name in estrategias_ativas:
                                        gerente_estrategia.estrategias[strat_name]['contexto_ml'] = contexto_ml_atual
                                    # Marca as estratégias como ativas para que o Analista verifique o Win/Loss na próxima vela
                                    gerente_estrategia.processar_resultado_votacao(estrategias_ativas)
                        else:
                            # Se não houve consenso (empate), libera quem estava esperando
                            gerente_estrategia.processar_resultado_votacao([])

        except Exception as e:
            print(f"Erro no monitoramento: {e}")
        
        # Polling constante de 1 segundo
        # Isso garante que pegamos a vela assim que ela estiver disponível, sem atrasos
        time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ativos-otc')
def get_ativos_otc():
    """Retorna lista de ativos OTC (Cacheado se possível)"""
    global cache_ativos_otc
    
    if not api:
        if not conectar_api():
            return jsonify({"erro": "Não foi possível conectar na API"}), 500

    if not cache_ativos_otc:
        try:
            # Usamos get_all_ACTIVES_OPCODE que é mais estável que get_all_open_time
            todos_ativos = api.get_all_ACTIVES_OPCODE()
            lista_temp = []
            
            for ativo in todos_ativos.keys():
                if 'OTC' in ativo:
                    lista_temp.append(ativo)
            
            cache_ativos_otc = sorted(list(set(lista_temp))) # Remove duplicatas e ordena
        except Exception as e:
            print(f"Erro ao buscar ativos: {e}")
            # Fallback: Lista básica caso a API falhe na listagem
            cache_ativos_otc = ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDCAD-OTC', 'NZDUSD-OTC', 'USDCHF-OTC']
    
    return jsonify(cache_ativos_otc)

@app.route('/api/selecionar-ativo', methods=['POST'])
def selecionar_ativo():
    global ativo_atual, historico_velas, thread_atualizacao, ultima_vela_analisada
    
    data = request.json
    novo_ativo = data.get('ativo')
    
    if novo_ativo:
        ativo_atual = novo_ativo
        historico_velas.clear() # Limpa histórico anterior
        gerente_estrategia.resetar() # Reseta estratégias para o novo ativo
        ultima_vela_analisada = None
        
        # Pega horário do servidor para referência precisa
        ts_server = api.get_server_timestamp()
        
        # Carrega as 750 velas iniciais (histórico aumentado conforme solicitado)
        velas_raw = api.get_candles(ativo_atual, 60, 750, ts_server)
        
        # Filtragem Inteligente: Remove apenas se for realmente a vela viva
        # A vela atual começa em: (ts_server // 60) * 60
        ts_inicio_atual = (ts_server // 60) * 60
        
        velas_fechadas = []
        for v in velas_raw:
            # Só adiciona se o timestamp da vela for ANTERIOR ao inicio da vela atual
            if v['from'] < ts_inicio_atual:
                velas_fechadas.append(v)
        
        for v in velas_fechadas:
            historico_velas.append(formatar_vela(v, ativo_atual))
            
        if historico_velas:
            ultima_vela_analisada = historico_velas[-1]['fromTimestamp']
            
        # Inicia a thread de monitoramento se não existir
        if thread_atualizacao is None or not thread_atualizacao.is_alive():
            thread_atualizacao = threading.Thread(target=loop_atualizacao_velas, daemon=True)
            thread_atualizacao.start()
            
        return jsonify({"status": "ok", "mensagem": f"Monitorando {ativo_atual}", "total_carregado": len(historico_velas)})
    
    return jsonify({"erro": "Ativo inválido"}), 400

@app.route('/api/ia/mensagens')
def get_ia_mensagens():
    """Retorna mensagens de log da IA Groq."""
    msgs = ia_brain.obter_mensagens()
    return jsonify(msgs)

@app.route('/api/historico')
def get_historico():
    return jsonify(list(historico_velas))

@app.route('/api/placar-geral')
def get_placar_geral():
    """
    Retorna o placar geral somando os resultados da sessão de cada estratégia.
    Isso garante que o total bata com a soma dos cards laterais.
    """
    # Retorna os contadores globais controlados pelo Gerente (evita duplicação em consensos)
    return jsonify({
        "wins": gerente_estrategia.global_wins,
        "loss": gerente_estrategia.global_loss,
        "ia_acertos_bloqueio": score_ia['acertos_bloqueio'],
        "ia_erros_bloqueio": score_ia['erros_bloqueio']
    })

@app.route('/api/tendencia')
def get_tendencia():
    """Retorna a tendência atual baseada na SMA 20"""
    # Converte o deque para lista para processamento
    tendencia = gerente_estrategia.detectar_tendencia(list(historico_velas))
    return jsonify({"tendencia": tendencia})

@app.route('/api/status-estrategias')
def get_status_estrategias():
    # Ordena: Active (0) > Waiting (1) > Idle (2)
    prioridade = {'active': 0, 'waiting': 1, 'idle': 2}
    
    resultado = []
    for k, v in gerente_estrategia.estrategias.items():
        item = v.copy()
        item['id'] = k
        
        # Modo Fantasma desativado: Todas as estratégias são consideradas operacionais
        item['is_ghost'] = False
        
        resultado.append(item)

    # Ordena por status e depois por nome
    resultado.sort(key=lambda x: (prioridade.get(x['status'], 2), x['nome']))
    
    return jsonify(resultado)

@app.route('/api/estrategias')
def get_estrategias_raw():
    """Retorna o dicionário completo das estratégias (Wins, Loss, Config)"""
    return jsonify(gerente_estrategia.estrategias)

@app.route('/api/saldo')
def get_saldo():
    """Retorna o saldo e o tipo de conta atual"""
    resultado = gerente_financas.obter_saldo(api)
    if "erro" in resultado:
        return jsonify(resultado), 500
    return jsonify(resultado)

@app.route('/api/alterar-conta', methods=['POST'])
def alterar_conta():
    """Troca entre conta REAL e PRACTICE"""
    tipo = request.json.get('tipo') # Espera 'REAL' ou 'PRACTICE'
    resultado = gerente_financas.alterar_conta(api, tipo)
    if "erro" in resultado:
        return jsonify(resultado), 500
    return jsonify(resultado)

@app.route('/api/definir-valor', methods=['POST'])
def definir_valor():
    dados = request.json
    resultado = gerente_financas.definir_valor_entrada(dados.get('valor'))
    return jsonify(resultado)

@app.route('/api/tipo-opcao', methods=['GET', 'POST'])
def gerenciar_tipo_opcao():
    global tipo_opcao
    if request.method == 'POST':
        data = request.json
        novo_tipo = data.get('tipo')
        if novo_tipo in ['BLITZ', 'BINARY', 'DIGITAL']:
            tipo_opcao = novo_tipo
            print(f"Modo de Operação alterado para: {tipo_opcao}")
            return jsonify({"status": "ok", "tipo": tipo_opcao})
        return jsonify({"erro": "Tipo inválido"}), 400
    return jsonify({"tipo": tipo_opcao})

@app.route('/api/toggle-trading', methods=['POST'])
def toggle_trading():
    global trading_enabled
    data = request.json
    if 'estado' in data:
        trading_enabled = bool(data['estado'])
    else:
        trading_enabled = not trading_enabled
    
    status = "ATIVADO" if trading_enabled else "DESATIVADO"
    print(f"--- TRADING {status} ---")
    return jsonify({"status": "ok", "enabled": trading_enabled})

@app.route('/api/trading-status')
def get_trading_status():
    return jsonify({"enabled": trading_enabled})

@app.route('/api/config/tendencia', methods=['GET', 'POST'])
def config_tendencia():
    if request.method == 'POST':
        data = request.json
        novo_periodo = int(data.get('periodo', 20))
        gerente_estrategia.config_tendencia['periodo'] = novo_periodo
        gerente_estrategia.salvar_stats() # Salva alteração no disco
        return jsonify({"status": "ok", "periodo": novo_periodo})
    return jsonify(gerente_estrategia.config_tendencia)

@app.route('/api/config/assertividade', methods=['GET', 'POST'])
def config_assertividade():
    if request.method == 'POST':
        data = request.json
        novo_valor = int(data.get('valor', 60))
        gerente_estrategia.min_assertividade = novo_valor
        gerente_estrategia.salvar_stats() # Salva alteração no disco
        return jsonify({"status": "ok", "valor": novo_valor})
    return jsonify({"valor": gerente_estrategia.min_assertividade})

@app.route('/api/config/estrategia', methods=['POST'])
def config_estrategia():
    data = request.json
    nome = data.get('nome')
    config = data.get('config')
    if nome in gerente_estrategia.estrategias:
        gerente_estrategia.estrategias[nome]['config'].update(config)
        gerente_estrategia.salvar_stats() # Salva alteração no disco
        return jsonify({"status": "ok", "msg": f"Configuração de {nome} atualizada."})
    return jsonify({"erro": "Estratégia não encontrada"}), 404

@app.route('/api/config/resetar', methods=['POST'])
def resetar_config_geral():
    gerente_estrategia.resetar_para_padrao()
    return jsonify({"status": "ok", "msg": "Todas as estratégias foram resetadas para o padrão de fábrica."})

def start_server():
    app.run(host='127.0.0.1', port=5000, threaded=True, use_reloader=False)

if __name__ == '__main__':
    # Inicia o servidor Flask em uma thread separada (background)
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # Inicia thread de checagem de resultados
    t_res = threading.Thread(target=loop_checagem_resultados, daemon=True)
    t_res.start()

    # Loop de Estudo da IA Aluna (Roda a cada 10 minutos)
    def loop_estudo_aluna():
        while True:
            time.sleep(600) # 10 minutos (Revertido para padrão)
            ia_aluna.estudar_professor()
            
    threading.Thread(target=loop_estudo_aluna, daemon=True).start()

    # Cria a janela nativa da aplicação
    webview.create_window('Tela de Status', 'http://127.0.0.1:5000', width=1000, height=700)
    webview.start()
