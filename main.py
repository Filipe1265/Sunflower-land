import os
import time
import threading
from flask import Flask
from telebot import TeleBot, types

# 1. CONFIGURAÇÃO DO SITE FALSO PARA O RENDER
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Sunflower Land (Painel Ultra Avançado) Online!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

# 2. CONFIGURAÇÃO SEGURA DO TELEGRAM
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", 0))

bot = TeleBot(TOKEN, threaded=False)

# Memória operacional do Bot
cronometros_ativos = {}
ultimo_id_adicionado = {}  # Guarda o último alarme por chat_id para poder cancelar

# Dicionários estruturados por Categorias (Tempos em segundos)
PLANTAS = {
    "🌻 Girassol (1 min)": 60, "🥔 Batata (5 min)": 300, "🎃 Abóbora (30 min)": 1800,
    "🥕 Cenoura (57 min)": 3420, "🍅 Tomate (1h 48m)": 6480, "🌽 Milho (17h 6m)": 61560,
    "🌾 Trigo (20h 31m)": 73860, "🥬 Couve (1d 6h)": 108000, "🌾 Barley (1d 17h)": 147600,
    "🪓 Árvore (2h)": 7200
}

COZINHA = {
    "🥣 Sopa de Abóbora (20 min)": 1200, "🍟 Batata Frita (20 min)": 1200,
    "🥗 Salada Crunch (30 min)": 1800, "🥞 Panqueca (15 min)": 900,
    "🥧 Torta de Maçã (4h)": 14400, "🍕 Pizza Marguerita (20h)": 72000
}

# Quantidade padrão de plots de terra que você possui para a calculadora
PLOTS_FAZENDA = 22  

def temporizador_callback(chat_id, nome_item, segundos, id_unico):
    """Gerencia o tempo, enviando o pré-alerta e o alerta final"""
    # Se o tempo for maior que 3 minutos, envia o pré-alerta de 2 minutos antes
    if segundos > 180:
        time.sleep(segundos - 120)
        # Verifica se o usuário não cancelou o alarme antes do tempo
        if id_unico in cronometros_ativos and not cronometros_ativos[id_unico]["cancelado"]:
            bot.send_message(chat_id, f"⏱️ **Pré-Alerta:** Faltam **2 minutos** para seu **{nome_item}** ficar pronto! Abra o jogo e prepare-se! 🧑‍🌾")
        time.sleep(120)
    else:
        time.sleep(segundos)

    # Alerta Final
    if id_unico in cronometros_ativos and not cronometros_ativos[id_unico]["cancelado"]:
        msg = f"🚨 **HORA DA COLHEITA/PREPARO!**\nSeu **{nome_item}** está pronto no Sunflower Land! Vá agir! 🚀🪵🍅"
        try:
            bot.send_message(chat_id, msg, parse_mode="Markdown")
        except Exception as e:
            print(f"❌ Erro ao notificar: {e}")

# --- GERENCIADORES DE INTERFACE (TECLADOS) ---
def teclado_principal():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("🌱 Menu Plantações"), types.KeyboardButton("🍳 Menu Cozinha"))
    markup.add(types.KeyboardButton("📊 Ver Meus Cronômetros"), types.KeyboardButton("🧮 Calculadora de Sementes"))
    markup.add(types.KeyboardButton("❌ Cancelar Último Alarme"))
    return markup

def teclado_plantas():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    botoes = [types.KeyboardButton(nome) for nome in PLANTAS.keys()]
    markup.add(*botoes)
    markup.add(types.KeyboardButton("⬅️ Voltar ao Menu Principal"))
    return markup

def teclado_cozinha():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    botoes = [types.KeyboardButton(nome) for nome in COZINHA.keys()]
    markup.add(*botoes)
    markup.add(types.KeyboardButton("⬅️ Voltar ao Menu Principal"))
    return markup

@bot.message_handler(commands=['start', 'menu', 'ajuda'])
def enviar_menu_principal(message):
    texto = (
        "👑 **Painel Ultra SFL Automatizado Ativo!**\n\n"
        "Navegue pelas abas abaixo para agendar os seus alarmes sem travar e sem depender de nenhuma rede blockchain:\n\n"
        "• **🌱 Plantações:** Todas as sementes e árvores.\n"
        "• **🍳 Cozinha:** Receitas do Fire Pit, Kitchen, etc.\n"
        "• **🧮 Calculadora:** Quantidade exata de sementes por canteiro.\n"
        "• **❌ Cancelar:** Errou o clique? Apague o último alarme num clique."
    )
    bot.reply_to(message, texto, reply_markup=teclado_principal(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def processar_interacoes_painel(message):
    global cronometros_ativos, ultimo_id_adicionado
    text = message.text
    tempo_atual = int(time.time())
    chat_id = message.chat.id
    
    # 1. NAVEGAÇÃO DE MENUS
    if text == "🌱 Menu Plantações":
        bot.reply_to(message, "Selecione o que você acabou de plantar ou cortar:", reply_markup=teclado_plantas())
        return
    elif text == "🍳 Menu Cozinha":
        bot.reply_to(message, "Selecione a receita que colocou para cozinhar:", reply_markup=teclado_cozinha())
        return
    elif text == "⬅️ Voltar ao Menu Principal":
        bot.reply_to(message, "Voltando...", reply_markup=teclado_principal())
        return

    # 2. SISTEMA DE CANCELAMENTO
    if text == "❌ Cancelar Último Alarme":
        last_id = ultimo_id_adicionado.get(chat_id)
        if last_id and last_id in cronometros_ativos and not cronometros_ativos[last_id]["cancelado"]:
            cronometros_ativos[last_id]["cancelado"] = True
            item_nome = cronometros_ativos[last_id]["item"]
            bot.reply_to(message, f"🗑️ O alarme para **{item_nome}** foi cancelado e apagado com sucesso!", reply_markup=teclado_principal())
        else:
            bot.reply_to(message, "📭 Você não tem nenhum alarme ativo recente para cancelar.", reply_markup=teclado_principal())
        return

    # 3. CALCULADORA DE SEMENTES
    if text == "🧮 Calculadora de Sementes":
        texto_calc = f"🧮 **Calculadora Inteligente de Sementes**\n"
        texto_calc += f"Considerando que sua fazenda possui atualmente `{PLOTS_FAZENDA} terrenos` livres:\n\n"
        texto_calc += "🛒 *Para plantar uma rodada completa você precisa comprar:*\n"
        texto_calc += f"• `{PLOTS_FAZENDA}` sementes do vegetal escolhido.\n\n"
        texto_calc += "💡 _Dica: Faça o estoque com o comerciante antes de começar a plantar em massa para não perder tempo com cliques extras!_"
        bot.reply_to(message, texto_calc, parse_mode="Markdown", reply_markup=teclado_principal())
        return

    # 4. EXIBIÇÃO DE RELATÓRIO DO STATUS
    if text == "📊 Ver Meus Cronômetros":
        texto_relatorio = "📋 **Seus Cronômetros Ativos:**\n\n"
        linhas = []
        
        # Limpa memória velha
        for k, v in list(cronometros_ativos.items()):
            if v["cancelado"] or (tempo_atual > v["fim"] and (tempo_atual - v["fim"] > 600)):
                del cronometros_ativos[k]

        for id_cronometro, info in cronometros_ativos.items():
            if info["cancelado"]: continue
            segundos_restantes = info["fim"] - tempo_atual
            if segundos_restantes <= 0:
                linhas.append(f"✅ **{info['item']}** — Pronto! 🎉")
            else:
                dias = segundos_restantes // 86400
                horas = (segundos_restantes % 86400) // 3600
                minutos = (segundos_restantes % 3600) // 60
                tempo_texto = f"{dias}d " if dias > 0 else ""
                tempo_texto += f"{horas}h " if horas > 0 else ""
                tempo_texto += f"{minutos}m"
                linhas.append(f"⏳ **{info['item']}** — Restam `{tempo_texto}`")
                
        texto_relatorio += "\n".join(linhas) if linhas else "📭 Nenhum alarme rodando na memória."
        bot.reply_to(message, texto_relatorio, parse_mode="Markdown")
        return

    # 5. AGENDAMENTO DOS BOTÕES (PLANTAS OU COZINHA)
    tabela_alvo = None
    if text in PLANTAS: tabela_alvo = PLANTAS
    elif text in COZINHA: tabela_alvo = COZINHA

    if tabela_alvo:
        segundos = tabela_alvo[text]
        tempo_fim = tempo_atual + segundos
        id_unico = f"{text}_{tempo_atual}"
        
        # Registra o alarme ativo
        cronometros_ativos[id_unico] = {"item": text, "fim": tempo_fim, "cancelado": False}
        ultimo_id_adicionado[chat_id] = id_unico  # Salva para caso queira cancelar
        
        dias = segundos // 86400
        horas = (segundos % 86400) // 3600
        minutos = (segundos % 3600) // 60
        tempo_texto = f"{dias}d " if dias > 0 else ""
        tempo_texto += f"{horas}h " if horas > 0 else ""
        tempo_texto += f"{minutos}m"
        
        bot.reply_to(message, f"⏳ Cronômetro iniciado para **{text}**!\nNotificações configuradas (com pré-alerta de 2 minutos).")
        
        # Inicia a Thread do temporizador
        threading.Thread(target=temporizador_callback, args=(CHAT_ID, text, segundos, id_unico)).start()
    else:
        bot.reply_to(message, "⚠️ Toque em um botão válido ou digite `/menu` para retornar.")

if __name__ == '__main__':
    t_web = threading.Thread(target=rodar_servidor_web)
    t_web.daemon = True
    t_web.start()
    
    print("🧹 [SISTEMA] Expulsando conexões antigas do Telegram...")
    bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 [SISTEMA] Painel Ultra SFL Inicializado com Sucesso!")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
        
