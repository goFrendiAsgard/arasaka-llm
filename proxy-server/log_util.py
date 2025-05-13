import logging

from config import LLM_API_KEY, LOG_LEVEL


class RedactingFormatter(logging.Formatter):

    def format(self, record):
        formatted_message = super().format(record)
        return formatted_message.replace(LLM_API_KEY, "***Redacted***")


# Configure logger
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = RedactingFormatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)
