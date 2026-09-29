from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db, get_current_company_user
from app.models.user import User
from app.models.offer import Offer
from app.schemas.offer import OfferBase, OfferCreate, OfferResponse


router = APIRouter()

@router.get("/", response_model=list[OfferResponse])
def get_offers(
    skip: int = 0, 
    limit: int= 100, 
    db: Session = Depends(get_db)
):
    query = select(Offer).where(Offer.is_active == True).offset(skip).limit(limit)
    offers = db.scalars(query).all()
    return offers

@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer(
    offer_id: int, 
    db: Session = Depends(get_db)
):
    offer = db.get(Offer, offer_id)
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Oferta no encontrada"
        )
    return offer

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