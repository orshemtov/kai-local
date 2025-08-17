import httpx


class TelegramClient:
    def __init__(self, bot_token: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.files_base_url = f"https://api.telegram.org/file/bot{bot_token}"
        self.client = httpx.Client(base_url=self.base_url)

    def send_message(self, chat_id: int, message: str):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
        }
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_file(self, file_id: str):
        url = f"{self.base_url}/getFile"
        payload = {"file_id": file_id}
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        response_body: dict = response.json()

        result = response_body.get("result")
        if not result:
            raise ValueError("No result found in response")

        file_path = result.get("file_path")
        if not file_path:
            raise ValueError("File path not found in response")

        file_url = f"{self.files_base_url}/{file_path}"
        response = self.client.get(file_url)
        response.raise_for_status()

        return response.content
