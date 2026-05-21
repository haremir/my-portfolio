import hashlib
import json
import os
import re
import sys

from dotenv import load_dotenv
from groq import AsyncGroq

from harun_site.utils.context_builder import (
    build_case_study_directive,
    build_context_for_messages,
    match_projects_for_query,
)

load_dotenv()

MODEL_FAST = os.environ.get("GROQ_CHAT_MODEL_FAST", "llama-3.1-8b-instant")
MODEL_DEEP = os.environ.get("GROQ_CHAT_MODEL_DEEP", "llama-3.3-70b-versatile")
MODEL_ADMIN = os.environ.get("GROQ_ADMIN_MODEL", MODEL_FAST)
CHAT_MAX_TOKENS = int(os.environ.get("GROQ_CHAT_MAX_TOKENS", "512"))
CHAT_MAX_HISTORY = int(os.environ.get("GROQ_CHAT_MAX_HISTORY", "12"))
ADMIN_AI_ON_LOAD = os.environ.get("ADMIN_AI_ON_LOAD", "true").lower() in ("1", "true", "yes")

_DEFAULT_DEEP_ROUTING_KEYWORDS = (
    "mimari", "architecture", "trade-off", "trade off", "multi-tenant", "multi tenant",
    "case study", "implementasyon", "production", "ölçek", "neden seç",
    "karşılaştır", "detaylı", "recruiter", "işe alım", "backend mimar",
    "rag ", " pipeline", "tenant", "postgresql", "fastapi",
)
_DEEP_ROUTING_KEYWORDS = tuple(
    keyword
    for keyword in (
        item.strip()
        for item in os.environ.get("GROQ_CHAT_ROUTING_DEEP_KEYWORDS", "").split(",")
    )
    if keyword
) or _DEFAULT_DEEP_ROUTING_KEYWORDS
_ROUTING_SHORT_MAX_CHARS = int(os.environ.get("GROQ_CHAT_ROUTING_PROJECT_SHORT_MAX_CHARS", "140"))
_ROUTING_DEEP_MIN_CHARS = int(os.environ.get("GROQ_CHAT_ROUTING_DEEP_MIN_CHARS", "140"))


def validate_groq_key() -> bool:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        print(
            "[GROQ] WARNING: GROQ_API_KEY is not set. "
            "All AI chat features will return error messages to users. "
            "Set GROQ_API_KEY in your .env file before deploying.",
            file=sys.stderr,
        )
        return False
    print(f"[GROQ] GROQ_API_KEY present (length={len(key)}).", file=sys.stderr)
    return True


def is_rate_limit_error(exc: BaseException) -> bool:
    err = str(exc).lower()
    return "rate_limit" in err or "rate limit" in err or "429" in err


def user_message_for_groq_error(exc: BaseException) -> str:
    if is_rate_limit_error(exc):
        wait_hint = ""
        match = re.search(r"try again in (\d+m[\d.]*s)", str(exc), re.IGNORECASE)
        if match:
            wait_hint = f" Yaklaşık {match.group(1)} sonra tekrar dene."
        return (
            "⚠️ Groq günlük token limitine ulaşıldı (ücretsiz kotanın dolmuş olabilir)."
            + wait_hint
            + " Bir süre bekleyebilir veya console.groq.com üzerinden kotayı kontrol edebilirsin."
        )
    err = str(exc).lower()
    if "api_key" in err or "authentication" in err or "invalid_api_key" in err:
        return "⚠️ Yapay zeka servisi şu an yapılandırılmamış. Lütfen daha sonra tekrar deneyin."
    return "⚠️ Bir hata oluştu, lütfen tekrar deneyin."


_SYSTEM_PROMPT_TEMPLATE = """Sen Harun Emirhan Bostancı'sın — portfolyo sitesinde ziyaretçilerle konuşuyorsun.
Gerçek kişi gibi konuş; "AI asistanım" deme. Sadece aşağıdaki bilgilere dayan, uydurma.

Kapsam: projeler, deneyim, eğitim, blog, iş birliği. Genel kod öğretme / algoritma yok.
Portfolyodaki teknolojilerle (RAG, YOLO, LangChain, PostgreSQL, Docker…) kısa kavramsal soru → deneyiminden yanıtla.
Kapsam dışı → kibarca portföye yönlendir; "kapsam dışı" deme.

Ton: doğal, özgüvenli, abartısız coşku yok. En fazla 3-4 cümle veya 4-5 madde.
Markdown: **kalın**, - madde. Proje sorularında **proje adı** + teknoloji listesi.
Belirli bir proje sorulduğunda ve context'te Case Study URL varsa, İLK yanıtında bile
sonuna mutlaka ekle: [→ Case Study'yi Gör](/projects/<slug>) — kullanıcı tekrar sormasın.
İletişim: LinkedIn https://www.linkedin.com/in/haremir826/ · GitHub https://github.com/haremir · harunemirhan826@gmail.com

====== BİLGİLERİM ======
{context}
====== BİLGİLERİM SONU ======"""


_ADMIN_ANALYTICS_PROMPT = """\
Portfolyo ziyaretçi analitik danışmanısın. Sohbet kayıtlarından stratejik içgörü ver.
Niyetler: teknik / işe alım / proje / kişisel / iş birliği / tech stack.
3-6 cümle veya kısa madde; **kalın** vurgu; son satırda 1-3 aksiyon. Türkçe.

{log_section}
"""


def _log_usage(label: str, model: str, usage, *, context_chars: int, history_turns: int) -> None:
    if usage is None:
        print(
            f"[GROQ] {label} model={model} context_chars={context_chars} "
            f"history_turns={history_turns}",
            file=sys.stderr,
        )
        return
    print(
        f"[GROQ] {label} model={model} "
        f"in={getattr(usage, 'prompt_tokens', '?')} "
        f"out={getattr(usage, 'completion_tokens', '?')} "
        f"context_chars={context_chars} history_turns={history_turns}",
        file=sys.stderr,
    )


def trim_chat_history(messages: list[dict], max_messages: int | None = None) -> list[dict]:
    limit = max_messages if max_messages is not None else CHAT_MAX_HISTORY
    if len(messages) <= limit:
        return messages
    return messages[-limit:]


def _last_user_message(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return str(msg.get("content", ""))
    return ""


def select_visitor_chat_model(last_user_message: str, *, project_matched: bool = False) -> str:
    override = os.environ.get("GROQ_CHAT_MODEL", "").strip()
    if override:
        return override
    msg = last_user_message.lower()
    # Proje sorusu: kısa istekler için hızlı model; derin teknik sorgular için deep model.
    if project_matched and not any(k in msg for k in _DEEP_ROUTING_KEYWORDS) and len(msg) <= _ROUTING_SHORT_MAX_CHARS:
        return MODEL_FAST
    if len(msg) > _ROUTING_DEEP_MIN_CHARS or any(k in msg for k in _DEEP_ROUTING_KEYWORDS):
        return MODEL_DEEP
    return MODEL_FAST


def _build_visitor_system_prompt(messages: list[dict]) -> tuple[str, str]:
    """Return (system_prompt, last_user_message)."""
    trimmed = trim_chat_history(messages)
    last_user = _last_user_message(trimmed)
    context = build_context_for_messages(trimmed)
    directive = build_case_study_directive(last_user)
    if directive:
        context = f"{context}\n\n{directive}"
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(context=context)
    return system_prompt, last_user


def _build_analytics_log_section(chat_logs: list[dict]) -> str:
    if not chat_logs:
        return "SOHBET KAYIT VERİSİ: Henüz kayıt yok."

    lines = [f"SOHBET KAYIT VERİSİ ({len(chat_logs)} kayıt):"]
    for i, log in enumerate(chat_logs, 1):
        lines.append(
            f"\n[{i}] {log.get('timestamp', '')} · {log.get('message_count', 0)} mesaj"
        )
        for j, q in enumerate(log.get("user_samples", []), 1):
            lines.append(f"  K{j}: {q[:160]}")
        for j, a in enumerate(log.get("assistant_samples", []), 1):
            lines.append(f"  A{j}: {a[:100]}")
    return "\n".join(lines)


async def stream_chat(messages: list[dict]):
    trimmed = trim_chat_history(messages)
    system_prompt, last_user = _build_visitor_system_prompt(messages)
    project_matched = bool(match_projects_for_query(last_user))
    model = select_visitor_chat_model(last_user, project_matched=project_matched)

    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    stream = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}] + trimmed,
        stream=True,
        max_tokens=CHAT_MAX_TOKENS,
        temperature=0.2,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
    if hasattr(stream, "usage") and stream.usage:
        _log_usage(
            "chat/stream",
            model,
            stream.usage,
            context_chars=len(system_prompt),
            history_turns=len(trimmed),
        )


async def complete_chat(messages: list[dict]) -> str:
    trimmed = trim_chat_history(messages)
    system_prompt, last_user = _build_visitor_system_prompt(messages)
    project_matched = bool(match_projects_for_query(last_user))
    model = select_visitor_chat_model(last_user, project_matched=project_matched)

    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}] + trimmed,
        stream=False,
        max_tokens=CHAT_MAX_TOKENS,
        temperature=0.2,
    )
    _log_usage(
        "chat/complete",
        model,
        response.usage,
        context_chars=len(system_prompt),
        history_turns=len(trimmed),
    )
    return response.choices[0].message.content or ""


async def summarize_conversation(messages: list[dict]) -> dict:
    """Lightweight session summary — no portfolio context."""
    lines = [
        f'{m["role"]}: {str(m.get("content", ""))[:200]}'
        for m in messages[-CHAT_MAX_HISTORY:]
    ]
    prompt = (
        "Portfolyo ziyaretçi konuşmasını özetle. SADECE geçerli JSON:\n"
        '{"summary":"2-3 cümle Türkçe","top_topics":["konu1","konu2"],'
        f'"message_count":{len(messages)}}}\n\n'
        + "\n".join(lines)
    )

    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    response = await client.chat.completions.create(
        model=MODEL_FAST,
        messages=[
            {
                "role": "system",
                "content": "Kısa Türkçe özet üret. Yalnızca istenen JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        stream=False,
        max_tokens=220,
        temperature=0.1,
    )
    _log_usage("chat/summary", MODEL_FAST, response.usage, context_chars=0, history_turns=len(lines))
    content = response.choices[0].message.content or ""
    cleaned = re.sub(r"```json|```", "", content).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return {}


def chat_logs_fingerprint(logs: list[dict]) -> str:
    parts = sorted(
        f"{log.get('filename', '')}:{log.get('mtime', 0)}:{log.get('message_count', 0)}"
        for log in logs
    )
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


async def summarize_chat_logs(chat_logs: list[dict]) -> dict:
    compact = [
        {
            "t": log.get("timestamp", "")[:16],
            "n": log.get("message_count", 0),
            "u": log.get("user_samples", [])[:3],
            "a": log.get("assistant_samples", [])[:1],
        }
        for log in chat_logs[:12]
    ]
    prompt = (
        "Sohbet kayıtlarından dashboard özeti. SADECE JSON:\n"
        '{"summary":"2-3 cümle","top_topics":["a","b","c"],'
        '"dominant_intent":"...","top_project":"...","visitor_expectation":"..."}\n'
        f"Kayıtlar:{json.dumps(compact, ensure_ascii=False)}"
    )

    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    response = await client.chat.completions.create(
        model=MODEL_ADMIN,
        messages=[
            {
                "role": "system",
                "content": "Portfolio analytics. Yalnızca JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        stream=False,
        max_tokens=400,
        temperature=0.2,
    )
    _log_usage("admin/overview", MODEL_ADMIN, response.usage, context_chars=len(prompt), history_turns=0)

    content = response.choices[0].message.content or ""
    cleaned = re.sub(r"```json|```", "", content).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as exc:
        print(
            f"[GROQ] summarize_chat_logs: JSON parse failed ({exc}). "
            f"Raw: {content[:200]!r}",
            file=sys.stderr,
        )
        return {}


async def answer_admin_chat_about_logs(
    messages: list[dict],
    chat_logs: list[dict],
) -> str:
    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    log_section = _build_analytics_log_section(chat_logs[:15])
    system_content = _ADMIN_ANALYTICS_PROMPT.format(log_section=log_section)

    llm_messages: list[dict] = [{"role": "system", "content": system_content}]
    for msg in trim_chat_history(messages, max_messages=16):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            llm_messages.append({"role": role, "content": content})

    response = await client.chat.completions.create(
        model=MODEL_DEEP,
        messages=llm_messages,
        stream=False,
        max_tokens=600,
        temperature=0.3,
    )
    _log_usage(
        "admin/assistant",
        MODEL_DEEP,
        response.usage,
        context_chars=len(system_content),
        history_turns=len(messages),
    )
    return (response.choices[0].message.content or "").strip()
