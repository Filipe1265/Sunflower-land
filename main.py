import os
import time
import requests
from flask import Flask, request
import threading
from telebot import TeleBot, types

# 1. CONFIGURAÇÃO DE AMBIENTE
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", 0))
FARM_ID = 163523

# O Render fornece automaticamente a URL do seu app nesta variável interna
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

bot = TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

terrenos_monitorados = {}
ultimo_rastreio = 0

TEMPOS = {
    "sunflower": 60, "potato": 300, "pumpkin": 1800, "carrot": 3420,
    "cabbage": 7200, "beetroot": 14400, "cauliflower": 28800, "parsnip": 43200,
    "radish": 86400, "wheat": 73860, "corn": 61560, "barley": 147600,
    "tomato": 6480, "blueberry": 14400, "orange": 28800, "apple": 86400, "banana": 43200,
    "wood_tree": 7200
}

TRADUCAO = {
    "sunflower": "Girassol", "potato": "Batata", "pumpkin": "Abóbora", "carrot": "Cenoura",
    "cabbage": "Repolho", "beetroot": "Beterraba", "cauliflower": "Couve", "parsnip": "Parsnip",
    "radish": "Rabanete", "wheat": "Trigo", "corn": "Milho", "barley": "Barley (Cevada)",
    "tomato": "Tomate 🍅", "blueberry": "Mirtilo 🫐", "orange": "Laranja 🍊", "apple": "Maçã 🍎", "banana": "Banana 🍌",
    "wood_tree": "Árvore de Madeira 🪵"
}

# ROTA 1: Página inicial padrão para o Render e UptimeRobot
@app.route('/')
def home():
    # Aproveita as visitas do UptimeRobot a cada 5 minutos para checar a fazenda de forma garantida
    executar_varredura_automatica()
    return f"Monitor SFL Ativo via Webhook! Fazenda #{FARM_ID}"

# ROTA 2: Canal seguro por onde o Telegram vai enviar os comandos (/status)
@app.route('/' + TOKEN, methods=['POST'])
def receber_updates():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Erro', 403

def executar_varredura_automatica():
    """Faz a checagem completa na API do jogo"""
    global terrenos_monitorados
    url_api = f"https://sunflower-land.com{FARM_ID}"
    
    print("🔄 [LOG] Iniciando varredura na fazenda...")
    try:
        resposta = requests.get(url_api, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            fazenda_estado = dados.get("state", {})
            tempo_atual = int(time.time())
            
            # Limpa registros antigos
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
                            print(f"🌱 [DETECTADO] Plantio de {planta_nome.capitalize()}.")

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
                            tempo_total = TEMPOS[fruta_nome]
                            tempo_colheita = data_segundos + tempo_total
                            terrenos_monitorados[id_unico] = {"planta": fruta_nome, "colheita_em": tempo_colheita, "notificado": False}
                            print(f"🍅 [DETECTADO] Fruta {fruta_nome.capitalize()}.")
            
            # 3. ÁRVORES DE MADEIRA
            arvores_jogo = fazenda_estado.get("trees", {})
            for tree_id, info_tree in arvores_jogo.items():
                wood_data = info_tree.get("wood")
                if wood_data:
                    data_corte = wood_data.get("choppedAt")
                    if data_corte:
                        data_corte_segundos = data_corte // 1000
                        id_unico = f"tree_{tree_id}_{data_corte_segundos}"
                        tempo_recarga = data_corte_segundos + TEMPOS["wood_tree"]
                        
                        if id_unico not in terrenos_monitorados and tempo_atual < tempo_recarga:
                            terrenos_monitorados[id_unico] = {"planta": "wood_tree", "colheita_em": tempo_recarga, "notificado": False}
                            print(f"🪵 [DETECTADO] Árvore {tree_id} em recarga.")

            # 4. DISPARO DOS ALARMES
            for id_plantio, info in list(terrenos_monitorados.items()):
                if not info["notificado"] and tempo_atual >= info["colheita_em"]:
                    nome_exibicao = TRADUCAO.get(info["planta"], info["planta"].capitalize())
                    if info["planta"] == "wood_tree":
                        msg = f"🚨 **ALERTA AUTOMÁTICO!**\nSuas **Árvores de Madeira** na fazenda **#{FARM_ID}** cresceram! 🪓🪵"
                    else:
                        msg = f"🚨 **ALERTA AUTOMÁTICO!**\nSua plantação de **{nome_exibicao}** na fazenda **#{FARM_ID}** está pronta! 🌾🍅"
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                    info["notificado"] = True
        else:
            print(f"⚠️ [AVISO] API com status {resposta.status_code}.")
    except Exception as e:
        print(f"❌ [ERRO INTERNO] Varredura falhou: {e}")

@bot.message_handler(commands=['start', 'status'])
def enviar_status(message):
    executar_varredura_automatica()
    tempo_atual = int(time.time())
    texto_relatorio = f"🤖 **Relatório de Tempo Real - Fazenda #{FARM_ID}**\n\n"
    
    linhas_crescimento = []
    linhas_prontas = []
    
    for id_plantio, info in terrenos_monitorados.items():
        nome_bonito = TRADUCAO.get(info["planta"], info["planta"].capitalize())
        segundos_restantes = info["colheita_em"] - tempo_atual
        
        if segundos_restantes <= 0:
            linhas_prontas.append(f"✅ **{nome_bonito}** — Pronto! 🌾")
        else:
            dias = segundos_restantes // 86400
            horas = (segundos_restantes % 86400) // 3600
            minutos = (segundos_restantes % 3600) // 60
            tempo_texto = f"{dias}d " if dias > 0 else ""
            tempo_texto += f"{horas}h " if horas > 0 else ""
            tempo_texto += f"{minutos}m"
            linhas_crescimento.append(f"⏳ **{nome_bonito}** — Restam `{tempo_texto}`")
            
    if linhas_prontas: texto_relatorio += "🚨 **Prontos para colheita/corte:**\n" + "\n".join(linhas_prontas) + "\n\n"
    if linhas_crescimento: texto_relatorio += "🌱 **Em crescimento / Recarga:**\n" + "\n".join(linhas_crescimento)
    if not linhas_prontas and not linhas_crescimento:
        texto_relatorio += "📭 Nenhuma atividade cadastrada. Sincronize o jogo e digite /status novamente!"

    bot.reply_to(message, texto_relatorio, parse_mode="Markdown")

# Função que configura o Webhook assim que o servidor liga
def configurar_webhook():
    time.sleep(3)
    if RENDER_EXTERNAL_URL:
        # Avisa ao Telegram para enviar as mensagens para o link do Render
        url_webhook = f"{RENDER_EXTERNAL_URL.rstrip('/')}/{TOKEN}"
        print(f"🧹 [SISTEMA] Removendo conexões velhas e ativando Webhook em: {url_webhook}")
        bot.remove_webhook()
        bot.set_webhook(url=url_webhook)
    else:
        print("❌ [ERRO] RENDER_EXTERNAL_URL não encontrada. Certifique-se de que é um Web Service.")

if __name__ == '__main__':
    # Dispara a configuração do Webhook em background
    threading.Thread(target=configurar_webhook).start()
    
    # Inicia o servidor Flask na linha principal
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
            
