import logging
from pathlib import Path


def setup_logger(name="ragbot") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] - %(message)s")

    if not logger.hasHandlers():
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


logger = setup_logger()
# logger.debug("Fetching LLM providers.")
# logger.warning(f"Invalid model provider: {model_provider}")
# logger.info(f"Getting collection count for provider: {model_provider}")
# logger.exception("Error getting collection count")
# logger.error("Failed to build LLM chain.")