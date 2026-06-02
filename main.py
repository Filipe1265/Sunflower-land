import os
import time
import threading
from flask import Flask
import telebot

# 1. CONFIGURAÇÃO DO SITE FALSO PARA O RENDER NÃO DERRUBAR O BOT
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Sunflower Land online e operando na nuvem!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

# 2. CONFIGURAÇÃO DO BOT DO TELEGRAM
# Recomenda-se usar variáveis de ambiente no Render. 
# Caso prefira direto no código, mude para: TOKEN = "SEU_TOKEN" e CHAT_ID = SEU_ID
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8779097957:AAEDGqwe5FQfbUQZI-IC4yBN87_ru9C1ccQ")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", 5303286197))

bot = telebot.TeleBot(TOKEN, threaded=False)

# TEMPOS EXATOS CONVERTIDOS EM SEGUNDOS
TEMPOS = {
    "cenoura": 3420,          # 57 minutos
    "tomate": 6480,           # 1 hora e 48 minutos
    "arvore": 7200,           # 2 horas
    "milho": 61560,           # 17 horas e 6 minutos
    "trigo": 73860,           # 20 horas e 31 minutos
    "couve": 108000,          # 1 dia e 6 horas
    "barley": 147600          # 1 dia e 17 horas
}

def temporizador(chat_id, planta, segundos):
    time.sleep(segundos)
    # Alerta visual bonito para o Telegram
    bot.send_message(
        chat_id, 
        f"🚨 **Hora da Colheita!** Suas plantações de **{planta.upper()}** estão prontas no Sunflower Land! 🌾🌻🍅", 
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['start', 'ajuda'])
def enviar_boas_vindas(message):
    texto = (
        "🧑‍🌾 **Bot do Sunflower Land Ativo!**\n\n"
        "Para iniciar um cronômetro, use:\n"
        "`/plantar [nome_da_planta]`\n\n"
        "**Plantações configuradas:**\n"
        "• `/plantar cenoura` (57 min)\n"
        "• `/plantar tomate` (1h 48min)\n"
        "• `/plantar arvore` (2h)\n"
        "• `/plantar milho` (17h 6min)\n"
        "• `/plantar trigo` (20h 31min)\n"
        "• `/plantar couve` (1 dia e 6h)\n"
        "• `/plantar barley` (1 dia e 17h)"
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

@bot.message_handler(commands=['plantar'])
def iniciar_cronometro(message):
    try:
        partes = message.text.split()
        if len(partes) < 2:
            raise IndexError
            
        # Pega o nome da planta digitada e padroniza sem acento básico
        planta = partes[1].lower().replace("árvore", "arvore")
        
        if planta in TEMPOS:
            segundos_totais = TEMPOS[planta]
            
            # Formatação inteligente do tempo restante para exibição
            dias = segundos_totais // 86400
            horas = (segundos_totais % 86400) // 3600
            minutos = (segundos_totais % 3600) // 60
            
            partes_texto = []
            if dias > 0:
                partes_texto.append(f"{dias} dia(s)")
            if horas > 0:
                partes_texto.append(f"{horas} hora(s)")
            if minutos > 0:
                partes_texto.append(f"{minutos} minuto(s)")
                
            tempo_texto = " e ".join(partes_texto) if len(partes_texto) == 2 else ", ".join(partes_texto)
            
            bot.reply_to(
                message, 
                f"⏳ Cronômetro iniciado para **{planta.capitalize()}**!\n"
                f"Vou te mandar mensagem daqui a **{tempo_texto}**.", 
                parse_mode="Markdown"
            )
            
            # Dispara a contagem em segundo plano
            threading.Thread(target=temporizador, args=(CHAT_ID, planta, segundos_totais)).start()
        else:
            bot.reply_to(message, "❌ Planta não cadastrada. Use `/ajuda` para ver as opções válidas.")
    except IndexError:
        bot.reply_to(message, "⚠️ Informe a planta ao lado do comando. Exemplo: `/plantar milho`")

# 3. INICIALIZAÇÃO EM PARALELO (SITE + BOT)
if __name__ == '__main__':
    t = threading.Thread(target=rodar_servidor_web)
    t.start()
    
    print("Bot do Sunflower Land iniciado com sucesso!")
    bot.infinity_polling()
    
