from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.api.errors.route import EnvelopeRoute
from app.modules.access.models import User
from app.modules.access.schemas import UserOut

router = APIRouter(prefix="/access", tags=["access"], route_class=EnvelopeRoute)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
