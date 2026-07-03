from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_pagelist_service
from app.schemas.pagelist import (
    CheckPagenameRequest,
    CheckPagenameResponse,
    PagelistResponse,
)
from app.services.pagelist import PageListService

router = APIRouter(prefix="/v1", tags=["pagelist"])


@router.get("/pagelist", response_model=PagelistResponse)
def get_pagelist(
    svc: PageListService = Depends(get_pagelist_service),
):
    titles = svc.get_pagelist()
    return PagelistResponse(
        total=len(titles),
        titles=titles,
        cache_valid=svc.cache_valid,
        cached_at=svc.cached_at,
    )


@router.post("/check-pagename", response_model=CheckPagenameResponse)
def check_pagename(
    req: CheckPagenameRequest,
    svc: PageListService = Depends(get_pagelist_service),
):
    matched = svc.check_pagename(req.text)
    return CheckPagenameResponse(total=len(matched), matched_titles=matched)
