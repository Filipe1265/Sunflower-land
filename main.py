import os
import time
import threading
from flask import Flask
from telebot import TeleBot, types

# 1. CONFIGURAÇÃO DO SITE FALSO PARA O RENDER
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Sunflower Land (Painel de Botões) Online!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

# 2. CONFIGURAÇÃO SEGURA DO TELEGRAM
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", 0))

bot = TeleBot(TOKEN, threaded=False)
cronometros_ativos = {}

# Tabela de tempos convertida exatamente em segundos
TEMPOS = {
    "🌻 Girassol (1 min)": 60,
    "🥔 Batata (5 min)": 300,
    "🎃 Abóbora (30 min)": 1800,
    "🥕 Cenoura (57 min)": 3420,
    "🍅 Tomate (1h 48m)": 6480,
    "🌽 Milho (17h 6m)": 61560,
    "🌾 Trigo (20h 31m)": 73860,
    "🥬 Couve (1d 6h)": 108000,
    "🌾 Barley (1d 17h)": 147600,
    "🪓 Árvore (2h)": 7200
}

def temporizador_callback(chat_id, nome_item, segundos):
    """Aguarda o tempo necessário e envia o alerta final"""
    time.sleep(segundos)
    msg = f"🚨 **HORA DA COLHEITA!**\nSeu **{nome_item}** está pronto no Sunflower Land! Vá colher! 🧑‍🌾🚀"
    try:
        bot.send_message(chat_id, msg, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem de alerta: {e}")

def criar_painel():
    """Gera o teclado com botões grandes no Telegram"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    botoes = [types.KeyboardButton(nome) for nome in TEMPOS.keys()]
    # Adiciona o botão de verificar status no final
    botoes.append(types.KeyboardButton("📊 Ver Meus Cronômetros"))
    markup.add(*botoes)
    return markup

@bot.message_handler(commands=['start', 'ajuda', 'menu'])
def enviar_boas_vindas(message):
    texto = (
        "🧑‍🌾 **Bem-vindo ao Painel do Sunflower Land!**\n\n"
        "Agora o bot funciona independente da rede! Sempre que você plantar ou cortar uma árvore no jogo, "
        "basta clicar no botão correspondente aqui embaixo para eu iniciar o seu alarme.\n\n"
        "Use o botão **📊 Ver Meus Cronômetros** para checar o tempo restante de tudo!"
    )
    bot.reply_to(message, texto, reply_markup=criar_painel(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def processar_botoes(message):
    text = message.text
    tempo_atual = int(time.time())
    
    # Caso o usuário clique para ver o Status de tempo restante
    if text == "📊 Ver Meus Cronômetros":
        texto_relatorio = "📋 **Cronômetros Ativos na Memória:**\n\n"
        linhas_crescimento = []
        
        # Limpa da memória o que já tocou há mais de 10 minutos
        for id_cronometro, info in list(cronometros_ativos.items()):
            if tempo_atual > info["fim"] and (tempo_atual - info["fim"] > 600):
                del cronometros_ativos[id_cronometro]
        
        for id_cronometro, info in cronometros_ativos.items():
            segundos_restantes = info["fim"] - tempo_atual
            if segundos_restantes <= 0:
                linhas_crescimento.append(f"✅ **{info['item']}** — ¡Pronto para Colher! 🌾")
            else:
                dias = segundos_restantes // 86400
                horas = (segundos_restantes % 86400) // 3600
                minutos = (segundos_restantes % 3600) // 60
                
                tempo_texto = f"{dias}d " if dias > 0 else ""
                tempo_texto += f"{horas}h " if horas > 0 else ""
                tempo_texto += f"{minutos}m"
                linhas_crescimento.append(f"⏳ **{info['item']}** — Restam `{tempo_texto}`")
                
        if linhas_crescimento:
            texto_relatorio += "\n".join(linhas_crescimento)
        else:
            texto_relatorio += "📭 Nenhum cronômetro rodando no momento. Clique em um botão abaixo para iniciar!"
            
        bot.reply_to(message, texto_relatorio, parse_mode="Markdown", reply_markup=criar_painel())
        return

    # Caso clique em um botão de Planta/Árvore
    if text in TEMPOS:
        segundos = TEMPOS[text]
        tempo_fim = tempo_atual + segundos
        
        # Cria um identificador único usando o timestamp atual para permitir múltiplos alarmes do mesmo item
        id_unico = f"{text}_{tempo_atual}"
        cronometros_ativos[id_unico] = {"item": text, "fim": tempo_fim}
        
        # Calcula o texto amigável de quanto tempo vai demorar
        dias = segundos // 86400
        horas = (segundos % 86400) // 3600
        minutos = (segundos % 3600) // 60
        tempo_texto = f"{dias} dia(s) " if dias > 0 else ""
        tempo_texto += f"{horas} hora(s) e " if horas > 0 else ""
        tempo_texto += f"{minutos} minuto(s)"
        
        bot.reply_to(
            message, 
            f"⏳ Cronômetro iniciado para **{text}**!\n"
            f"Vou te mandar mensagem daqui a **{tempo_texto}**.", 
            reply_markup=criar_painel(),
            parse_mode="Markdown"
        )
        
        # Dispara o alarme em background sem travar o bot
        threading.Thread(target=temporizador_callback, args=(CHAT_ID, text, segundos)).start()
    else:
        bot.reply_to(message, "❌ Comando não reconhecido. Use os botões do painel ou digite `/menu`.", reply_markup=criar_painel())

if __name__ == '__main__':
    t_web = threading.Thread(target=rodar_servidor_web)
    t_web.daemon = True
    t_web.start()
    
    print("🧹 [SISTEMA] Removendo conexões antigas para evitar o Erro 409...")
    bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 [SISTEMA] Iniciando Polling do Painel de Botões...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
            
