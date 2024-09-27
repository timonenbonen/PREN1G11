from dotenv import load_dotenv
from loguru import logger

from helloworld import say_hello
from utils import configure_logger

load_dotenv()

if __name__ == "__main__":
    configure_logger.configure("main")
    logger.debug("starting main")
    say_hello()
    logger.debug("exiting main")
