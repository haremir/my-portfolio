import hashlib
import json
import os
import re
import sys
import time
from collections import OrderedDict

import httpx
from dotenv import load_dotenv
from groq import AsyncGroq

from harun_site.utils.context_builder import (
    build_case_study_directive,
    build_context_for_messages,
    match_projects_for_query,
)

load_dotenv(override=True)

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "deepseek").strip().lower() or "deepseek"
LLM_FALLBACK_PROVIDER = os.environ.get("LLM_FALLBACK_PROVIDER", "groq").strip().lower() or "groq"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
DEEPSEEK_CHAT_MODEL_FAST = os.environ.get("DEEPSEEK_CHAT_MODEL_FAST", "deepseek-v4-flash")
DEEPSEEK_CHAT_MODEL_DEEP = os.environ.get("DEEPSEEK_CHAT_MODEL_DEEP", "deepseek-v4-pro")
DEEPSEEK_ADMIN_MODEL = os.environ.get("DEEPSEEK_ADMIN_MODEL", DEEPSEEK_CHAT_MODEL_DEEP)
DEEPSEEK_SUMMARY_MODEL = os.environ.get("DEEPSEEK_SUMMARY_MODEL", DEEPSEEK_CHAT_MODEL_FAST)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_CHAT_MODEL_FAST = os.environ.get("GROQ_CHAT_MODEL_FAST", "llama-3.1-8b-instant")
GROQ_CHAT_MODEL_DEEP = os.environ.get("GROQ_CHAT_MODEL_DEEP", "llama-3.3-70b-versatile")
GROQ_ADMIN_MODEL = os.environ.get("GROQ_ADMIN_MODEL", GROQ_CHAT_MODEL_FAST)

ACTIVE_PROVIDER = LLM_PROVIDER if (LLM_PROVIDER == "deepseek" and DEEPSEEK_API_KEY) or (LLM_PROVIDER == "groq" and GROQ_API_KEY) else (LLM_FALLBACK_PROVIDER if LLM_FALLBACK_PROVIDER in ("deepseek", "groq") else "groq")
PRIMARY_PROVIDER_NAME = "DeepSeek" if ACTIVE_PROVIDER == "deepseek" else "Groq"

MODEL_FAST = DEEPSEEK_CHAT_MODEL_FAST if ACTIVE_PROVIDER == "deepseek" else GROQ_CHAT_MODEL_FAST
MODEL_DEEP = DEEPSEEK_CHAT_MODEL_DEEP if ACTIVE_PROVIDER == "deepseek" else GROQ_CHAT_MODEL_DEEP
MODEL_ADMIN = DEEPSEEK_ADMIN_MODEL if ACTIVE_PROVIDER == "deepseek" else GROQ_ADMIN_MODEL
CHAT_MAX_TOKENS = int(os.environ.get("GROQ_CHAT_MAX_TOKENS", "512"))
CHAT_MAX_HISTORY = int(os.environ.get("GROQ_CHAT_MAX_HISTORY", "12"))
ADMIN_AI_ON_LOAD = os.environ.get("ADMIN_AI_ON_LOAD", "true").lower() in ("1", "true", "yes")
LLM_CACHE_MAX_ENTRIES = int(os.environ.get("LLM_CACHE_MAX_ENTRIES", "128"))
LLM_CACHE_TTL_SECONDS = int(os.environ.get("LLM_CACHE_TTL_SECONDS", "3600"))

_LLM_RESPONSE_CACHE: OrderedDict[str, tuple[float, str]] = OrderedDict()

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
    has_deepseek = bool(DEEPSEEK_API_KEY)
    has_groq = bool(GROQ_API_KEY)
    if has_deepseek or has_groq:
        print(
            f"[LLM] active provider={ACTIVE_PROVIDER} deepseek_key={'yes' if has_deepseek else 'no'} groq_key={'yes' if has_groq else 'no'}",
            file=sys.stderr,
        )
        return True
    print(
        "[LLM] WARNING: neither DEEPSEEK_API_KEY nor GROQ_API_KEY is set. "
        "AI chat features will return error messages to users.",
        file=sys.stderr,
    )
    return False


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
            "⚠️ Yapay zeka servisinin günlük token limitine ulaşıldı."
            + wait_hint
            + " Bir süre bekleyebilir veya sağlayıcı panelinden kotayı kontrol edebilirsin."
        )
    err = str(exc).lower()
    if "api_key" in err or "authentication" in err or "invalid_api_key" in err or "unauthorized" in err:
        return "⚠️ Yapay zeka servisi şu an yapılandırılmamış veya erişilemiyor. Lütfen daha sonra tekrar deneyin."
    return "⚠️ Bir hata oluştu, lütfen tekrar deneyin."


def _provider_order() -> list[str]:
    order: list[str] = []
    for provider in (LLM_PROVIDER, LLM_FALLBACK_PROVIDER, "deepseek", "groq"):
        if provider not in order:
            order.append(provider)
    return order


def _provider_label(provider: str) -> str:
    return "DeepSeek" if provider == "deepseek" else "Groq"


def _provider_key(provider: str) -> str:
    return DEEPSEEK_API_KEY if provider == "deepseek" else GROQ_API_KEY


def _provider_model(provider: str, kind: str) -> str:
    if provider == "deepseek":
        if kind == "deep":
            return DEEPSEEK_CHAT_MODEL_DEEP
        if kind == "admin":
            return DEEPSEEK_ADMIN_MODEL
        if kind == "summary":
            return DEEPSEEK_SUMMARY_MODEL
        return DEEPSEEK_CHAT_MODEL_FAST
    if kind == "deep":
        return GROQ_CHAT_MODEL_DEEP
    if kind == "admin":
        return GROQ_ADMIN_MODEL
    return GROQ_CHAT_MODEL_FAST


def _select_kind(last_user_message: str, *, project_matched: bool = False) -> str:
    msg = last_user_message.lower()
    if project_matched and not any(k in msg for k in _DEEP_ROUTING_KEYWORDS) and len(msg) <= _ROUTING_SHORT_MAX_CHARS:
        return "fast"
    if len(msg) > _ROUTING_DEEP_MIN_CHARS or any(k in msg for k in _DEEP_ROUTING_KEYWORDS):
        return "deep"
    return "fast"


def _build_cache_key(provider: str, model: str, system_prompt: str, messages: list[dict], *, max_tokens: int, temperature: float) -> str:
    payload = {
        "provider": provider,
        "model": model,
        "system_prompt": system_prompt,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> str | None:
    item = _LLM_RESPONSE_CACHE.get(key)
    if not item:
        return None
    cached_at, content = item
    if time.time() - cached_at > LLM_CACHE_TTL_SECONDS:
        _LLM_RESPONSE_CACHE.pop(key, None)
        return None
    _LLM_RESPONSE_CACHE.move_to_end(key)
    return content


def _cache_set(key: str, content: str) -> None:
    if not content:
        return
    _LLM_RESPONSE_CACHE[key] = (time.time(), content)
    _LLM_RESPONSE_CACHE.move_to_end(key)
    while len(_LLM_RESPONSE_CACHE) > LLM_CACHE_MAX_ENTRIES:
        _LLM_RESPONSE_CACHE.popitem(last=False)


def _normalize_messages(messages: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for message in messages:
        content = message.get("content", "")
        if content is None:
            content = ""
        elif isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        elif isinstance(content, list):
            content = "\n".join(str(item) for item in content if item is not None)
        elif not isinstance(content, str):
            content = str(content)
        normalized.append({"role": str(message.get("role", "user")), "content": content})
    return normalized


def _groq_client() -> AsyncGroq:
    return AsyncGroq(api_key=GROQ_API_KEY)


def _deepseek_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }


async def _complete_one(provider: str, model: str, messages: list[dict], *, max_tokens: int, temperature: float) -> tuple[str, object | None]:
    if provider == "deepseek":
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            response = await client.post(f"{DEEPSEEK_BASE_URL}/chat/completions", headers=_deepseek_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        content = ""
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
        return content, data.get("usage")

    client = _groq_client()
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content or "", getattr(response, "usage", None)


async def _stream_one(provider: str, model: str, messages: list[dict], *, max_tokens: int, temperature: float):
    if provider == "deepseek":
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(None, connect=10.0)) as client:
            async with client.stream("POST", f"{DEEPSEEK_BASE_URL}/chat/completions", headers=_deepseek_headers(), json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    chunk = line[5:].strip()
                    if chunk == "[DONE]":
                        break
                    try:
                        event = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    choices = event.get("choices") or []
                    if not choices:
                        continue
                    delta = (choices[0].get("delta") or {}).get("content") or ""
                    if delta:
                        yield delta
        return

    client = _groq_client()
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


_SYSTEM_PROMPT_TEMPLATE_TR = """Sen Harun Emirhan Bostancı'sın — kişisel portfolyo sitesinde ziyaretçilerle sohbet ediyorsun.
Bu site senin kendi geliştirdiğin bir Reflex (Python) uygulaması ve ziyaretçi şu an bu sitenin içinde.
KENDİN gibi konuş; "AI asistanım" veya "ben bir yapay zeka" gibi ifadeler KULLANMA. Sen Harun'sun, kendi portfolyo sitemi anlatıyorum.
Sadece aşağıdaki bilgilere dayan, bilgi uydurma. Emin olmadığın konuda dürüst ol.

## KRİTİK: BU SİTEYİ TANIT
Ziyaretçi "bu siteyi anlat" veya "bu sistemi anlat" derse:
- Bu sitenin, kendini (SelfAPI projesini) de tanıtan bir full-stack Reflex uygulaması olduğunu vurgula.
- Kullanıcı bu chatbot aracılığıyla şu anda bu siteyi KULLANIYOR — bunu belirt.
- SelfAPI projesine yönlendir: [[PROJECT_REF:selfapi]]

## Yanıt Formatı (ZORUNLU)
- Maksimum 1-2 kısa paragraf veya 3-5 madde işareti. ASLA daha uzun yazma.
- Uzun yanıt gerekiyorsa mutlaka liste ( - ) yapısı kullan, paragraf yığınına gömme.
- Her yanıtın SONUNDA, eğer bir projeden bahsediyorsan mutlaka ilgili proje linkini ekle: [[PROJECT_REF:<project_id>]]
- Eğer soru bir projeyle ilgiliyse ve o projenin case study'si varsa, yanıtın sonunda case study linkini de ekle.

## Site Navigasyonu (Ziyaretçiyi YÖNLENDİR)
Bu site şu sayfaları içeriyor — ziyaretçiyi İLGİLİ sayfaya yönlendir:
- Hakkımda: [Hakkımda](/about)
- Projelerim: [Portfolyo](/portfolio)
- Blog yazılarım: [Blog](/blog)
- Belirli bir proje: yalnızca registry token'ı kullan: [[PROJECT_REF:<project_id>]]
- Belirli bir blog: [Yazı](/blog/<slug>)
ASLA harici link verme (haremir.github.io vb.). Tüm içerik BU sitede.
Project names and URLs are immutable registry-controlled identifiers. Never invent, rewrite, pluralize, abbreviate, or autocorrect them.

## Kapsam
- Projeler, deneyim, eğitim, beceriler, blog, iş birliği, iletişim.
- Portfolyodaki teknolojilerle (RAG, YOLO, LangChain, PostgreSQL, Docker…) ilgili kısa kavramsal soru → kendi deneyiminden yanıtla.
- Genel kod öğretme, algoritma çözme veya kapsam dışı konularda kibarca ilgili sayfaya yönlendir.

## Ton ve Stil
- Doğal, özgüvenli, samimi. Abartılı coşku veya emoji seli yok.
- Markdown kullan: **kalın** vurgular, `kod` blokları, - madde işaretleri.
- Proje sorularında: **proje adı** + kullanılan teknolojiler + ne yaptığının kısa özeti.
- Case Study veya proje referansı gerekiyorsa MUTLAKA token kullan: [[PROJECT_REF:<project_id>]]
- Teknoloji sorusunda sadece liste dökme; kategorize et ve nasıl kullandığını anlat.
- "Bana bu siteyi anlat" tarzı sorularda önce SelfAPI'den bahset, sonra diğer projelere geç.

## İletişim ve İş Teklifleri (Freelance / İşe Alım)
- Ziyaretçi freelance iş teklifi, işbirliği veya işe alım (recruiter / İK) amacıyla yazıyorsa:
  1. Kendi iletişim bilgilerini (LinkedIn, E-posta) paylaş.
  2. Harun'un kendilerine doğrudan dönüş yapabilmesi için ziyaretçiden de kendi iletişim bilgilerini (isim, e-posta veya LinkedIn profili) ve proje detaylarını buraya yazmasını rica et.
- LinkedIn: https://www.linkedin.com/in/haremir826/
- GitHub: https://github.com/haremir
- E-posta: harunemirhan826@gmail.com

====== BİLGİLERİM ======
{context}
====== BİLGİLERİM SONU ======"""


_SYSTEM_PROMPT_TEMPLATE_EN = """You are Harun Emirhan Bostancı — the owner of this personal portfolio website, chatting with visitors.
This site is YOUR own Reflex (Python) full-stack application that you built. The visitor is currently INSIDE this website.
Talk as YOURSELF; do NOT use phrases like "AI assistant" or "I am an AI." You are Harun, explaining your own portfolio site.
Base your answers ONLY on the information below — do not make things up. Be honest when unsure.

## CRITICAL: INTRODUCE THIS SITE
If a visitor asks "tell me about this site" or "describe this system":
- Emphasize that this site is a full-stack Reflex application that also introduces itself (the SelfAPI project).
- Point out that the user is currently USING this site through this chatbot.
- Direct them to the SelfAPI project: [[PROJECT_REF:selfapi]]

## Response Format (REQUIRED)
- Maximum 1-2 short paragraphs or 3-5 bullet points. NEVER write longer.
- If a long answer is needed, use a list ( - ) structure, don't bury it in paragraph blocks.
- At the END of every answer, if you mention a project, MUST include the project link: [[PROJECT_REF:<project_id>]]
- If the question relates to a project and that project has a case study, also include the case study link at the end of the answer.

## Site Navigation (DIRECT Visitors)
This site includes the following pages — direct visitors to the RELEVANT page:
- About Me: [About](/about)
- Projects: [Portfolio](/portfolio)
- Blog posts: [Blog](/blog)
- Specific project: use only registry token: [[PROJECT_REF:<project_id>]]
- Specific blog: [Post](/blog/<slug>)
NEVER give external links (haremir.github.io etc.). All content is ON this site.
Project names and URLs are immutable registry-controlled identifiers. Never invent, rewrite, pluralize, abbreviate, or autocorrect them.

## Scope
- Projects, experience, education, skills, blog, collaboration, communication.
- Short conceptual questions about technologies in the portfolio (RAG, YOLO, LangChain, PostgreSQL, Docker...) → answer from your experience.
- For general coding questions, algorithm solving, or out-of-scope topics, politely direct them to the relevant page.

## Tone and Style
- Natural, confident, friendly. No excessive enthusiasm or emoji spam.
- Use Markdown: **bold** for emphasis, `code` blocks, - bullet points.
- For project questions: **project name** + technologies used + short summary of what it does.
- If a Case Study or project reference is needed, MUST use token: [[PROJECT_REF:<project_id>]]
- For technology questions, don't just list; categorize and explain how you use them.
- For "tell me about this site" type questions, start with SelfAPI, then move to other projects.

## Communication and Job Offers (Freelance / Recruitment)
- If a visitor reaches out for freelance work, collaboration, or recruitment (recruiter/HR):
  1. Share your contact information (LinkedIn, Email).
  2. Ask the visitor to also share their contact info (name, email or LinkedIn) and project details so Harun can get back to them.
- LinkedIn: https://www.linkedin.com/in/haremir826/
- GitHub: https://github.com/haremir
- Email: harunemirhan826@gmail.com

====== MY INFORMATION ======
{context}
====== END OF MY INFORMATION ======"""


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


def _chunk_text(text: str, chunk_size: int = 20):
    """Chunk a string into smaller pieces for streaming simulation."""
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def _last_user_message(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return str(msg.get("content", ""))
    return ""


def select_visitor_chat_model(last_user_message: str, *, project_matched: bool = False) -> str:
    kind = _select_kind(last_user_message, project_matched=project_matched)
    return _provider_model(ACTIVE_PROVIDER, kind)


def _get_system_prompt_template(lang: str = "tr") -> str:
    """Return the system prompt template for the given language.
    Falls back to TR if EN template is not available.
    """
    if lang == "en":
        return _SYSTEM_PROMPT_TEMPLATE_EN
    return _SYSTEM_PROMPT_TEMPLATE_TR


def _build_visitor_system_prompt(messages: list[dict]) -> tuple[str, str]:
    """Return (system_prompt, last_user_message)."""
    trimmed = trim_chat_history(messages)
    last_user = _last_user_message(trimmed)
    # Auto-detect language preference from query or fall back to TR
    has_en = any(k in last_user.lower() for k in ("hello", "tell me", "describe", "about", "what is", "explain", "portfolio", "project", "who are you"))
    lang = "en" if has_en else "tr"
    context = build_context_for_messages(trimmed, lang=lang)
    directive = build_case_study_directive(last_user)
    if directive:
        context = f"{context}\n\n{directive}"
    template = _get_system_prompt_template(lang)
    system_prompt = template.format(context=context)
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


async def stream_chat(messages: list[dict], info: dict = None):
    trimmed = trim_chat_history(messages)
    system_prompt, last_user = _build_visitor_system_prompt(messages)
    project_matched = bool(match_projects_for_query(last_user))
    kind = _select_kind(last_user, project_matched=project_matched)
    provider_messages = [{"role": "system", "content": system_prompt}] + trimmed
    cache_key = _build_cache_key(ACTIVE_PROVIDER, _provider_model(ACTIVE_PROVIDER, kind), system_prompt, provider_messages, max_tokens=CHAT_MAX_TOKENS, temperature=0.2)
    cached = _cache_get(cache_key)
    if cached is not None:
        if info is not None:
            info["provider"] = ACTIVE_PROVIDER
            info["model"] = _provider_model(ACTIVE_PROVIDER, kind)
        for part in _chunk_text(cached):
            yield part
        return

    last_exc: BaseException | None = None
    for provider in _provider_order():
        model = _provider_model(provider, kind)
        if not _provider_key(provider):
            continue
        parts: list[str] = []
        try:
            if info is not None:
                info["provider"] = provider
                info["model"] = model
            async for delta in _stream_one(provider, model, provider_messages, max_tokens=CHAT_MAX_TOKENS, temperature=0.2):
                parts.append(delta)
                yield delta
            content = "".join(parts)
            if content:
                _cache_set(cache_key, content)
            _log_usage(f"chat/stream[{_provider_label(provider)}]", model, None, context_chars=len(system_prompt), history_turns=len(trimmed))
            return
        except Exception as exc:
            last_exc = exc
            if parts:
                raise
            continue

    if last_exc is not None:
        raise last_exc


async def complete_chat(messages: list[dict], info: dict = None) -> str:
    trimmed = trim_chat_history(messages)
    system_prompt, last_user = _build_visitor_system_prompt(messages)
    project_matched = bool(match_projects_for_query(last_user))
    kind = _select_kind(last_user, project_matched=project_matched)
    provider_messages = [{"role": "system", "content": system_prompt}] + trimmed
    cache_key = _build_cache_key(ACTIVE_PROVIDER, _provider_model(ACTIVE_PROVIDER, kind), system_prompt, provider_messages, max_tokens=CHAT_MAX_TOKENS, temperature=0.2)
    cached = _cache_get(cache_key)
    if cached is not None:
        if info is not None:
            info["provider"] = ACTIVE_PROVIDER
            info["model"] = _provider_model(ACTIVE_PROVIDER, kind)
        return cached

    last_exc: BaseException | None = None
    for provider in _provider_order():
        model = _provider_model(provider, kind)
        if not _provider_key(provider):
            continue
        try:
            content, usage = await _complete_one(provider, model, provider_messages, max_tokens=CHAT_MAX_TOKENS, temperature=0.2)
            if info is not None:
                info["provider"] = provider
                info["model"] = model
            _cache_set(cache_key, content)
            _log_usage(
                f"chat/complete[{_provider_label(provider)}]",
                model,
                usage,
                context_chars=len(system_prompt),
                history_turns=len(trimmed),
            )
            return content
        except Exception as exc:
            last_exc = exc
            continue

    if last_exc is not None:
        raise last_exc
    return ""


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

    summary_messages = [
        {
            "role": "system",
            "content": "Kısa Türkçe özet üret. Yalnızca istenen JSON.",
        },
        {"role": "user", "content": prompt},
    ]

    for provider in _provider_order():
        model = _provider_model(provider, "summary")
        if not _provider_key(provider):
            continue
        try:
            content, usage = await _complete_one(provider, model, summary_messages, max_tokens=220, temperature=0.1)
            _log_usage(f"chat/summary[{_provider_label(provider)}]", model, usage, context_chars=0, history_turns=len(lines))
            cleaned = re.sub(r"```json|```", "", content).strip()
            try:
                return json.loads(cleaned)
            except (json.JSONDecodeError, ValueError):
                return {}
        except Exception:
            continue
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

    admin_messages = [
        {
            "role": "system",
            "content": "Portfolio analytics. Yalnızca JSON.",
        },
        {"role": "user", "content": prompt},
    ]

    for provider in _provider_order():
        model = _provider_model(provider, "admin")
        if not _provider_key(provider):
            continue
        try:
            content, usage = await _complete_one(provider, model, admin_messages, max_tokens=400, temperature=0.2)
            _log_usage(f"admin/overview[{_provider_label(provider)}]", model, usage, context_chars=len(prompt), history_turns=0)
            cleaned = re.sub(r"```json|```", "", content).strip()
            try:
                return json.loads(cleaned)
            except (json.JSONDecodeError, ValueError) as exc:
                print(
                    f"[LLM] summarize_chat_logs: JSON parse failed ({exc}). Raw: {content[:200]!r}",
                    file=sys.stderr,
                )
                return {}
        except Exception:
            continue
    return {}


async def answer_admin_chat_about_logs(
    messages: list[dict],
    chat_logs: list[dict],
) -> str:
    log_section = _build_analytics_log_section(chat_logs[:15])
    system_content = _ADMIN_ANALYTICS_PROMPT.format(log_section=log_section)

    llm_messages: list[dict] = [{"role": "system", "content": system_content}]
    for msg in trim_chat_history(messages, max_messages=16):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            llm_messages.append({"role": role, "content": content})

    last_exc: BaseException | None = None
    for provider in _provider_order():
        model = _provider_model(provider, "deep")
        if not _provider_key(provider):
            continue
        try:
            content, usage = await _complete_one(provider, model, llm_messages, max_tokens=600, temperature=0.3)
            _log_usage(
                f"admin/assistant[{_provider_label(provider)}]",
                model,
                usage,
                context_chars=len(system_content),
                history_turns=len(messages),
            )
            return content.strip()
        except Exception as exc:
            last_exc = exc
            continue
    if last_exc is not None:
        raise last_exc
    return ""
