from app.services.llm_service import MockLLMProvider, LLMService

def test_prompt_manager_loads_versioned_template(app):
    prompts = app.extensions["services"]["prompts"]
    prompt = prompts.response_prompt(
        customer_message="My invoice is wrong",
        predicted_category="Billing",
        predicted_priority="High",
        ticket_status="Open",
        human_review_required=False,
    )
    assert "My invoice is wrong" in prompt
    assert prompts.VERSION == "v1.0"

def test_llm_rejects_secret_like_output():
    assert not LLMService.validate_response("api_key=sk-abcdefghijklmnopqrstuvwxyz123456")
    assert LLMService.validate_response("A safe support response.")

def test_mock_provider_is_deterministic():
    provider = MockLLMProvider()
    prompt = "Customer message:\nThe app crashes\nPredicted category: Technical"
    assert provider.generate(prompt) == provider.generate(prompt)
