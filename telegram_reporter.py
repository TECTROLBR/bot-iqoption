import requests
import time
import threading

class TelegramReporter:
    def __init__(self, token, chat_id, financas_manager):
        self.token = token
        self.chat_id = chat_id
        self.financas = financas_manager
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        self.operacoes_na_hora = 0
        self.lucro_inicio_hora = 0.0
        self._lock = threading.Lock()

        if not token or not chat_id or "SEU_TOKEN_AQUI" in token:
            print("⚠️ Aviso: Token ou Chat ID do Telegram não configurado. Relatórios desativados.")
            self.ativo = False
        else:
            self.ativo = True

    def send_message(self, message):
        if not self.ativo:
            return

        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        try:
            response = requests.post(self.base_url, data=payload, timeout=10)
            if response.status_code == 200:
                print("✅ Relatório enviado para o Telegram com sucesso!")
            else:
                print(f"❌ Erro ao enviar relatório para o Telegram: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Erro de conexão ao enviar para o Telegram: {e}")

    def registrar_operacao(self):
        with self._lock:
            self.operacoes_na_hora += 1

    def _gerar_relatorio(self):
        with self._lock:
            lucro_total_sessao = self.financas.lucro_sessao
            lucro_da_hora = lucro_total_sessao - self.lucro_inicio_hora

            message = (
                f"🤖 *Relatório Horário do Robô*\n"
                f"-----------------------------------\n"
                f"📈 *Operações na última hora:* `{self.operacoes_na_hora}`\n"
                f"💰 *Lucro/Prejuízo na hora:* `${lucro_da_hora:,.2f}`\n"
                f"-----------------------------------\n"
                f"📊 *Lucro Total da Sessão:* `${lucro_total_sessao:,.2f}`\n"
            )

            self.operacoes_na_hora = 0
            self.lucro_inicio_hora = lucro_total_sessao
            return message

    def loop_relatorio_horario(self):
        if not self.ativo:
            return
        print("📡 Serviço de relatório do Telegram iniciado. Enviando a cada hora.")
        time.sleep(5)
        with self._lock:
            self.lucro_inicio_hora = self.financas.lucro_sessao
        while True:
            time.sleep(3600)
            relatorio_msg = self._gerar_relatorio()
            self.send_message(relatorio_msg)