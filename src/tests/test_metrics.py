import pytest
import httpx

@pytest.mark.asyncio
async def test_metrics():
    async with httpx.AsyncClient() as ac:
        response = await ac.get("http://localhost:8000/metrics")
        print(response.status_code)
        print(response.text)
        assert response.status_code == 200
        assert "auth_success_total" in response.text
        assert "auth_failure_total" in response.text
        assert "request_count" in response.text
        assert "request_duration_seconds" in response.text
