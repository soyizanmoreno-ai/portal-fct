from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.deps import get_db, get_current_company_user
from app.models.user import User
from app.models.offer import Offer
from app.schemas.offer import OfferCreate, OfferResponse, OfferStatusUpdate, OfferUpdate


router = APIRouter()

@router.get("/", response_model=list[OfferResponse])
@router.get("/me", response_model=list[OfferResponse], include_in_schema=False)
def get_offers(
    search: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Offer).where(Offer.is_active.is_(True))
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Offer.title.ilike(pattern), Offer.description.ilike(pattern)))
    query = query.options(selectinload(Offer.company).selectinload(User.company_profile))
    return db.scalars(query.order_by(Offer.id.desc()).offset(skip).limit(limit)).all()


@router.get("/mine", response_model=list[OfferResponse])
def get_company_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_company_user),
):
    query = select(Offer).where(Offer.company_id == current_user.id).order_by(Offer.id.desc())
    return db.scalars(query).all()

@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = db.get(Offer, offer_id)
    if not offer or not offer.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Oferta no encontrada"
        )
    return offer


def get_owned_offer(offer_id: int, db: Session, current_user: User) -> Offer:
    offer = db.get(Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oferta no encontrada")
    if offer.company_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes modificar esta oferta")
    return offer


@router.patch("/{offer_id}", response_model=OfferResponse)
def update_offer(
    offer_id: int,
    offer_in: OfferUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_company_user),
):
    offer = get_owned_offer(offer_id, db, current_user)
    for field, value in offer_in.model_dump(exclude_unset=True).items():
        setattr(offer, field, value)
    db.commit()
    db.refresh(offer)
    return offer


@router.patch("/{offer_id}/status", response_model=OfferResponse)
def update_offer_status(
    offer_id: int,
    status_update: OfferStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_company_user),
):
    offer = get_owned_offer(offer_id, db, current_user)
    offer.is_active = status_update.is_active
    db.commit()
    db.refresh(offer)
    return offer

@router.post("/", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def create_offer(offer_in: OfferCreate,db: Session = Depends(get_db),current_user: User = Depends(get_current_company_user)):
    new_offer = Offer(title=offer_in.title,description=offer_in.description,company_id=current_user.id)

    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)

    return new_offer