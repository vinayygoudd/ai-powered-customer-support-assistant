import re

class ValidationError(ValueError):
    pass

def validate_customer_id(customer_id):
    if type(customer_id) is not str:
        raise ValidationError("customer_id must be a string")
    value = customer_id.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise ValidationError("customer_id must contain 1-64 letters, digits, underscores, or hyphens")
    return value

def validate_message(message):
    if type(message) is not str:
        raise ValidationError("message must be a string")
    value = re.sub(r"\s+", " ", message).strip()
    if not value:
        raise ValidationError("message cannot be empty")
    if len(value) > 5000:
        raise ValidationError("message must be 5000 characters or fewer")
    return value

def validate_rating(rating):
    if type(rating) is not int or rating < 1 or rating > 5:
        raise ValidationError("rating must be an integer from 1 to 5")
    return rating
