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
    # O Render exige ler a variável PORT. Se não achar, usa a porta padrão 10000
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

# 2. CONFIGURAÇÃO SEGURA DO BOT DO TELEGRAM
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID"))

# Importante: Desativamos 'threaded' para o plano free do Render rodar mais liso
bot = telebot.TeleBot(TOKEN, threaded=False)

TEMPOS = {
    "girassol": 60,            # 1 minuto (para testes)
    "batata": 300,            # 5 minutos
    "abobora": 1800,          # 30 minutos
    "cenoura": 3600,          # 1 hora
    "repolho": 7200,          # 2 horas
    "beterraba": 14400,       # 4 horas
    "couve": 28800,           # 8 horas
    "trigo": 86400            # 24 horas
}

def temporizador(chat_id, planta, segundos):
    time.sleep(segundos)
    bot.send_message(chat_id, f"🚨 **Hora da Colheita!** Suas plantações de **{planta.capitalize()}** estão prontas! 🌾🌻", parse_mode="Markdown")

@bot.message_handler(commands=['start', 'ajuda'])
def enviar_boas_vindas(message):
    texto = (
        "🧑‍🌾 **Bot do Sunflower Land Ativo na Nuvem!**\n\n"
        "Para iniciar um cronômetro, digite:\n"
        "`/plantar [nome_da_planta]`\n\n"
        "**Exemplos:**\n"
        "• `/plantar girassol`\n"
        "• `/plantar batata`"
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

@bot.message_handler(commands=['plantar'])
def iniciar_cronometro(message):
    try:
        partes = message.text.split()
        if len(partes) < 2:
            raise IndexError
            
        planta = partes[1].lower()
        
        if planta in TEMPOS:
            segundos = TEMPOS[planta]
            minutos_totais = segundos // 60
            
            if minutos_totais >= 60:
                horas = minutos_totais // 60
                tempo_texto = f"{horas} hora(s)"
            else:
                tempo_texto = f"{minutos_totais} minutos"
                
            bot.reply_to(message, f"⏳ Cronômetro iniciado para **{planta.capitalize()}**! Vou te avisar em {tempo_texto}.", parse_mode="Markdown")
            
            threading.Thread(target=temporizador, args=(CHAT_ID, planta, segundos)).start()
        else:
            bot.reply_to(message, "❌ Planta não encontrada. Digite `/ajuda` para ver a lista.")
    except IndexError:
        bot.reply_to(message, "⚠️ Use o comando informando a planta ao lado. Exemplo: `/plantar batata`")

# 3. INICIALIZAÇÃO EM PARALELO (SITE + BOT)
if __name__ == '__main__':
    # Inicia o site falso em uma tarefa separada
    t = threading.Thread(target=rodar_servidor_web)
    t.start()
    
    # Inicia o monitoramento do Telegram
    print("Bot do Sunflower Land iniciado com sucesso!")
    bot.infinity_polling()
                
