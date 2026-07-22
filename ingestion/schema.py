from pydantic import BaseModel, Field, field_validator


class OrderEvent(BaseModel):
    """
    Data contract for incoming order events.
    Any record that doesn't match this shape is rejected
    BEFORE it reaches Kafka (quarantined with a reason).
    """
    order_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    product: str = Field(min_length=1)
    price: float = Field(gt=0)
    quantity: int = Field(gt=0)

    @field_validator("price")
    @classmethod
    def price_must_be_reasonable(cls, v: float) -> float:
        if v > 1_000_000:
            raise ValueError("price exceeds reasonable maximum")
        return v
