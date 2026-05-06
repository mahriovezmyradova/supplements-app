import requests
import streamlit as st
import os


def _get_hf_token() -> str | None:
    try:
        tok = st.secrets.get("HF_TOKEN") or st.secrets.get("HUGGINGFACE_TOKEN")
        if tok:
            return tok
    except Exception:
        pass
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")


def transcribe_with_huggingface(audio_bytes: bytes) -> str | None:
    """Send raw audio bytes to HuggingFace Inference API (Whisper large-v3).
    Returns the transcript string, or None on error.
    No local model is loaded — zero extra memory on Streamlit Cloud."""
    token = _get_hf_token()
    if not token:
        st.error(
            "HuggingFace API Token fehlt. "
            "Bitte HF_TOKEN in .streamlit/secrets.toml eintragen."
        )
        return None

    API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.post(API_URL, headers=headers, data=audio_bytes, timeout=60)
    except requests.exceptions.Timeout:
        st.error("Zeitüberschreitung — API hat nicht geantwortet. Bitte erneut versuchen.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Netzwerkfehler: {e}")
        return None

    if resp.status_code == 200:
        return resp.json().get("text", "")
    elif resp.status_code == 503:
        estimated = resp.json().get("estimated_time", 20)
        st.warning(
            f"Whisper-Modell wird gerade geladen (~{int(estimated)} s). "
            "Bitte in einem Moment erneut transkribieren."
        )
        return None
    elif resp.status_code == 401:
        st.error("Ungültiger HuggingFace API Token.")
        return None
    else:
        st.error(f"API-Fehler {resp.status_code}: {resp.text[:200]}")
        return None
