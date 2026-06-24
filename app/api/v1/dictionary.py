from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.modules.access.models import User
from app.modules.dictionary import service
from app.modules.dictionary.factory import get_dictionary_providers
from app.modules.dictionary.provider import DictionaryProvider
from app.modules.dictionary.schemas import DictionaryEntryOut

router = APIRouter(prefix="/dictionary", tags=["dictionary"], route_class=EnvelopeRoute)


@router.get("/lookup", response_model=DictionaryEntryOut)
async def lookup(
    word: str = Query(min_length=1),
    source_lang: str = Query(default="de"),
    target_lang: str = Query(default="ru"),
    db: AsyncSession = Depends(get_db),
    providers: list[DictionaryProvider] = Depends(get_dictionary_providers),
    _: User = Depends(get_current_user),
) -> DictionaryEntryOut:
    entry = await service.lookup(
        db, providers, word=word, source_lang=source_lang, target_lang=target_lang
    )
    return DictionaryEntryOut.model_validate(entry)
