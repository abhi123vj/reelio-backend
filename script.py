import instaloader
from datetime import timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Instagram Reel Metadata API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

loader = instaloader.Instaloader()



def get_post_metadata(shortcode: str) -> dict:
    post = instaloader.Post.from_shortcode(loader.context, shortcode)

    if not post.is_video:
        raise ValueError("The provided post is not a video/reel.")

    location = None
    if post.location:
        location = {
            "id": post.location.id,
            "name": post.location.name,
            "slug": post.location.slug,
            "lat": post.location.lat,
            "lng": post.location.lng,
        }

    owner = post.owner_profile
    return {
        "shortcode": post.shortcode,
        "owner": {
            "username": post.owner_username,
            "id": post.owner_id,
            "full_name": owner.full_name if owner else None,
            "is_verified": owner.is_verified if owner else None,
            "followers": owner.followers if owner else None,
        },
        "title": post.title,
        "caption": post.caption,
        "hashtags": list(post.caption_hashtags) if post.caption_hashtags else [],
        "mentions": list(post.caption_mentions) if post.caption_mentions else [],
        "tagged_users": [u.username for u in post.tagged_users] if post.tagged_users else [],
        "date_utc": post.date_utc.replace(tzinfo=timezone.utc).isoformat(),
        "date_local": post.date_local.isoformat(),
        "stats": {
            "likes": post.likes,
            "comments": post.comments,
            "video_view_count": post.video_view_count,
            "video_duration": post.video_duration,
        },
        "media": {
            "video_url": post.video_url,
            "thumbnail_url": post.url,
        },
        "is_sponsored": post.is_sponsored,
        "location": location,
        "accessibility_caption": post.accessibility_caption,
    }


@app.get("/reel/{shortcode}")
def get_reel(shortcode: str):
    """
    Fetch metadata for an Instagram Reel by shortcode.
    Example: /reel/DTfqhNhk6Sf
    The response includes a video_url you can use directly in a <video> tag.
    """
    try:
        metadata = get_post_metadata(shortcode)
    except instaloader.exceptions.InstaloaderException as e:
        raise HTTPException(status_code=502, detail=f"Instagram error: {e}")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return metadata


@app.get("/health")
def health():
    return {"status": "ok"}
