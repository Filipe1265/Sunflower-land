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
    return "Monitor Blockchain SFL Online!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

# 2. CONFIGURAÇÃO DO TELEGRAM E JOGO
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8779097957:AAEDGqwe5FQfbUQZI-IC4yBN87_ru9C1ccQ")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", 5303286197))
FARM_ID = 163523  # Sua fazenda fixa

bot = telebot.TeleBot(TOKEN, threaded=False)
terrenos_monitorados = {}

# Tabela oficial de tempos do jogo em segundos
TEMPOS = {
    "sunflower": 60, "potato": 300, "pumpkin": 1800, "carrot": 3420,
    "cabbage": 7200, "beetroot": 14400, "cauliflower": 28800, "parsnip": 43200,
    "radish": 86400, "wheat": 73860, "corn": 61560, "barley": 147600,
    "tomato": 6480, "blueberry": 14400, "orange": 28800, "apple": 86400, "banana": 43200
}

TRADUCAO = {
    "sunflower": "Girassol", "potato": "Batata", "pumpkin": "Abóbora", "carrot": "Cenoura",
    "cabbage": "Repolho", "beetroot": "Beterraba", "cauliflower": "Couve", "parsnip": "Parsnip",
    "radish": "Rabanete", "wheat": "Trigo", "corn": "Milho", "barley": "Barley (Cevada)",
    "tomato": "Tomate 🍅", "blueberry": "Mirtilo 🫐", "orange": "Laranja 🍊", "apple": "Maçã 🍎", "banana": "Banana 🍌"
}

def checar_fazenda_loop():
    print(f"🕵️‍♂️ [SISTEMA] Iniciando monitoramento automático completo da fazenda {FARM_ID}...")
    
    # CORREÇÃO: URL restaurada com o caminho oficial da API pública do jogo
    url_api = f"https://sunflower-land.com{FARM_ID}"
    
    while True:
        print("🔄 [LOG] Fazendo varredura na fazenda...")
        try:
            resposta = requests.get(url_api, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            print(f"📡 [LOG] Resposta recebida da rede. Status: {resposta.status_code}")
            
            if resposta.status_code == 200:
                dados = resposta.json()
                fazenda_estado = dados.get("state", {})
                tempo_atual = int(time.time())
                
                # 1. PLANTAÇÕES COMUNS
                terrenos_comuns = fazenda_estado.get("crops", {})
                for terreno_id, info_terreno in terrenos_comuns.items():
                    crop_data = info_terreno.get("crop")
                    if crop_data:
                        planta_atual = crop_data.get("name")
                        data_plantio = crop_data.get("plantedAt")
                        
                        if planta_atual and data_plantio:
                            planta_nome = planta_atual.lower().replace(" seed", "").strip()
                            data_plantio_segundos = data_plantio // 1000
                            id_unico = f"comum_{terreno_id}_{data_plantio_segundos}"
                            
                            if planta_nome in TEMPOS and id_unico not in terrenos_monitorados:
                                tempo_colheita = data_plantio_segundos + TEMPOS[planta_nome]
                                terrenos_monitorados[id_unico] = {"planta": planta_nome, "colheita_em": tempo_colheita, "notificado": False}
                                print(f"🌱 [DETECTADO] Plantio de {planta_nome.capitalize()} encontrado no campo {terreno_id}.")

                # 2. CANTEIROS DE FRUTAS (Tomate)
                canteiros_frutas = fazenda_estado.get("fruitPatches", {})
                for patch_id, info_patch in canteiros_frutas.items():
                    fruit_data = info_patch.get("fruit")
                    if fruit_data:
                        fruta_atual = fruit_data.get("name")
                        data_plantio_fruta = fruit_data.get("plantedAt")
                        
                        if fruta_atual and data_plantio_fruta:
                            fruta_nome = fruta_atual.lower().replace(" seed", "").strip()
                            data_segundos = data_plantio_fruta // 1000
                            id_unico = f"fruta_{patch_id}_{data_segundos}"
                            
                            if fruta_nome in TEMPOS and id_unico not in terrenos_monitorados:
                                tempo_colheita = data_segundos + TEMPOS[fruta_nome]
                                terrenos_monitorados[id_unico] = {"planta": fruta_nome, "colheita_em": tempo_colheita, "notificado": False}
                                print(f"🍅 [DETECTADO] Fruta {fruta_nome.capitalize()} encontrada no canteiro {patch_id}.")
                
                # 3. DISPARO DOS ALARMES
                for id_plantio, info in list(terrenos_monitorados.items()):
                    if not info["notificado"] and tempo_atual >= info["colheita_em"]:
                        nome_exibicao = TRADUCAO.get(info["planta"], info["planta"].capitalize())
                        msg = f"🚨 **ALERTA AUTOMÁTICO!**\nSua plantação de **{nome_exibicao}** na fazenda **#{FARM_ID}** está pronta para colheita! 🌾🍅🌻"
                        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                        info["notificado"] = True
                        print(f"📢 [NOTIFICADO] Mensagem enviada para {info['planta']}.")
            else:
                print(f"⚠️ [AVISO] API retornou erro status {resposta.status_code}. Aguardando próxima checagem...")
                
        except Exception as e:
            print(f"❌ [ERRO] Falha crítica na leitura: {e}")
            
        time.sleep(120)  # Checa a cada 2 minutos

# CORREÇÃO: Função do comando /status adicionada de volta com log de verificação
@bot.message_handler(commands=['start', 'status'])
def enviar_status(message):
    print("📥 [TELEGRAM] Comando /status recebido com sucesso no chat!")
    bot.reply_to(
        message, 
        f"🤖 **Monitor Automático Online!**\n\nEstou cuidando das Plantações e das Frutas da Fazenda **#{FARM_ID}** 24h por dia sem parar!"
    )

if __name__ == '__main__':
    # 1. Abre o servidor Web para o Render ficar feliz (Prioridade 1)
    t_web = threading.Thread(target=rodar_servidor_web)
    t_web.daemon = True
    t_web.start()
    
    # 2. Inicia o espião da fazenda em uma thread totalmente isolada e segura (Prioridade 2)
    t_monitor = threading.Thread(target=checar_fazenda_loop)
    t_monitor.daemon = True
    t_monitor.start()
    
    # 3. Dá 5 segundos de folga para o sistema respirar antes de ligar o Telegram
    time.sleep(5)
    
    # 4. Lança o polling do Telegram na linha principal (Garante que ele responda e não congele)
    print("🚀 [SISTEMA] Bot e Rastreador integrados com sucesso. Conectando ao Telegram...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
