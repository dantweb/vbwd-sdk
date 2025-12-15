import requests
import time
import os


class LoopAIClient:
    """Client for LoopAI API integration."""

    def __init__(self, base_url=None, api_key=None):
        self._base_url = base_url or os.getenv('LOOPAI_API_URL', 'http://loopai-web:5000')
        self._api_key = api_key or os.getenv('LOOPAI_API_KEY')
        self._agent_id = int(os.getenv('LOOPAI_AGENT_ID', '1'))

    def run_diagnostic(self, data: dict) -> dict:
        """Submit diagnostic request to LoopAI."""
        response = requests.post(
            f'{self._base_url}/api/public/agent/{self._agent_id}/action/diagnose/',
            json=data,
            headers=self._headers(),
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def poll_for_result(self, execution_id: str, timeout: int = 3600, interval: int = 60) -> dict:
        """Poll for execution result with timeout."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = requests.get(
                f'{self._base_url}/api/execution/{execution_id}/status/',
                headers=self._headers(),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'COMPLETED':
                return data.get('result', {})
            elif data.get('status') == 'FAILED':
                raise Exception(f"LoopAI execution failed: {data.get('error')}")

            time.sleep(interval)

        raise Exception(f"Timeout waiting for result after {timeout} seconds")

    def _headers(self) -> dict:
        headers = {'Content-Type': 'application/json'}
        if self._api_key:
            headers['Authorization'] = f'Bearer {self._api_key}'
        return headers
