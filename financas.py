import threading

class GerenteFinancas:
    def __init__(self):
        self.valor_aposta = 2  # Defina aqui o valor da sua entrada (Min 2 BRL)
        self.saldo_inicial = None
        self.lucro_sessao = 0.0
        self._lock = threading.Lock()

    def obter_saldo(self, api):
        """Retorna o saldo e o tipo de conta atual"""
        if not api:
            return {"erro": "API desconectada"}

        # Pega o saldo da conta ativa
        saldo = api.get_balance()
        
        # Validação de segurança: se a API ainda não carregou o saldo
        if saldo is None:
            return {"erro": "Saldo indisponível"}
            
        # Descobre qual modo está ativo (PRACTICE ou REAL)
        modo = api.get_balance_mode()

        with self._lock:
            # Se for a primeira vez rodando (ou após troca de conta), define o marco inicial
            if self.saldo_inicial is None:
                self.saldo_inicial = saldo

            # Calcula o lucro da sessão (Saldo Atual - Saldo Inicial)
            lucro_atual = saldo - self.saldo_inicial
            self.lucro_sessao = lucro_atual
            valor_aposta_atual = self.valor_aposta

        return {
            "saldo": saldo,
            "modo": modo,
            "lucro": lucro_atual,
            "valor_aposta": valor_aposta_atual
        }

    def alterar_conta(self, api, tipo):
        """Troca entre conta REAL e PRACTICE"""
        if not api:
            return {"erro": "API desconectada"}

        api.change_balance(tipo)
        with self._lock:
            # Reseta o saldo inicial para recalcular o lucro baseada na nova conta
            self.saldo_inicial = None
        return self.obter_saldo(api)

    def validar_gestao_risco(self, valor, saldo):
        """Verifica se o valor da aposta respeita o gerenciamento"""
        # Retorna sempre True para permitir operações com banca pequena (Min 2 BRL)
        return True

    def definir_valor_entrada(self, valor):
        """Define o novo valor da aposta"""
        try:
            novo_valor = float(valor)
            if novo_valor <= 0:
                return {"erro": "O valor deve ser maior que zero."}
            with self._lock:
                # Verifica risco se tivermos saldo carregado
                if self.saldo_inicial and self.saldo_inicial > 0:
                    # Usa saldo inicial ou atual? Idealmente atual, mas aqui usamos o cacheado
                    # para aviso rápido.
                    if not self.validar_gestao_risco(novo_valor, self.saldo_inicial):
                        return {"erro": f"⚠️ Risco Alto! ${novo_valor} é > 2% do capital."}
                self.valor_aposta = novo_valor
                return {"status": "ok", "novo_valor": self.valor_aposta}
        except ValueError:
            return {"erro": "Valor inválido."}

    def autorizar_operacao(self, sinais):
        """Contabiliza votos de CALL e PUT e decide a operação"""
        if not sinais:
            return None
            
        # Extrai direções e expirações
        votos_call = 0
        votos_put = 0
        exps_call = []
        exps_put = []
        strats_call = []
        strats_put = []

        for s in sinais:
            if s['sinal'] == "CALL":
                votos_call += 1
                exps_call.append(s['expiracao'])
                strats_call.append(s['nome']) # Guarda nome da estratégia
            elif s['sinal'] == "PUT":
                votos_put += 1
                exps_put.append(s['expiracao'])
                strats_put.append(s['nome'])
        
        if votos_call > votos_put:
            print(f"--- VOTAÇÃO VENCIDA POR CALL ({votos_call} vs {votos_put}) ---")
            return {"sinal": "CALL", "expiracao": max(exps_call), "estrategias": strats_call}
        elif votos_put > votos_call:
            print(f"--- VOTAÇÃO VENCIDA POR PUT ({votos_put} vs {votos_call}) ---")
            return {"sinal": "PUT", "expiracao": max(exps_put), "estrategias": strats_put}
        
        if votos_call > 0 or votos_put > 0:
            print(f"--- EMPATE NA VOTAÇÃO ({votos_call} vs {votos_put}) - NENHUMA AÇÃO ---")
            
        return None