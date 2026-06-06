import time
import uuid
import aiohttp
import asyncio
from loguru import logger
import json


class TokenManager:
    """
    Класс для управления токеном: получение, обновление по истечении времени жизни (TTL)
    с защитой от одновременного обновления.
    """

    def __init__(self, api_key, scope='GIGACHAT_API_PERS', ttl=1740):
        """
        :param api_key: Ключ API для авторизации.
        :param scope: Область доступа (scope).
        :param ttl: Время жизни токена в секундах (по умолчанию 29 минут = 1740 сек).
        """

        self.api_key = api_key
        self.scope = scope
        self.ttl = ttl

        self._token = None
        self._token_time = 0
        self._lock = asyncio.Lock()


    async def _fetch_new_token(self):
        """Приватный метод для запроса нового токена."""

        logger.info("Токен устарел. Запрашиваю новый...")

        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        rq_uid = str(uuid.uuid4())

        payload = {'scope': self.scope}
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': rq_uid,
            'Authorization': f'Basic {self.api_key}'
        }

        try:
            async with (aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=1)) as session):
                async with session.post(url, headers=headers, data=payload, ssl=False) as response:
                    response.raise_for_status()

                    data = await response.json()
                    self._token = data.get("access_token")

                    if not self._token:
                        data_json_str = json.dumps(data, ensure_ascii=False, indent=2)
                        logger.error(
                            f"В ответе сервера отсутствует поле 'access_token'. Полный ответ сервера:\n{data_json_str}"
                        )
                        return None

                    self._token_time = time.time()
                    logger.info("Новый access token успешно получен и сохранен.")
                    return self._token

        except Exception as e:
            logger.error(f"Ошибка при запросе токена: {e}")
            return None


    async def get_token(self):
        """
        Публичный метод для получения токена.
        Использует блокировку для предотвращения одновременных запросов.
        """
        current_time = time.time()

        # Быстрая проверка без ожидания блокировки (оптимизация)
        if self._token and (current_time - self._token_time) < self.ttl:
            logger.debug("Используем существующий токен из кэша.")
            return self._token

        # Если токен устарел или отсутствует, входит в блокировку
        async with self._lock:
            # Проверяет токен снова, так как другая корутина могла его обновить
            if not self._token or (time.time() - self._token_time) >= self.ttl:
                return await self._fetch_new_token()

            logger.debug("Другой поток обновил токен, используем его.")
            return self._token