import os
import time
import threading
import requests
from flask import Flask
import telebot

# 1. CONFIGURAÇÃO DO SITE FALSO PARA O RENDER
app = Flask(__name__)

@app.route('/')
def home():
    return "Monitor Automático da Fazenda 163523 Online!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

# 2. CONFIGURAÇÃO DO TELEGRAM E JOGO
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8779097957:AAEDGqwe5FQfbUQZI-IC4yBN87_ru9C1ccQ")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", 5303286197))
FARM_ID = 163523  # <--- Sua fazenda configurada fixa no robô!

bot = telebot.TeleBot(TOKEN, threaded=False)

# Banco de dados temporário na memória para acompanhar o que está plantado
# Estrutura: {id_do_terreno: {"planta": "tomate", "tempo_colheita": 178239281}}
terrenos_monitorados = {}

# Tempos das suas culturas em segundos (padrão do jogo)
TEMPOS = {
    "cenoura": 3420,          # 57 min
    "tomate": 6480,           # 1h 48min
    "arvore": 7200,           # 2h
    "milho": 61560,           # 17h 6min
    "trigo": 73860,           # 20h 31min
    "couve": 108000,          # 1 dia e 6h
    "barley": 147600          # 1 dia e 17h
}

def checar_fazenda_loop():
    """Roda de 2 em 2 minutos checando a API do jogo"""
    print(f"🕵️‍♂️ Iniciando monitoramento automático da fazenda {FARM_ID}...")
    
    # URL pública da API oficial do Sunflower Land para ler fazendas
    url_api = f"https://sunflower-land.com{FARM_ID}"
    
    while True:
        try:
            resposta = requests.get(url_api, timeout=15)
            if resposta.status_code == 200:
                dados = resposta.json()
                
                # Acessa a lista de terrenos (plots) dentro do JSON do jogo
                # Nota: Os nomes exatos das chaves dependem do formato atual da API do SFL
                fazenda_estado = dados.get("state", {})
                terrenos = fazenda_estado.get("crops", {}) # Dicionário de terrenos do jogador
                
                tempo_atual = int(time.time())
                
                for terreno_id, info_terreno in terrenos.items():
                    planta_atual = info_terreno.get("crop", {}).get("name")
                    data_plantio = info_terreno.get("crop", {}).get("plantedAt") # timestamp em milissegundos
                    
                    if planta_atual and data_plantio:
                        planta_nome = planta_atual.lower()
                        data_plantio_segundos = data_plantio // 1000
                        
                        # Verifica se é uma planta cadastrada e se ainda não estamos monitorando este plantio específico
                        id_unico_plantio = f"{terreno_id}_{data_plantio_segundos}"
                        
                        if planta_nome in TEMPOS and id_unico_plantio not in terrenos_monitorados:
                            # Descobre o segundo exato em que vai ficar pronto
                            tempo_total = TEMPOS[planta_nome]
                            tempo_colheita = data_plantio_segundos + tempo_total
                            
                            # Registra o monitoramento
                            terrenos_monitorados[id_unico_plantio] = {
                                "planta": planta_nome,
                                "colheita_em": tempo_colheita,
                                "notificado": False
                            }
                            
                            print(f"🌱 Novo plantio detectado no terreno {terreno_id}: {planta_nome.capitalize()}")
                
                # Varre os plantios registrados para ver se algum ficou pronto
                for id_plantio, info in list(terrenos_monitorados.items()):
                    if not info["notificado"] and tempo_atual >= info["colheita_em"]:
                        # Envia o alerta automático no Telegram!
                        msg = f"🚨 **ALERTA AUTOMÁTICO!**\nSua plantação de **{info['planta'].capitalize()}** na fazenda **#{FARM_ID}** está pronta para colheita! 🌾🍅🌻"
                        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                        info["notificado"] = True
                        
            else:
                print(f"⚠️ Erro ao acessar API do jogo: Status {resposta.status_code}")
                
        except Exception as e:
            print(f"❌ Erro no loop de checagem: {e}")
            
        time.sleep(120) # Espera 2 minutos antes de espiar de novo

# Comandos básicos caso você queira interagir
@bot.message_handler(commands=['start', 'status'])
def enviar_status(message):
    bot.reply_to(message, f"🤖 **Monitor Automático Ativo!**\n\nEstou cuidando da Fazenda **#{FARM_ID}** 24h por dia. Não precisa digitar nada quando plantar, eu aviso aqui!")

if __name__ == '__main__':
    # Linha do Flask para manter o Render feliz
    threading.Thread(target=rodar_servidor_web).start()
    
    # Nova linha que inicia o espião da sua fazenda
    threading.Thread(target=checar_fazenda_loop).start()
    
    print("Bot com rastreador automático iniciado!")
    bot.infinity_polling()
            
