from __future__ import annotations
PLATFORM_LIMITS = {"X": 280, "THREADS": 500, "FACEBOOK": 63206, "INSTAGRAM": 2200, "TIKTOK": 2200, "PINTEREST": 500, "YOUTUBE": 5000}

def format_for_platform(master: dict, platform: str) -> dict:
    platform = platform.upper()
    if platform not in PLATFORM_LIMITS:
        raise ValueError(f"unsupported platform: {platform}")
    text = (master.get("caption") or master.get("body") or "").strip()
    cta = (master.get("cta") or "Learn more").strip()
    disclosure = (master.get("disclosure") or "#ad").strip()
    limit = PLATFORM_LIMITS[platform]
    if platform == "X":
        text = f"{master.get('hook', '').strip()} {text} {cta}".strip()
    elif platform == "PINTEREST":
        text = f"{master.get('title', '').strip()} — {text} {cta}".strip()
    else:
        text = f"{master.get('hook', '').strip()}\n\n{text}\n\n{cta}".strip()
    if disclosure and disclosure.lower() not in text.lower():
        text = f"{text}\n{disclosure}"
    if len(text) > limit:
        raise ValueError(f"{platform} content exceeds configured limit")
    return {"platform": platform, "text": text, "hashtags": master.get("hashtags", []), "media_required": platform in {"TIKTOK", "INSTAGRAM", "YOUTUBE", "PINTEREST"}}
