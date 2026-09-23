from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db, get_current_company_user
from app.models.user import User
from app.models.offer import Offer
from app.schemas.offer import OfferBase, OfferCreate, OfferResponse


router = APIRouter()

@router.post("/", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def create_offer(
    offer_in: OfferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_company_user)
):
    new_offer = Offer(
        title=offer_in.title,
        description=offer_in.description,
        company_id=current_user.id
    )

    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)

    return new_offer