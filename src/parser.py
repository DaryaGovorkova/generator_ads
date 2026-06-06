import aiohttp
import asyncio
from loguru import logger
from bs4 import BeautifulSoup
import json


async def fetch_title(session, url):
    """
    Извлекает заголовок из HTML-кода.
    """
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            html = await response.text()
            logger.info(f"Запрос к {url} выполнен успешно")

            soup = BeautifulSoup(html, 'html.parser')
            title_tag = soup.find('title')

            if title_tag and title_tag.string:
                return {"title": title_tag.string.strip()}

            logger.warning(f"Тег <title> отсутствует на странице {url}")
            return {"title": "Без названия."}

    except Exception as e:
        logger.error(f"Ошибка при парсинге {url}: {e}")
        return {"title": "Ошибка загрузки."}



async def generate_ad_text(session, url, api_base, giga_token):
    """
    Генерирует рекламный текст с помощью GigaChat API.
    """

    prompt = f"""Составь короткое рекламное описание для заведения, на основе его сайта {url}."""

    payload = {
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 1,
        "repetition_penalty": 1

    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {giga_token}"
    }

    title = await fetch_title(session, url)

    if title == {"title": "Ошибка загрузки."}:
        logger.warning(f"Сайт {url} недоступен. Пропускаем генерацию.")
        return {"answer": "Ошибка доступа к сайту заведения."}



    try:
        async with session.post(api_base, headers=headers, json=payload, ssl=False, timeout=20) as response:
            response.raise_for_status()
            data = await response.json()

            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                content = message.get("content")

                if content:
                    return {"answer": content}

            logger.warning(f"API вернул неожиданную структуру или пустой 'content' для {url}.")
            logger.debug(f"Ответ API: {data}")
            return {"answer": "Пустой или некорректный ответ от API"}

    except Exception as e:
        logger.error(
            f"Произошла ошибка в ответе сервера: {e}."
        )
        return {"answer": "Ошибка генерации"}