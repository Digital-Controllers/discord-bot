from configs import configs
from datetime import datetime
from tb_discord import bot
import logging

# =======UTILITIES=======

logging.basicConfig(filename='runtime.log', encoding='utf-8', level=logging.INFO)

# =======INIT=======

utc_start = datetime.utcnow()
print(f"Started at {str(utc_start)[:-16]}")
logging.info("Started on %s", utc_start.strftime('%d-%m-%Y at %H:%M:%S UTC%z'))

bot.run(configs.TOKEN)
