from typing import Any, Dict


async def summarize_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize bookmark content.

    Parameters:
        payload: {"text": "..."}

    Returns:
        dict: {"summary": str}

    Usage:
        await summarize_text({"text": "..."})

    Examples:
        See tests.

    Notes:
        Will integrate OpenAI with caching.

    See Also:
        analyzer.py, tagger.py
    """
    text = payload.get("text", "")
    return {"status": "ok", "summary": text[:120]}
