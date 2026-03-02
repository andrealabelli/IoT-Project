from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.models.database import get_db
from app.models.entities import Event, User
from app.models.schemas import EventOut

router = APIRouter(tags=["events"])


@router.get("/events", response_model=list[EventOut])
def list_events(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Event).order_by(Event.ts.desc()).limit(100).all()
