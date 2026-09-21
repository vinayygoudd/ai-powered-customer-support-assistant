import pytest
from app import create_app
from app.utils.config import Settings

@pytest.fixture()
def app(tmp_path):
    settings = Settings(
        database_path=str(tmp_path / "test.db"),
        model_dir=str(tmp_path / "models"),
        prompt_dir="app/prompts",
        openai_api_key="",
        openai_model="gpt-4o-mini",
        mock_llm=True,
        api_base_url="http://test",
        secret_key="test",
    )
    application = create_app(settings)
    return application

@pytest.fixture()
def client(app):
    return app.test_client()
