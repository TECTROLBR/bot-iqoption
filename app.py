import time
import threading
import os
import logging
import webview
from collections import deque
from flask import Flask, render_template, jsonify, request
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
from financas import GerenteFinancas
from telegram_reporter import TelegramReporter

app = Flask(__name__)
app.json.sort_keys = False # Garante que o JSON respeite a ordem de prioridade (Flask 3.x)

# Desativa logs de requisição do Flask (Werkzeug) para limpar o console
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# --- CONFIGURAÇÕES ---
# IMPORTANTE: Substitua pelas suas credenciais ou use variáveis de ambiente
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Variáveis Globais
api = None
historico_velas = deque(maxlen=50) # Reduzido para 50 conforme solicitado
ativo_atual = None
thread_atualizacao = None
cache_ativos_otc = []
ultima_vela_analisada = None
window = None # Referência global para a janela
ultima_vela_viva_id = None # Controle para detectar nascimento da vela

gerente_financas = GerenteFinancas()
telegram_reporter = TelegramReporter(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, gerente_financas)

def conectar_api():
    global api
    if api is None:
        print("Inicializando nova instância da API...")
        api = IQ_Option(EMAIL, PASSWORD)
    
    print("Tentando conectar...")
    check, reason = api.connect()
    if check:
        print("Conectado com sucesso!")
        try:
            api.update_ACTIVES_OPCODE() # Atualiza lista interna de ativos para evitar erros no get_candles
            api.change_balance("PRACTICE") # Força uma chamada inicial para validar
        except Exception as e:
            print(f"Erro ao definir conta Practice: {e}")
    else:
        print(f"Erro na conexão: {reason}")
    return check

def garantir_conexao():
    """Verifica se a API está conectada e tenta reconectar se necessário."""
    global api
    if api is None or not api.check_connect():
        print("⚠️ Conexão perdida ou inexistente. Tentando reconectar...")
        return conectar_api()
    return True

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

def detectar_tendencia(historico, periodo=20):
    """Calcula a tendência baseada na SMA (Simple Moving Average)"""
    if len(historico) < periodo:
        return "INDETERMINADO"
    
    # Pega os fechamentos das últimas X velas
    fechamentos = [v['close'] for v in list(historico)[-periodo:]]
    media = sum(fechamentos) / periodo
    preco_atual = historico[-1]['close']
    
    if preco_atual > media:
        return "ALTA"
    elif preco_atual < media:
        return "BAIXA"
    return "LATERAL"

def verificar_baixa_liquidez(historico, num_velas=3):
    """
    Detecta se o mercado está em 'linha reta' (baixa liquidez/dojis seguidos).
    Retorna True se o mercado estiver parado (perigoso para operar).
    """
    if len(historico) < num_velas:
        return False

    ultimas = list(historico)[-num_velas:]
    
    # Calcula a média do tamanho dos corpos (Open - Close)
    soma_corpos = sum(abs(v['close'] - v['open']) for v in ultimas)
    media_corpos = soma_corpos / num_velas
    
    # Se a média dos corpos for menor que 2 pontos (0.00010), é linha reta/doji
    if media_corpos < 0.00010:
        return True
        
    return False

def analisar_sinal_indicador(historico):
    """
    AQUI VAI A LÓGICA DO SEU INDICADOR/SCRIPT.
    Analisa o histórico e retorna "CALL", "PUT" ou None.
    """
    # O script "JUST Win" olha até a vela 8 (close[8]), então precisamos de pelo menos 10 velas
    if len(historico) < 10:
        return None

    # --- FILTRO DE LIQUIDEZ (LINHA RETA) ---
    if verificar_baixa_liquidez(historico):
        return None # Mercado morto, ignora qualquer sinal

    # Mapeamento do Script Lua para Python:
    # close (atual/última fechada) -> historico[-1]
    # close[2] -> historico[-3]
    # open[2]  -> historico[-3]
    # close[4] -> historico[-5]
    # close[8] -> historico[-9]
    
    h = historico
    close_0 = h[-1]['close']
    close_2 = h[-3]['close']
    open_2  = h[-3]['open']
    close_4 = h[-5]['close']
    close_8 = h[-9]['close']
    
    # Lógica de COMPRA (Bull_OTC)
    # if ((close > close[2]) and (close[2] > open[2]) and (close[4] > close[8]))
    if (close_0 > close_2) and (close_2 > open_2) and (close_4 > close_8):
        print(f"💎 SINAL JUST WIN: Padrão de COMPRA detectado")
        return "CALL"

    # Lógica de VENDA (Bear_OTC)
    # if ((close < close[2]) and (close[2] < open[2]) and (close[4] < close[8]))
    if (close_0 < close_2) and (close_2 < open_2) and (close_4 < close_8):
        print(f"💎 SINAL JUST WIN: Padrão de VENDA detectado")
        return "PUT"
        
    return None

def executar_entrada(ativo, direcao):
    """Envia a ordem para a IQ Option"""
    global api, gerente_financas, telegram_reporter
    
    valor = gerente_financas.valor_aposta
    expiracao = 1 # 1 Minuto (Binária/Turbo)
    
    print(f"🚀 ENVIANDO ORDEM: {direcao} em {ativo} | Valor: ${valor} | Exp: {expiracao}m")

    # Registra que uma operação foi tentada (para o relatório do Telegram)
    telegram_reporter.registrar_operacao()
    
    # Envia a ordem (buy retorna: check, id_da_ordem)
    status, id_ordem = api.buy(valor, ativo, direcao, expiracao)
    
    if status:
        print(f"✅ Ordem Executada com Sucesso! ID: {id_ordem}")
    else:
        print(f"❌ Falha ao executar ordem: {id_ordem}")

def loop_atualizacao_velas():
    """
    Loop simples: Busca velas e atualiza o histórico para a tabela.
    """
    global ativo_atual, historico_velas, ultima_vela_analisada, ultima_vela_viva_id

    while True:
        if not api or not api.check_connect() or not ativo_atual:
            time.sleep(0.5)
            continue

        try:
            server_time = api.get_server_timestamp()
            if server_time is None:
                server_time = int(time.time()) # Fallback para não travar o loop de velas

            # -----------------------------------------------------------------
            # ATUALIZAÇÃO DO HISTÓRICO (Velas de 1M)
            # -----------------------------------------------------------------
            # Busca velas de 60 segundos (periodo=60)
            velas = api.get_candles(ativo_atual, 60, 3, server_time)
            if velas:
                # --- DETECÇÃO DE NASCIMENTO DE VELA (VELA VIVA) ---
                vela_viva = velas[-1] # A última é a que está se formando
                
                # Se o ID mudou, significa que uma nova vela nasceu
                if ultima_vela_viva_id != vela_viva['id']:
                    ultima_vela_viva_id = vela_viva['id']
                    
                    # A vela anterior (penúltima) acabou de fechar
                    if len(velas) >= 2:
                        vela_fechada_nova = velas[-2]
                        
                        dados_formatados = formatar_vela(vela_fechada_nova, ativo_atual)
                        
                        # Evita duplicatas e atualiza histórico
                        if not historico_velas or historico_velas[-1]['id'] != dados_formatados['id']:
                            historico_velas.append(dados_formatados)
                            print(f"\n--- 1M | NOVA VELA NASCEU ({vela_viva['id']}) | Fechou: {dados_formatados['horario_formatado']} ---")
                            
                            # --- GATILHO IMEDIATO: Analisa e Opera ---
                            sinal = analisar_sinal_indicador(list(historico_velas))
                            if sinal:
                                print(f"⚡ SINAL RÁPIDO DETECTADO: {sinal}")
                                threading.Thread(target=executar_entrada, args=(ativo_atual, sinal)).start()
                            
                            ultima_vela_analisada = vela_fechada_nova['from']

        except Exception as e:
            print(f"Erro no loop 30s: {e}")
        
        time.sleep(1) # Aumentado para 1s para evitar desconexões por excesso de requisições

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ativos-otc')
def get_ativos_otc():
    """Retorna lista estática de ativos OTC para evitar erros de API."""
    # Lista fixa de ativos OTC mais comuns para garantir estabilidade
    # Isso evita que o robô tente buscar ativos inválidos ou fechados
    lista_otc = [
        {"ativo": "EURUSD-OTC", "payout": 91},
        {"ativo": "GBPUSD-OTC", "payout": 91},
        {"ativo": "USDJPY-OTC", "payout": 91},
        {"ativo": "AUDCAD-OTC", "payout": 89},
        {"ativo": "NZDUSD-OTC", "payout": 89},
        {"ativo": "USDCHF-OTC", "payout": 89},
        {"ativo": "AUDUSD-OTC", "payout": 89},
        {"ativo": "USDCAD-OTC", "payout": 89},
    ]
    return jsonify(lista_otc)

@app.route('/api/selecionar-ativo', methods=['POST'])
def selecionar_ativo():
    global ativo_atual, historico_velas, thread_atualizacao, ultima_vela_analisada
    
    data = request.json
    novo_ativo = data.get('ativo')
    
    if not garantir_conexao():
        return jsonify({"erro": "Falha de conexão com a IQ Option"}), 500

    if novo_ativo:
        ativo_atual = novo_ativo
        historico_velas.clear() # Limpa histórico anterior
        ultima_vela_analisada = None
        
        # Pega horário do servidor para referência precisa
        ts_server = api.get_server_timestamp()
        
        # Mecanismo de retry para sincronização de tempo (até 5 tentativas)
        if ts_server is None or not isinstance(ts_server, int):
            print("⚠️ Sincronizando relógio com o servidor...")
            for i in range(5):
                if not api.check_connect():
                    print("Reconectando durante sincronização...")
                    api.connect()
                ts_server = api.get_server_timestamp()
                if isinstance(ts_server, int):
                    break
                time.sleep(1)
        
        if ts_server is None or not isinstance(ts_server, int):
            print("⚠️ Aviso: Servidor da corretora demorou a responder. Usando o relógio local do computador como referência.")
            ts_server = int(time.time()) # Usa a hora da sua máquina como fallback
            
        # Carrega as 50 velas iniciais de 60 SEGUNDOS (1M)
        try:
            velas_raw = api.get_candles(ativo_atual, 60, 50, ts_server)
        except Exception as e:
            print(f"❌ Erro ao baixar velas de {ativo_atual}: {e}")
            return jsonify({"erro": f"Erro ao carregar gráfico de {ativo_atual}. O ativo pode estar fechado."}), 400
        
        # A vela atual começa em: (ts_server // 60) * 60
        ts_inicio_atual = (ts_server // 60) * 60
        
        # Carrega TODAS as velas (incluindo a viva se houver)
        for v in velas_raw:
            historico_velas.append(formatar_vela(v, ativo_atual))
            
        if historico_velas:
            # Se a última vela for a viva (timestamp == inicio atual), a última analisada é a penúltima
            last = historico_velas[-1]
            if last['fromTimestamp'] == ts_inicio_atual:
                ultima_vela_analisada = historico_velas[-2]['fromTimestamp'] if len(historico_velas) > 1 else None
            else:
                ultima_vela_analisada = last['fromTimestamp']
            
        # Inicia a thread de monitoramento se não existir
        if thread_atualizacao is None or not thread_atualizacao.is_alive():
            thread_atualizacao = threading.Thread(target=loop_atualizacao_velas, daemon=True)
            thread_atualizacao.start()
            
        return jsonify({"status": "ok", "mensagem": f"Monitorando {ativo_atual}", "total_carregado": len(historico_velas)})
    
    return jsonify({"erro": "Ativo inválido"}), 400

@app.route('/api/tempo-vela')
def get_tempo_vela():
    """Retorna o tempo restante para o fechamento da vela de 1 minuto."""
    if not api or not api.check_connect(): return jsonify({"restante": 0, "erro": "API não conectada"})
    try:
        ts = api.get_server_timestamp()
    except Exception:
        ts = None
        
    if ts is None:
        ts = int(time.time()) # Usa a máquina local para não zerar o cronômetro do front-end
    restante = int(60 - (ts % 60)) # Ajustado para 60s (1M)
    return jsonify({"restante": restante})

@app.route('/api/historico')
def get_historico():
    # Cria uma cópia da lista de velas fechadas
    hist_list = list(historico_velas)
    
    # Se a API estiver conectada e um ativo selecionado, busca a vela viva
    if api and api.check_connect() and ativo_atual:
        try:
            # Pega a vela que está se formando AGORA (count=1)
            velas_live = api.get_candles(ativo_atual, 60, 1, api.get_server_timestamp())
            if velas_live:
                v_live = velas_live[0]
                
                # Garante que a vela viva não é a última vela já fechada no histórico
                # (evita duplicata no segundo 00)
                if not hist_list or hist_list[-1]['id'] != v_live['id']:
                    # Adiciona a vela viva no final da lista APENAS para o frontend
                    hist_list.append(formatar_vela(v_live, ativo_atual))
        except Exception as e:
            print(f"Erro ao buscar vela viva para o histórico do frontend: {e}")
            
    return jsonify(hist_list)

@app.route('/api/tendencia')
def get_tendencia():
    """Retorna a tendência atual baseada na SMA 20"""
    # Converte o deque para lista para processamento
    tendencia = detectar_tendencia(list(historico_velas))
    return jsonify({"tendencia": tendencia})

@app.route('/api/saldo')
def get_saldo():
    """Retorna o saldo e o tipo de conta atual"""
    if not garantir_conexao():
        return jsonify({"erro": "Reconectando..."}), 503
    resultado = gerente_financas.obter_saldo(api)
    if "erro" in resultado:
        return jsonify(resultado), 500
    return jsonify(resultado)

@app.route('/api/alterar-conta', methods=['POST'])
def alterar_conta():
    """Troca entre conta REAL e PRACTICE"""
    if not garantir_conexao():
        return jsonify({"erro": "Sem conexão"}), 500
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

@app.route('/api/telegram/status')
def telegram_status():
    """Rota para testar o envio de mensagens do Telegram"""
    if telegram_reporter.ativo:
        telegram_reporter.send_message("🔔 *Status*: O Robô está conectado e operando! 🚀")
        return jsonify({"status": "ok", "mensagem": "Mensagem de teste enviada para o Telegram."})
    else:
        return jsonify({"status": "erro", "mensagem": "Telegram não está configurado ou ativo."}), 400

def start_server():
    app.run(host='127.0.0.1', port=5000, threaded=True, use_reloader=False)

if __name__ == '__main__':
    try:
        # Inicia o servidor Flask em uma thread separada (background)
        t = threading.Thread(target=start_server)
        t.daemon = True
        t.start()
        
        # Inicia a thread de relatórios do Telegram
        t_telegram = threading.Thread(target=telegram_reporter.loop_relatorio_horario, daemon=True)
        t_telegram.start()
        
        # Cria a janela nativa da aplicação
        print("🚀 Iniciando interface gráfica...")
        window = webview.create_window('Tela de Status', 'http://127.0.0.1:5000', width=1000, height=700)
        webview.start()
    except Exception as e:
        print("\n--- 🚨 ERRO CRÍTICO AO INICIAR A APLICAÇÃO 🚨 ---")
        print(f"Ocorreu um erro que impediu a janela de abrir: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para fechar...")
