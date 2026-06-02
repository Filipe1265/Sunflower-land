import os
import time
import threading
import telebot

# Puxa as configurações seguras da nuvem (Render)
TOKEN = os.environ.get("8779097957:AAEDGqwe5FQfbUQZI-IC4yBN87_ru9C1ccQ")
# Converte o ID para número inteiro, necessário para a biblioteca funcionar
CHAT_ID = int(os.environ.get("5303286197"))

bot = telebot.TeleBot(TOKEN)

# Tabela de tempos de cultivo oficiais do Sunflower Land (em segundos)
TEMPOS = {
    "girassol": 60,            # 1 minuto (ideal para você fazer testes)
    "batata": 300,            # 5 minutos
    "abobora": 1800,          # 30 minutos
    "cenoura": 3600,          # 1 hora
    "repolho": 7200,          # 2 horas
    "beterraba": 14400,       # 4 horas
    "couve": 28800,           # 8 horas
    "trigo": 86400            # 24 horas
}

# Função que roda em segundo plano contando o tempo
def temporizador(chat_id, planta, segundos):
    time.sleep(segundos)
    # Envia a mensagem direto no seu chat privado
    bot.send_message(chat_id, f"🚨 **Hora da Colheita!** Suas plantações de **{planta.capitalize()}** estão prontas! 🌾🌻", parse_mode="Markdown")

# Comando inicial do Bot
@bot.message_handler(commands=['start', 'ajuda'])
def enviar_boas_vindas(message):
    texto = (
        "🧑‍🌾 **Bot do Sunflower Land Ativo na Nuvem!**\n\n"
        "Para iniciar um cronômetro, digite:\n"
        "`/plantar [nome_da_planta]`\n\n"
        "**Exemplos de plantas:**\n"
        "• `/plantar girassol` (teste rápido)\n"
        "• `/plantar batata`\n"
        "• `/plantar abobora`\n"
        "• `/plantar cenoura`\n"
        "• `/plantar repolho`\n"
        "• `/plantar beterraba`\n"
        "• `/plantar couve`\n"
        "• `/plantar trigo`"
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

# Comando que ativa o cronômetro
@bot.message_handler(commands=['plantar'])
def iniciar_cronometro(message):
    try:
        # Separa o comando do nome da planta e padroniza em minúsculo
        partes = message.text.split()
        if len(partes) < 2:
            raise IndexError
            
        planta = partes[1].lower()
        
        if planta in TEMPOS:
            segundos = TEMPOS[planta]
            minutos_totais = segundos // 60
            
            # Formata o aviso de resposta
            if minutos_totais >= 60:
                horas = minutos_totais // 60
                tempo_texto = f"{horas} hora(s)"
            else:
                tempo_texto = f"{minutos_totais} minutos"
                
            bot.reply_to(message, f"⏳ Cronômetro iniciado para **{planta.capitalize()}**! Vou te avisar em {tempo_texto}.", parse_mode="Markdown")
            
            # Cria a linha de contagem em paralelo para a nuvem não travar
            threading.Thread(target=temporizador, args=(CHAT_ID, planta, segundos)).start()
        else:
            bot.reply_to(message, "❌ Planta não encontrada. Digite `/ajuda` para ver a lista de plantas aceitas.")
            
except IndexError:
        bot.reply_to(message, "⚠️ Use o comando informando a planta ao lado. Exemplo: `/plantar batata`")

# Mantém o bot conectado 24 horas sem derrubar o script
print("Bot do Sunflower Land iniciado com sucesso!")
bot.infinity_polling()
