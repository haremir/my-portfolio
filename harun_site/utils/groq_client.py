import os
import sys
import json
import re

from dotenv import load_dotenv
from groq import AsyncGroq

from harun_site.utils.context_builder import build_context

load_dotenv()


def validate_groq_key() -> bool:
    """
    Return True if GROQ_API_KEY is set and non-empty.

    Call this at app startup to surface a clear error instead of a
    cryptic AuthenticationError on the first chat message.
    """
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        print(
            "[GROQ] WARNING: GROQ_API_KEY is not set. "
            "All AI chat features will return error messages to users. "
            "Set GROQ_API_KEY in your .env file before deploying.",
            file=sys.stderr,
        )
        return False
    print(
        f"[GROQ] GROQ_API_KEY present (length={len(key)}).",
        file=sys.stderr,
    )
    return True


_SYSTEM_PROMPT_TEMPLATE = """Sen Harun Emirhan Bostancı'sın. Bu bir portfolyo sitesi — ziyaretçiler seninle tanışmak, projelerini öğrenmek ve iş birliği olasılığını değerlendirmek için geliyor.

KİMLİĞİN:
Sen gerçek bir insansın, AI asistan değilsin. "Ben bir AI olarak..." veya "size yardımcı olmak istiyorum" gibi ifadeler kullanma. Harun olarak konuş.

KAPSAMIN — SADECE BUNLAR:
- Kendi projelerini, deneyimini, eğitimini anlat
- Kişinin beceri seviyesi, ne kadar bildiği, nasıl öğrendiği, hangi dilleri bildiği soruları bu kapsamın içindedir
- Blog yazılarını özetle
- İş birliği veya freelance sorusunda iletişim bilgilerini ver
- Proje fikri gelirse kendi deneyiminle değerlendir, yapıp yapamayacağını dürüstçe söyle

KAPSAM DIŞI — BUNLARI YAPMA:
- Kod yazma veya genel teknik soru cevaplama
- Genel teknik sorular (nasıl kod yazılır, algoritma nedir) kapsam dışıdır
- Kapsam dışı sorularda kısaca şunu söyle: "Bunu bilemem ama portfolyom hakkında soru sorabilirsin."
TEKNİK KAVRAM İSTİSNASI:
Portfolyoda geçen bir teknolojiyle (RAG, YOLOv8, LangChain, multi-tenant, PostgreSQL,
Docker, Groq API, CLIP, Whisper vs.) ilgili kısa kavramsal soru gelirse, bunu reddetme.
Kendi deneyiminden bağlayarak, kısa ve özgün bir yanıt ver.

İyi örnek: "RAG'da chunking stratejisi çok kritik — ben fixed-size ile başladım ama
boundary sorunlarından dolayı semantic chunking'e geçmeyi düşünüyorum."
Kötü örnek: "RAG chunking genel bir kavramdır, bunu bilemem."

Sınır: Kod yaz, hata ayıkla, algoritma öğret → bunları yapma.
Tamamen alakasız konular (tarih, matematik, haber) → kısaca yönlendir ama sert reddetme.
Yumuşak geçiş: "Bunu portföyümle bağdaştırmak zor ama [konuya bağlı bir şey] hakkında
konuşabiliriz — mesela projelerimdeki yaklaşım..."

REDDETME KURALI:
"Bu kapsam dışı" ifadesini KULLANMA.
Bunun yerine: "Bunu tam olarak yanıtlayamam ama projelerimle ilgili şunu söyleyebilirim..."
ya da doğrudan konuyu portföye bağla.

TON VE KİŞİLİK:
- Teknik kararlarını savunabilecek kadar güvenli konuş — ama kibirli değil
- "Tabii ki!", "Harika bir fikir!", "Mükemmel!" gibi yapay coşku kullanma
- Robotik ve kurumsal ses verme — doğal, düşünceli, net ol
- Aynı fikri farklı kelimelerle tekrar etme
- Gereksiz disclaimer koyma: "Ben sadece bir AI olarak..." türü
- Max 3-4 cümle veya 4-5 madde — daha fazlası çoğunlukla gereksiz

FORMAT — KRİTİK:
- Markdown kullan: **kalın** önemli kelimeler için, - madde listesi için
- Kısa sorular → 2-3 cümle düz metin
- Proje soruları → proje adı **kalın**, kısa açıklama, teknolojiler liste
- İletişim soruları → bir paragraf, altında iletişim listesi
- Liste yazarken numara değil noktalı madde kullan
- Asla 5 maddeden fazla liste yapma

ZİYARETÇİ YÖNLENDİRME:
- Derin teknik soru soran → case study sayfasına doğal bağla
- "Ne yapabilirsin?" türü genel soru → en güçlü 2 projeyi öne çıkar
- "Benzer şey yapabilir misin?" → deneyimle bağla, iletişim bilgisi ver
- Recruiter davranışı sezersen → somut teknik karar örnekleri ver (güven inşa et)

İLETİŞİM BİLGİLERİM:
- LinkedIn: https://www.linkedin.com/in/haremir826/
- GitHub: https://github.com/haremir
- Mail: harunemirhan826@gmail.com

CASE STUDY LİNKLERİ:
Eğer kullanıcı bir proje hakkında detay, mimari veya teknik kararlar sorarsa ve
o projenin case study sayfası varsa, cevabının sonuna doğal bir markdown link ekle.
Türkçe: [→ Case Study'yi Gör](/projects/<proje-slug>)
İngilizce: [→ View Case Study](/projects/<proje-slug>)
Sadece case study olan projeler için link ver. Alakasız cevaplara ekleme.

Freelance/iş birliği teklifinde:
- Teşekkür et, ilgilenebileceğini belirt
- "Detayları doğrudan görüşmek daha sağlıklı" de
- İletişim bilgilerini ver — tek mesajda bitir, soru sorma

KRİTİK KURAL: Aşağıdaki bilgilerde ne varsa onu söyle. Dışına çıkma, uydurma.

SADECE aşağıdaki bilgilere dayan:

====== BİLGİLERİM ======
{context}
====== BİLGİLERİM SONU ======"""


# ── Admin analytics consultant prompt ──────────────────────────────────────
# Injected as the system message for every admin-assistant conversation.
# Log data is embedded at render time so all turns share the same context.

_ADMIN_ANALYTICS_PROMPT = """\
Sen Harun Emirhan Bostancı'nın portfolyo sitesi için bir ziyaretçi analitik danışmanısın.

GÖREVİN
Portföy ziyaretçilerinin sohbet kayıtlarını analiz ederek site sahibine (Harun) somut,
stratejik içgörüler sunmak. Yüzeysel özetler değil — "neden olduğunu" ve "ne yapmalı"yı
açıkla.

ZİYARETÇİ NİYET KATEGORİLERİ — her analizde bu sınıflandırmayı kullan:
  • teknik sorular       → mimari, implementasyon, sistem tasarımı, kod kalitesi
  • kariyer / işe alım   → iş teklifi, pozisyon uygunluğu, profesyonel background
  • proje soruları       → belirli projeler, teknik detaylar, proje sonuçları
  • kişisel sorular      → kim olduğu, öğrenme yolculuğu, genel background
  • çalışma / iş birliği → freelance, proje ortaklığı, danışmanlık teklifi
  • AI / tech stack      → araç tercihleri, framework seçimleri, opinionlar

ANALİZ STANDARTLARI
  • İçgörüsel cümleler kur  → "Ziyaretçiler ağırlıklı olarak backend mimarini merak ediyor."
  • Pattern vurgula         → "İşe alım soruları genellikle tech stack sorusuyla başlıyor."
  • Sıklık / oran belirt    → "Kayıtların ~%60'ı teknik sorularla açılıyor."
  • Recruiter-grade dil     → "ziyaretçiler teknik derinliğe önem veriyor" tarzında konuş.
  • Proje bazlı karşılaştır → "CebirX diğer projelere kıyasla 3x daha fazla teknik soru çekiyor."
  • Türkçe yanıt ver; teknik terimleri İngilizce bırakabilirsin.

YANIT FORMATI
  • Odaklı ve kısa: 3-6 cümle veya madde listesi.
  • Önemli bulguları **kalın** yaz.
  • Analitik tonun dışına çıkma. "Yardımcı olmak istiyorum" gibi ifade kullanma.

{log_section}
"""

def _build_analytics_log_section(chat_logs: list[dict]) -> str:
    """
    Format chat log payload into a readable context block for the system prompt.
    Keeps the context concise to avoid exceeding token limits.
    """
    if not chat_logs:
        return "SOHBET KAYIT VERİSİ: Henüz kayıt yok."

    lines = [f"SOHBET KAYIT VERİSİ ({len(chat_logs)} kayıt analiz için hazır):"]
    for i, log in enumerate(chat_logs, 1):
        lines.append(f"\n[Kayıt {i}] — {log.get('timestamp', 'tarih yok')} | {log.get('message_count', 0)} mesaj")
        for j, q in enumerate(log.get("user_samples", []), 1):
            lines.append(f"  Kullanıcı {j}: {q}")
        for j, a in enumerate(log.get("assistant_samples", []), 1):
            lines.append(f"  Asistan {j}: {a}")
    return "\n".join(lines)


async def stream_chat(messages: list[dict]):
    # Her sohbette context'i taze oluştur
    context = build_context()
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(context=context)

    print(f"[GROQ] Context built: {len(context)} chars", file=sys.stderr)

    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        stream=True,
        max_tokens=1024,
        temperature=0.2,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def complete_chat(messages: list[dict]) -> str:
    context = build_context()
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(context=context)

    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        stream=False,
        max_tokens=1024,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


async def summarize_chat_logs(chat_logs: list[dict]) -> dict:
    """
    Produce a rich analytics summary for the admin dashboard card.

    Returns a dict with keys:
      summary            – 2-3 sentence executive summary (Turkish)
      top_topics         – list of 3 short topic labels
      dominant_intent    – single label for the primary visitor intent
      top_project        – name of the most-discussed project (or "")
      visitor_expectation – one sentence on what visitors want from Harun
    """
    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

    prompt = f"""Aşağıdaki portfolyo sohbet kayıtlarını analitik bir dashboard özeti için analiz et.
SADECE geçerli JSON döndür, başka hiçbir şey yazma.

Şu formata kesinlikle uy:
{{
  "summary": "2-3 cümle executive summary — öne çıkan pattern ve insight, Türkçe",
  "top_topics": ["kısa etiket 1", "kısa etiket 2", "kısa etiket 3"],
  "dominant_intent": "en baskın ziyaretçi niyeti (ör: teknik merak / işe alım / proje sorgusu)",
  "top_project": "en çok konuşulan proje adı ya da boş string",
  "visitor_expectation": "ziyaretçilerin Harun'dan tek cümleyle ne beklediği"
}}

Kayıtlar:
{json.dumps(chat_logs, ensure_ascii=False, indent=2)}"""

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Sen bir portfolio analytics danışmanısın. "
                    "Ziyaretçi sohbet kayıtlarını analiz ederek stratejik içgörüler üretirsin. "
                    "Sadece istenen JSON formatında yanıt ver."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        stream=False,
        max_tokens=600,
        temperature=0.2,
    )

    content = response.choices[0].message.content or ""
    cleaned = re.sub(r"```json|```", "", content).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as exc:
        print(
            f"[GROQ] summarize_chat_logs: JSON parse failed ({exc}). "
            f"Raw response (first 200 chars): {content[:200]!r}",
            file=sys.stderr,
        )
        return {}


async def answer_admin_chat_about_logs(
    messages: list[dict],
    chat_logs: list[dict],
) -> str:
    """
    Answer an admin question about visitor chat logs.

    Key design:
    • Log data is embedded in the SYSTEM prompt so it persists across all turns.
    • `messages` is the full conversation history (role: user/assistant) and is
      passed directly as the LLM message list — this gives proper multi-turn memory.
    • The model acts as an analytics consultant, not a generic assistant.
    """
    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

    log_section = _build_analytics_log_section(chat_logs)
    system_content = _ADMIN_ANALYTICS_PROMPT.format(log_section=log_section)

    # Build the full message list:  system  +  full conversation history
    llm_messages: list[dict] = [{"role": "system", "content": system_content}]
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            llm_messages.append({"role": role, "content": content})

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=llm_messages,
        stream=False,
        max_tokens=800,
        temperature=0.3,
    )

    return (response.choices[0].message.content or "").strip()
