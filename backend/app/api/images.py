"""Live image search via Pexels, proxied server-side.

Deliberately does not download/persist anything -- the frontend gets back
hotlink URLs (Pexels' own CDN) to display directly, and nothing ever touches
disk or git in this repo. That's not an incidental detail: Pexels images are
free to use (including commercially) but this repo shouldn't become a stash
of someone else's photos, and images picked for one dashboard mockup
shouldn't outlive the session that picked them. If real persistence is ever
needed (e.g. "pin this exact image to this exact dashboard"), that's a
deliberate choice to make later, not a side effect of caching for
convenience.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.config import get_settings
from app.db.models.user import User

router = APIRouter(prefix="/api/images", tags=["images"])

PEXELS_API_URL = "https://api.pexels.com/v1/search"


@router.get("/search")
async def search_images(
    query: str = Query(min_length=1, max_length=100),
    per_page: int = Query(default=6, ge=1, le=20),
    _user: User = Depends(get_current_user),
) -> list[dict]:
    settings = get_settings()
    if not settings.pexels_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Image search isn't configured (missing API key)"
        )

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            PEXELS_API_URL,
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
            headers={"Authorization": settings.pexels_api_key},
        )
    if resp.status_code != 200:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Image provider request failed")

    photos = resp.json().get("photos", [])
    return [
        {
            "id": p["id"],
            "url": p["src"]["large"],
            "alt": p.get("alt") or query,
            "photographer": p["photographer"],
            "photographer_url": p["photographer_url"],
        }
        for p in photos
    ]
