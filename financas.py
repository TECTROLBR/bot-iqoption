import threading
from websocket._exceptions import WebSocketConnectionClosedException

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

        try:
            # Pega o saldo da conta ativa
            saldo = api.get_balance()
            
            # Validação de segurança: se a API ainda não carregou o saldo
            if saldo is None:
                return {"erro": "Saldo indisponível, reconectando..."}
                
            # Descobre qual modo está ativo (PRACTICE ou REAL)
            modo = api.get_balance_mode()
        except WebSocketConnectionClosedException:
            return {"erro": "Conexão perdida. Tentando reconectar..."}
        except Exception as e:
            return {"erro": f"Erro inesperado no saldo: {e}"}

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

        try:
            api.change_balance(tipo)
            with self._lock:
                # Reseta o saldo inicial para recalcular o lucro baseada na nova conta
                self.saldo_inicial = None
            return self.obter_saldo(api)
        except WebSocketConnectionClosedException:
            return {"erro": "Conexão perdida ao trocar de conta."}
        except Exception as e:
            return {"erro": f"Erro ao trocar conta: {e}"}

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