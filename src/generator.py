import json
import aiohttp
import asyncio
import aiofiles
from loguru import logger
from urllib.parse import urlparse
from auth_token import TokenManager
from src.parser import fetch_title, generate_ad_text
from pathlib import Path


async def constructor(session, url, api_base, output_dir,token_manager):
    """
    Обрабатывает один URL: получает заголовок, рекламный текст и сохраняет результат в json-файл.
    """

    access_token = await token_manager.get_token()

    title_task = asyncio.create_task(fetch_title(session, url))
    ad_text_task = asyncio.create_task(generate_ad_text(session, url, api_base, access_token))

    title, ad_text = await asyncio.gather(title_task, ad_text_task)

    merged_answers = title | ad_text

    #Создание названия файла
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(".", "_")
    path = parsed_url.path.strip("/").replace("/", "_") or "index"
    file_name = f"{domain}_{path}.json"

    # Полный путь к файлу для сохранения
    output_path = Path(output_dir)
    filepath = output_path / file_name

    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(json.dumps(merged_answers, ensure_ascii=False, indent=2))

    logger.info(f"Имя файла успешно сгенерировано: {file_name}")



async def start_process(input_path, output_dir, api_key, api_base):
    """
    Читает список URL из файла и запускает их асинхронную обработку.
    """

    token_manager = TokenManager(api_key=api_key)
    token = await token_manager.get_token()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Создана (или уже существует) директория для вывода: {output_dir}")

    with open(input_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        logger.warning("Файл со ссылками пуст.")
        return

    logger.info(f"Найдено {len(urls)} URL для обработки.")


    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=1)) as session:
        tasks = [
            constructor(session, url, api_base, output_dir, token_manager)
            for url in urls
        ]
        await asyncio.gather(*tasks)