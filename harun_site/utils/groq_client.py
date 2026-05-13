import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

# Proje kokunu bul - harun_site/utils/groq_client.py'den 3 ust dizin
_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parent.parent.parent
_CONTEXT_PATH = _PROJECT_ROOT / "portfolio_context.md"

print(f"[GROQ] Project root: {_PROJECT_ROOT}", file=sys.stderr)
print(f"[GROQ] Context path: {_CONTEXT_PATH}", file=sys.stderr)
print(f"[GROQ] File exists: {_CONTEXT_PATH.exists()}", file=sys.stderr)

if not _CONTEXT_PATH.exists():
    # Alternatif: rxconfig.py'nin yanini dene
    _ALT_PATH = Path.cwd() / "portfolio_context.md"
    print(f"[GROQ] Trying cwd: {_ALT_PATH}, exists: {_ALT_PATH.exists()}", file=sys.stderr)
    _CONTEXT_PATH = _ALT_PATH

try:
    _portfolio_context = _CONTEXT_PATH.read_text(encoding="utf-8")
    _portfolio_context = _portfolio_context.replace("\x00", "")
    print(f"[GROQ] Context loaded: {len(_portfolio_context)} chars", file=sys.stderr)
except Exception as e:
    print(f"[GROQ] FAILED to read context: {e}", file=sys.stderr)
    _portfolio_context = "Portfolyo bilgisi yuklenemedi."

_SYSTEM_PROMPT = f"""Sen Harun Dülger adlı bir yazılım mühendisinin kişisel portfolyo asistanısın.
SADECE aşağıdaki bilgilere dayanarak cevap ver.
Bu bilgilerin dışında HİÇBİR şey uydurma, tahmin etme veya training datandan getirme.
Bilmediğin şeyleri 'Bu konuda bilgim yok' diyerek reddet.
Türkçe soruya Türkçe, İngilizce soruya İngilizce cevap ver.

====== PORTFOLYO BİLGİLERİ BAŞLANGICI ======
{_portfolio_context}
====== PORTFOLYO BİLGİLERİ SONU ======

Bu bilgilerin dışına çıkma. Yukarıdakiler dışında hiçbir bilgiyi doğru kabul etme."""


async def stream_chat(messages: list[dict]):
    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    stream = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": _SYSTEM_PROMPT}] + messages,
        stream=True,
        max_tokens=1024,
        temperature=0.3,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
