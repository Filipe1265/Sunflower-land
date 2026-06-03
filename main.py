import os
import time
import requests
from flask import Flask
import threading
from telebot import TeleBot

# 1. CONFIGURAÇÃO DO SITE FALSO PARA O RENDER
app = Flask(__name__)

@app.route('/')
def home():
    return "Monitor SFL Automatizado e com Relatório Online!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

# 2. CONFIGURAÇÃO SEGURA (LENDO DO SEU ENVIRONMENT NO RENDER)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID")
FARM_ID = 163523  # Sua fazenda fixa

bot = TeleBot(TOKEN, threaded=False)
terrenos_monitorados = {}
ultimo_rastreio = 0

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

def executar_varredura_automatica():
    """Faz a checagem na API do jogo"""
    global terrenos_monitorados
    url_api = f"https://sunflower-land.com{FARM_ID}"
    
    print("🔄 [LOG] Iniciando varredura programada na fazenda...")
    try:
        resposta = requests.get(url_api, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        print(f"📡 [LOG] Resposta da API recebida. Status: {resposta.status_code}")
        
        if resposta.status_code == 200:
            dados = resposta.json()
            fazenda_estado = dados.get("state", {})
            tempo_atual = int(time.time())
            
            # Limpa registros antigos que já foram colhidos para não acumular lixo na memória
            for id_plantio, info in list(terrenos_monitorados.items()):
                if info["notificado"] and (tempo_atual - info["colheita_em"] > 600):
                    del terrenos_monitorados[id_plantio]
            
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
                            tempo_total = TEMPOS[planta_nome]
                            tempo_colheita = data_plantio_segundos + tempo_total
                            
                            terrenos_monitorados[id_unico] = {"planta": planta_nome, "colheita_em": tempo_colheita, "notificado": False}
                            print(f"🌱 [DETECTADO] Plantio de {planta_nome.capitalize()} no campo {terreno_id}.")

            # 2. CANTEIROS DE FRUTAS
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
                            print(f"🍅 [DETECTADO] Fruta {fruta_nome.capitalize()} no canteiro {patch_id}.")
            
            # 3. DISPARO DOS ALARMES IMEDIATOS
            for id_plantio, info in list(terrenos_monitorados.items()):
                if not info["notificado"] and tempo_atual >= info["colheita_em"]:
                    nome_exibicao = TRADUCAO.get(info["planta"], info["planta"].capitalize())
                    msg = f"🚨 **ALERTA AUTOMÁTICO!**\nSua plantação de **{nome_exibicao}** na fazenda **#{FARM_ID}** está pronta para colheita! 🌾🍅🌻"
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                    info["notificado"] = True
                    print(f"📢 [NOTIFICADO] Mensagem enviada para {info['planta']}.")
        else:
            print(f"⚠️ [AVISO] API retornou erro status {resposta.status_code}.")
            
    except Exception as e:
        print(f"❌ [ERRO INTERNO] Falha na varredura: {e}")

# Interceptador de ciclos
def checar_tempo_e_varrer(messages):
    global ultimo_rastreio
    tempo_atual = time.time()
    if tempo_atual - ultimo_rastreio >= 120:
        ultimo_rastreio = tempo_atual
        executar_varredura_automatica()

bot.set_update_listener(checar_tempo_e_varrer)

# 3. NOVO COMANDO /STATUS DETALHADO
@bot.message_handler(commands=['start', 'status'])
def enviar_status(message):
    print("📥 [TELEGRAM] Comando /status solicitado.")
    tempo_atual = int(time.time())
    
    # Cabeçalho do relatório
    texto_relatorio = f"🤖 **Relatório da Fazenda #{FARM_ID}**\n"
    texto_relatorio += f"⏱️ *Última checagem automática ativa.*\n\n"
    
    linhas_crescimento = []
    linhas_prontas = []
    
    # Varre a memória do bot procurando o que está cadastrado
    for id_plantio, info in terrenos_monitorados.items():
        nome_bonito = TRADUCAO.get(info["planta"], info["planta"].capitalize())
        segundos_restantes = info["colheita_em"] - tempo_atual
        
        if segundos_restantes <= 0:
            linhas_prontas.append(f"✅ **{nome_bonito}** — ¡Pronto para Colher! 🌾")
        else:
            # Formatação do tempo legível
            dias = segundos_restantes // 86400
            horas = (segundos_restantes % 86400) // 3600
            minutos = (segundos_restantes % 3600) // 60
            
            # Monta o texto bonitinho
            tempo_texto = ""
            if dias > 0: tempo_texto += f"{dias}d "
            if horas > 0: tempo_texto += f"{horas}h "
            tempo_texto += f"{minutos}m"
            
            linhas_crescimento.append(f"⏳ **{nome_bonito}** — Restam `{tempo_texto}`")
            
    # Junta as listas na mensagem final
    if linhas_prontas:
        texto_relatorio += "🚨 **Prontos para colheita:**\n" + "\n".join(linhas_prontas) + "\n\n"
    
    if lines_crescimento := linhas_crescimento:
        texto_relatorio += "🌱 **Crescendo nos campos:**\n" + "\n".join(lines_crescimento)
        
    if not linhas_prontas and not linhas_crescimento:
        texto_relatorio += "📭 Nenhuma plantação ativa ou detectada no momento. Vá até o jogo e plante para iniciar o rastreio automático!"

    bot.reply_to(message, texto_relatorio, parse_mode="Markdown")

if __name__ == '__main__':
    t_web = threading.Thread(target=rodar_servidor_web)
    t_web.daemon = True
    t_web.start()
    
    ultimo_rastreio = time.time()
    executar_varredura_automatica()
    
    print("🧹 [SISTEMA] Removendo conexões antigas para evitar o Erro 409...")
    bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 [SISTEMA] Iniciando Polling Linear do Telegram...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
                
