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
    return "Monitor Automático SFL (Crops + Frutas) Online!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

# 2. CONFIGURAÇÃO DO TELEGRAM E JOGO
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8779097957:AAEDGqwe5FQfbUQZI-IC4yBN87_ru9C1ccQ")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", 5303286197))
FARM_ID = 163523  # Sua fazenda cadastrada fixa

bot = telebot.TeleBot(TOKEN, threaded=False)

# Banco de dados temporário na memória para os alarmes
terrenos_monitorados = {}

# Tempos das suas culturas/frutas em segundos (padrão do jogo)
TEMPOS = {
    "cenoura": 3420,          # 57 min
    "tomate": 6480,           # 1h 48min (Fruta) 🍅
    "arvore": 7200,           # 2h
    "milho": 61560,           # 17h 6min
    "trigo": 73860,           # 20h 31min
    "couve": 108000,          # 1 dia e 6h
    "barley": 147600          # 1 dia e 17h
}

def checar_fazenda_loop():
    """Roda de 2 em 2 minutos checando a API do jogo"""
    print(f"🕵️‍♂️ Iniciando monitoramento automático completo da fazenda {FARM_ID}...")
    url_api = f"https://sunflower-land.com{FARM_ID}"
    
    while True:
        try:
            resposta = requests.get(url_api, timeout=15)
            if resposta.status_code == 200:
                dados = resposta.json()
                fazenda_estado = dados.get("state", {})
                tempo_atual = int(time.time())
                
                # -----------------------------------------------------------
                # MONITORAMENTO 1: PLANTAÇÕES COMUNS (Crops)
                # -----------------------------------------------------------
                terrenos_comuns = fazenda_estado.get("crops", {})
                for terreno_id, info_terreno in terrenos_comuns.items():
                    planta_atual = info_terreno.get("crop", {}).get("name")
                    data_plantio = info_terreno.get("crop", {}).get("plantedAt")
                    
                    if planta_atual and data_plantio:
                        planta_nome = planta_atual.lower()
                        data_plantio_segundos = data_plantio // 1000
                        id_unico_plantio = f"comum_{terreno_id}_{data_plantio_segundos}"
                        
                        if planta_nome in TEMPOS and id_unico_plantio not in terrenos_monitorados:
                            tempo_total = TEMPOS[planta_nome]
                            tempo_colheita = data_plantio_segundos + tempo_total
                            
                            terrenos_monitorados[id_unico_plantio] = {
                                "planta": planta_nome,
                                "colheita_em": tempo_colheita,
                                "notificado": False
                            }
                            print(f"🌱 Novo plantio comum detectado: {planta_nome.capitalize()}")

                # -----------------------------------------------------------
                # MONITORAMENTO 2: CANTEIROS DE FRUTAS (Fruit Patches - ex: Tomate)
                # -----------------------------------------------------------
                canteiros_frutas = fazenda_estado.get("fruitPatches", {})
                for patch_id, info_patch in canteiros_frutas.items():
                    fruta_atual = info_patch.get("fruit", {}).get("name")
                    data_plantio_fruta = info_patch.get("fruit", {}).get("plantedAt")
                    
                    if fruta_atual and data_plantio_fruta:
                        fruta_nome = fruta_atual.lower()
                        data_segundos = data_plantio_fruta // 1000
                        id_unico_fruta = f"fruta_{patch_id}_{data_segundos}"
                        
                        if fruta_nome in TEMPOS and id_unico_fruta not in terrenos_monitorados:
                            tempo_total = TEMPOS[fruta_nome]
                            tempo_colheita = data_segundos + tempo_total
                            
                            terrenos_monitorados[id_unico_fruta] = {
                                "planta": fruta_nome,
                                "colheita_em": tempo_colheita,
                                "notificado": False
                            }
                            print(f"🍅 Nova fruta detectada no Fruit Patch: {fruta_nome.capitalize()}")
                
                # -----------------------------------------------------------
                # VERIFICAÇÃO SE OS ALARMES CHEGARAM AO FIM
                # -----------------------------------------------------------
                for id_plantio, info in list(terrenos_monitorados.items()):
                    if not info["notificado"] and tempo_atual >= info["colheita_em"]:
                        msg = f"🚨 **ALERTA AUTOMÁTICO!**\nSua plantação de **{info['planta'].capitalize()}** na fazenda **#{FARM_ID}** está pronta para colheita! 🌾🍅"
                        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                        info["notificado"] = True
                        
            else:
                print(f"⚠️ Erro ao acessar API do jogo: Status {resposta.status_code}")
                
        except Exception as e:
            print(f"❌ Erro no loop de checagem: {e}")
            
        time.sleep(120)  # Checa a fazenda a cada 2 minutos

@bot.message_handler(commands=['start', 'status'])
def enviar_status(message):
    bot.reply_to(
        message, 
        f"🤖 **Monitor de Visão Ampliada Ativo!**\n\nEstou cuidando das Plantações e das Frutas (Tomates) da Fazenda **#{FARM_ID}**.\nTudo automático!"
    )

if __name__ == '__main__':
    threading.Thread(target=rodar_servidor_web).start()
    threading.Thread(target=checar_fazenda_loop).start()
    
    print("Bot com rastreador completo (Crops + Fruit) iniciado!")
    bot.infinity_polling()
                
