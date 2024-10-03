from typing import Annotated, Optional

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.user import UserRead


class CoinPaymentBase(BaseModel):
    amount: Annotated[int, Field(ge=0)]
    comment: Optional[Annotated[str, Field(max_length=255)]] = None
    user_id: Optional[int] = None
    payer_id: Optional[int] = None



class CoinPaymentCreate(CoinPaymentBase):
    pass


class CoinPaymentRead(CoinPaymentBase):
    id: int
    user: Optional["UserRead"] = None
    payer: Optional["UserRead"] = None

    model_config = ConfigDict(
        from_attributes=True
    )
