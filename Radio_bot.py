import discord
from discord.ext import commands
import mysql.connector
import yt_dlp
import asyncio


intents = discord.Intents.default()
intents.message_content = True


# Prefixo do BOT # Altere conforme o seu bot
bot = commands.Bot(command_prefix="COLOQUE O PREFIXO AQUI -> ex: !p/!play/@play, etc", intents=intents)


# Configuração do Banco de Dados # Altere conforme o seu banco de dados
db_config = {
    "host": "HOST",
    "user": "USER",
    "password": "SENHA DO BANCO DE DADOS",
    "database": "NOME DO BANCO DE DADOS",
}


# Conecta com o banco de dados
def connect_db():
    return mysql.connector.connect(**db_config)


# Criacao da database e as tabelas 
def setup_database():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS radio_channels (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            url TEXT NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

setup_database()  # Inicializa a base de dados ao iniciar o bot


# Pega os canais de radio do banco de dados
def get_channels():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM NOME_DA_TABELA") #altere conforme a sua tabela
    channels = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return channels


# Comandos do bot
# Lista os canais
@bot.command()
async def list_channels(ctx):
    conn = connect_db()  
    if conn.is_connected():
        print("✅ Database conectada!✅")
    else:
        print("❌ Conexão com a database falhou!❌")
        await ctx.send("❌ Erro de conexao com a database. Cheque os logs.❌")
        conn.close()
        return  

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM radio_channels")  #altere conforme a sua tabela
    channels = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close() 

    if channels:
        await ctx.send("📡 **Canais Disponiveis:**\n" + "\n".join([f"- {ch}" for ch in channels]))
    else:
        await ctx.send("❌ Nenhum canal encontrado. É necessário adiciona-los a database.❌")

# Entra no canal de voz
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send("🔊 Entrou no canal de voz!🔊")
    else:
        await ctx.send("❌ Você precisa estar em um canal de voz!❌")


# Toca a stream do canal pedido
@bot.command()
async def play_channel(ctx, channel_name: str):
    if ctx.author.voice is None:
        await ctx.send("❌ Voce precisa estar em um canal de voz.❌")
        return

 
    voice_channel = ctx.author.voice.channel

    # Conecta ao banco de dados
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM channels WHERE name = %s", (channel_name,))  
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        await ctx.send(f"❌ Canal '{channel_name}' nao encontrado.❌")
        return

    stream_url = result[0]

    # Conecta ao canal de voz
    vc = await ctx.author.voice.channel.connect() if not ctx.voice_client else ctx.voice_client

    # Extrai o URL da stream usando yt-dlp
    ydl_opts = {"format": "bestaudio", "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(stream_url, download=False)
        audio_url = info["url"]

    # Toca a stream
    vc.stop()  
    vc.play(discord.FFmpegPCMAudio(audio_url), after=lambda e: print(f"Stream finalizada: {e}"))

    await ctx.send(f"🎶 Tocando agora **{channel_name}**!🎶")


# Pausa a stream
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Stream pausada.⏸️")
    else:
        await ctx.send("❌Nenhum aúdio está sendo tocado!❌")


# Retomar a stream
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Retomar a stream.▶️")
    else:
        await ctx.send("❌Nenhum aúdio está pausado!❌")


# Parar a stream e sair
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Desconectado. 🛑")
    else:
        await ctx.send("❌Rádio já está em um canal.❌")


# Mensagens de log
@bot.event
async def on_message(message):
    print(f"Mensagem Recebida: {message.content}") 

    if message.author.bot:
        return  

    ctx = await bot.get_context(message)
    if ctx.command:
        print(f"✅ Comando '{ctx.command}' recebido, processando...")

    await bot.process_commands(message)  


# Mostra os comandos registrados, e confirma se o bot esta online
@bot.event
async def on_ready():
    print(f"✅Bot está online como {bot.user}✅")
    print(f"📜Comandos registrados: {', '.join([cmd.name for cmd in bot.commands])} 📜")

# Liga o bot com o token do discord.
bot.run("TOKEN DO DISCORD")