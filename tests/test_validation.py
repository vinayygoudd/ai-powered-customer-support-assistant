import pytest
from app.utils.validators import validate_customer_id, validate_message, validate_rating, ValidationError

def test_validators():
    assert validate_customer_id("CUST-123") == "CUST-123"
    assert validate_message(" hello   world ") == "hello world"
    assert validate_rating(5) == 5

@pytest.mark.parametrize("value", ["", "a" * 5001, None])
def test_invalid_message(value):
    with pytest.raises(ValidationError):
        validate_message(value)
