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
    return "Monitor Automático SFL Inteligente Online!"

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

# LISTA ATUALIZADA COM OS NOMES EM INGLÊS EXATOS DO JOGO (E SEUS TEMPOS)
TEMPOS = {
    # Plantações Comuns (Crops)
    "sunflower": 60,          # Girassol (1 min)
    "potato": 300,            # Batata (5 min)
    "pumpkin": 1800,          # Abóbora (30 min)
    "carrot": 3420,           # Cenoura (57 min)
    "cabbage": 7200,          # Repolho (2 horas)
    "beetroot": 14400,        # Beterraba (4 horas)
    "cauliflower": 108000,     # Sua Couve Modificada (1 dia e 6h = 108.000s)
    "parsnip": 43200,         # Pastinaca (12 horas)
    "radish": 86400,          # Rabanete (24 horas)
    "wheat": 73860,           # Trigo (Seu tempo: 20h 31min)
    "corn": 61560,            # Milho (Seu tempo: 17h 6min)
    "barley": 147600,         # Cevada (Seu tempo: 1 dia e 17h)
    
    # Frutas (Fruit Patches)
    "tomato": 6480,           # Tomate (1h 48min) 🍅
    "blueberry": 14400,       # Mirtilo (4 horas) 🫐
    "orange": 28800,          # Laranja (8 horas) 🍊
    "apple": 86400,           # Maçã (24 horas) 🍎
    "banana": 43200,          # Banana (12 horas) 🍌
    
    # Recursos Extra
    "tree": 7200              # Árvore de Madeira (2 horas)
}

# Dicionário de tradução simples apenas para o alerta do Telegram ficar em português
TRADUCAO = {
    "sunflower": "Girassol 🌻", "potato": "Batata 🥔", "pumpkin": "Abóbora 🎃", 
    "carrot": "Cenoura 🥕", "cabbage": "Repolho 🥬", "beetroot": "Beterraba 🪵", 
    "cauliflower": "Couve 🥦", "parsnip": "Parsnip 🥕", "radish": "Rabanete 🫚", 
    "wheat": "Trigo 🌾", "corn": "Milho 🌽", "barley": "Barley 🌾", 
    "tomato": "Tomate 🍅", "blueberry": "Mirtilo 🫐", "orange": "Laranja 🍊", 
    "apple": "Maçã 🍎", "banana": "Banana 🍌", "tree": "Árvore 🪵"
}

def checar_fazenda_loop():
    """Roda de 2 em 2 minutos checando a API do jogo"""
    print(f"🕵️‍♂️ Iniciando monitoramento automático completo da fazenda {FARM_ID}...")
    url_api = f"https://sunflower-land.com{FARM_ID}"
    
    while True:
        try:
            resposta = requests.get(url_api, timeout=15)
            if resposta.status_code == 200:
                dados = response_json = resposta.json()
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
                        # Limpa o nome removendo a palavra "seed" ou espaços indesejados
                        planta_nome = planta_atual.lower().replace(" seed", "").strip()
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
                        # Limpa o nome removendo a palavra "seed" ou espaços indesejados
                        fruta_nome = fruta_atual.lower().replace(" seed", "").strip()
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
                        # Busca o nome traduzido bonitinho para mandar na mensagem
                        nome_traduzido = TRADUCAO.get(info["planta"], info["planta"].capitalize())
                        
                        msg = f"🚨 **ALERTA AUTOMÁTICO!**\nSua plantação de **{nome_traduzido}** na fazenda **#{FARM_ID}** está pronta para colheita! 🎉🌾"
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
        f"🤖 **Monitor Inteligente Global Ativo!**\n\nEstou cuidando de todas as culturas e frutas da Fazenda **#{FARM_ID}** traduzindo os dados do jogo em tempo real!"
    )

if __name__ == '__main__':
    threading.Thread(target=rodar_servidor_web).start()
    threading.Thread(target=checar_fazenda_loop).start()
    
    print("Bot com rastreador inteligente iniciado!")
    bot.infinity_polling()
                               
