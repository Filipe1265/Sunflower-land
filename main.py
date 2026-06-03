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
    return "Monitor SFL Completo (Crops + Frutas + Árvores) Online!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

# 2. CONFIGURAÇÃO SEGURA (LENDO DO SEU ENVIRONMENT NO RENDER)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", 0))
FARM_ID = 163523  # Sua fazenda fixa

bot = TeleBot(TOKEN, threaded=False)
terrenos_monitorados = {}
ultimo_rastreio = 0

TEMPOS = {
    "sunflower": 60, "potato": 300, "pumpkin": 1800, "carrot": 3420,
    "cabbage": 7200, "beetroot": 14400, "cauliflower": 28800, "parsnip": 43200,
    "radish": 86400, "wheat": 73860, "corn": 61560, "barley": 147600,
    "tomato": 6480, "blueberry": 14400, "orange": 28800, "apple": 86400, "banana": 43200,
    "wood_tree": 7200  # Tempo de recarga da árvore de madeira (2 horas) 🪵
}

TRADUCAO = {
    "sunflower": "Girassol", "potato": "Batata", "pumpkin": "Abóbora", "carrot": "Cenoura",
    "cabbage": "Repolho", "beetroot": "Beterraba", "cauliflower": "Couve", "parsnip": "Parsnip",
    "radish": "Rabanete", "wheat": "Trigo", "corn": "Milho", "barley": "Barley (Cevada)",
    "tomato": "Tomate 🍅", "blueberry": "Mirtilo 🫐", "orange": "Laranja 🍊", "apple": "Maçã 🍎", "banana": "Banana 🍌",
    "wood_tree": "Árvore de Madeira 🪵"
}

def executar_varredura_automatica():
    """Faz a checagem completa na API do jogo"""
    global terrenos_monitorados
    url_api = f"https://sunflower-land.com{FARM_ID}"
    
    print("🔄 [LOG] Iniciando varredura na fazenda...")
    try:
        resposta = requests.get(url_api, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        print(f"📡 [LOG] Resposta da API recebida. Status: {resposta.status_code}")
        
        if resposta.status_code == 200:
            dados = resposta.json()
            fazenda_estado = dados.get("state", {})
            tempo_atual = int(time.time())
            
            # Limpa registros antigos da memória
            for id_plantio, info in list(terrenos_monitorados.items()):
                if info["notificado"] and (tempo_atual - info["colheita_em"] > 600):
                    del terrenos_monitorados[id_plantio]
            
            # 1. MONITORAMENTO: PLANTAÇÕES COMUNS
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

            # 2. MONITORAMENTO: CANTEIROS DE FRUTAS
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
                            print(f"🍅 [DETECTADO] Fruta {fruta_nome.capitalize()} no canteiro {patch_id}.")
            
            # 3. NOVO: MONITORAMENTO DE ÁRVORES DE MADEIRA (Trees)
            arvores_jogo = fazenda_estado.get("trees", {})
            for tree_id, info_tree in arvores_jogo.items():
                wood_data = info_tree.get("wood")
                if wood_data:
                    data_corte = wood_data.get("choppedAt")
                    if data_corte:
                        data_corte_segundos = data_corte // 1000
                        id_unico = f"tree_{tree_id}_{data_corte_segundos}"
                        
                        # Se a árvore foi cortada, calcula o tempo de renascimento (2 horas)
                        tempo_total = TEMPOS["wood_tree"]
                        tempo_recarga = data_corte_segundos + tempo_total
                        
                        if id_unico not in terrenos_monitorados and tempo_atual < tempo_recarga:
                            terrenos_monitorados[id_unico] = {"planta": "wood_tree", "colheita_em": tempo_recarga, "notificado": False}
                            print(f"🪵 [DETECTADO] Árvore {tree_id} foi cortada. Iniciando recarga de 2h.")

            # 4. DISPARO DOS ALARMES IMEDIATOS
            for id_plantio, info in list(terrenos_monitorados.items()):
                if not info["notificado"] and tempo_atual >= info["colheita_em"]:
                    nome_exibicao = TRADUCAO.get(info["planta"], info["planta"].capitalize())
                    
                    if info["planta"] == "wood_tree":
                        msg = f"🚨 **ALERTA AUTOMÁTICO!**\nSuas **Árvores de Madeira** na fazenda **#{FARM_ID}** cresceram novamente e estão prontas para o machado! 🪓🪵"
                    else:
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

# 4. COMANDO /STATUS AVANÇADO (INCLUINDO ÁRVORES)
@bot.message_handler(commands=['start', 'status'])
def enviar_status(message):
    print("📥 [TELEGRAM] Comando /status solicitado. Forçando atualização da fazenda...")
    executar_varredura_automatica()
    
    tempo_atual = int(time.time())
    texto_relatorio = f"🤖 **Relatório de Tempo Real - Fazenda #{FARM_ID}**\n"
    texto_relatorio += f"⏱ *Dados sincronizados com a API.*\n\n"
    
    linhas_crescimento = []
    linhas_prontas = []
    
    for id_plantio, info in terrenos_monitorados.items():
        nome_bonito = TRADUCAO.get(info["planta"], info["planta"].capitalize())
        segundos_restantes = info["colheita_em"] - tempo_atual
        
        if segundos_restantes <= 0:
            if info["planta"] == "wood_tree":
                linhas_prontas.append(f"✅ **{nome_bonito}** — Pronta para cortar! 🪓")
            else:
                linhas_prontas.append(f"✅ **{nome_bonito}** — Pronto para Colher! 🌾")
        else:
            dias = segundos_restantes // 86400
            horas = (segundos_restantes % 86400) // 3600
            minutos = (segundos_restantes % 3600) // 60
            
            tempo_texto = ""
            if dias > 0: tempo_texto += f"{dias}d "
            if horas > 0: tempo_texto += f"{horas}h "
            tempo_texto += f"{minutos}m"
            
            linhas_crescimento.append(f"⏳ **{nome_bonito}** — Restam `{tempo_texto}`")
            
    if linhas_prontas:
        texto_relatorio += "🚨 **Prontos para colheita/corte:**\n" + "\n".join(linhas_prontas) + "\n\n"
    if linhas_crescimento:
        texto_relatorio += "🌱 **Em crescimento / Recarga:**\n" + "\n".join(linhas_crescimento)
    if not linhas_prontas and not linhas_crescimento:
        texto_relatorio += "📭 Nenhuma atividade ativa na memória. Se você acabou de plantar ou cortar árvores, mude de mapa no jogo e digite /status novamente!"

    bot.reply_to(message, texto_relatorio, parse_mode="Markdown")

if __name__ == '__main__':
    t_web = threading.Thread(target=rodar_servidor_web)
    t_web.daemon = True
    t_web.start()
    
    ultimo_rastreio = time.time()
    executar_varredura_automatica()
    
    bot.delete_webhook(drop_pending_updates=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
                        
