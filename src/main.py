import asyncio
import sys
from pathlib import Path
from src.utils import load_config
from src.generator import start_process
from loguru import logger


def setup_logging():

    logger.remove()

    logger.add("logs/main.log", rotation="10 MB", level="INFO", format="{time} - {level} - {message}", enqueue=True,)

    logger.add(
        "logs/auth_token.log", rotation="10 MB", retention=3, compression="zip", level="INFO", enqueue=True,
        format="{time} - {level} - {message}", filter=lambda record: "auth_token" in record["name"]
    )

    logger.add(
        "logs/generator.log", rotation="10 MB", retention=3, compression="zip", level="DEBUG", enqueue=True,
        format="{time} - {level} - {message}", filter=lambda record: "src.generator" in record["name"]
    )

    logger.add(
        "logs/parser.log", rotation="10 MB", retention=3, compression="zip", level="DEBUG", enqueue=True,
        format="{time} - {level} - {message}", filter=lambda record: "src.parser" in record["name"]
    )


async def main():

    setup_logging()

    project_root = Path(__file__).resolve().parent.parent

    config_path = project_root / "config" / "settings.yaml"
    config = load_config(config_path)

    input_urls_path = project_root / config["paths"]["input_path"]
    output_dir_path = project_root / config["paths"]["output_dir"]

    await start_process(
        input_path=str(input_urls_path),
        output_dir=str(output_dir_path),
        api_key=config["api"]["api_key"],
        api_base=config["api"]["api_base"]
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)