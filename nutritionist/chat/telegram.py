import logging
import asyncio
import os

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from agents.nutritionist import NutritionistAgent
from pyrogram.enums import ChatAction

from settings import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_TOKEN,
    TELEGRAM_BOT_NAME,
)


# https://my.telegram.org/apps to authentication


class TelegramBot:
    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

        # Inicialização do bot no Telegram
        self.app = Client(
            name=TELEGRAM_BOT_NAME,
            api_id=TELEGRAM_API_ID,
            api_hash=TELEGRAM_API_HASH,
            bot_token=TELEGRAM_TOKEN,
        )

        self._setup_handlers()

    def _setup_handlers(self):
        """Define os handlers para as mensagens do bot."""
        start_handler = MessageHandler(
            self.start,
            filters.command("start") & filters.private
        )
        self.app.add_handler(start_handler)

        # Handler para mensagens de texto
        text_filter = filters.text & filters.private
        message_handler = MessageHandler(
            self.handle_message,
            text_filter
        )
        self.app.add_handler(message_handler)

        # Handler para fotos
        photo_filter = filters.photo & filters.private
        photo_handler = MessageHandler(
            self.handle_photo,
            photo_filter
        )
        self.app.add_handler(photo_handler)

    async def start(self, client: Client, message: Message):
        """Função chamada quando o usuário envia /start."""
        await message.reply_text(
            "Olá! Eu sou a SmartNutri AI, sua assistente nutricional. 🌱✨\n"
            "Fui criada para ajudar você a alcançar seus objetivos alimentares de forma prática e eficiente.\n\n"
            "📋 O que posso fazer por você?\n"
            "- Criar dietas personalizadas.\n"
            "- Sugerir receitas deliciosas e equilibradas.\n"
            "- Avaliar suas refeições através de imagens.\n\n"
            "Envie uma mensagem ou uma foto do seu prato, e vamos começar sua jornada para uma alimentação mais saudável! 🍎🥗\n\n"
            "🛡️ Aviso: Todos os dados fornecidos serão salvos para oferecer um atendimento personalizado e melhorar sua experiência."
        )
        self.logger.info(f"Usuário {message.from_user.id} iniciou uma conversa.")

    async def handle_message(self, client: Client, message: Message):
        """Função que trata mensagens de texto enviadas para o bot."""
        user_id = message.from_user.id
        user_input = message.text
        print(f"Recebido do usuário {user_id}: {user_input}")

        # Exibir a animação de digitação
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

        # Criar o agente passando o `session_id` como `user_id`
        agent = NutritionistAgent(session_id=str(user_id))

        # Executar o agente de maneira síncrona usando run_in_executor
        try:
            response = agent.run(f'telegram_id: {user_id} ' + f'menssagem: {user_input}')
        except Exception as e:
            self.logger.error(f"Erro ao processar a mensagem do usuário {user_id}: {e}", exc_info=True)
            response = "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."

        # Responder ao usuário com a mensagem gerada pelo agente
        await message.reply_text(response)
        self.logger.info(f"Resposta enviada para o usuário {user_id}.")




    async def handle_photo(self, client: Client, message: Message):
        """Função que trata fotos enviadas para o bot."""
        user_id = message.from_user.id
        print(f"Recebida foto do usuário {user_id}.")

        # Exibir a animação de digitação
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

        # Criar a pasta 'storage' se não existir
        storage_dir = os.path.join(os.getcwd(), 'storage')
        os.makedirs(storage_dir, exist_ok=True)

        # Baixar a foto para a pasta 'storage' com um nome único
        photo_file_name = f"{user_id}_{message.photo.file_id}.jpg"
        photo_path = os.path.join(storage_dir, photo_file_name)
        await message.download(file_name=photo_path)
        print(f"Foto baixada em: {photo_path}")

        # Criar o agente passando o `session_id` como `user_id`
        agent = NutritionistAgent(session_id=str(user_id))

        # Executar o agente de maneira síncrona usando run_in_executor
        try:
            # Enviar o caminho da foto para o agente
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                agent.run,
                photo_path,  # Passamos o caminho da foto como input
            )
        except Exception as e:
            self.logger.error(f"Erro ao processar a imagem do usuário {user_id}: {e}", exc_info=True)
            response = "Desculpe, ocorreu um erro ao processar sua imagem. Por favor, tente novamente."

        # Responder ao usuário com a mensagem gerada pelo agente
        await message.reply_text(response)
        self.logger.info(f"Resposta enviada para o usuário {user_id}.")
        
        
        
        
        
        

    def run(self):
        """Inicia o bot no Telegram."""
        self.logger.info("Bot iniciado.")
        self.app.run()
