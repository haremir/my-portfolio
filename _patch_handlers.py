"""Handlers.py - API client entegrasyonu icin toplu degisiklik."""
import sys
from pathlib import Path

p = Path(r"C:\Users\PC\Desktop\my-portfolio\harun_site\telegram_bot\handlers.py")
src = p.read_text(encoding="utf-8")

# 1. _build_log_payload body: import + 2 calls
old1 = '    from harun_site.utils.data_manager import load_chat_log_messages, load_chat_logs\n\n    logs = load_chat_logs()\n    payload = []\n    for log in logs[:max_logs]:\n        messages = load_chat_log_messages(log["filename"])'
new1 = '    from harun_site.telegram_bot.api_client import api_client\n\n    logs = await api_client.get_chat_logs()\n    payload = []\n    for log in logs[:max_logs]:\n        messages = await api_client.get_chat_log_messages(log["filename"])'
assert old1 in src, "[1] _build_log_payload body not found"
src = src.replace(old1, new1, 1)
print("[1] _build_log_payload body -> API client")

# 2. _run_analytics_query: add await
old2 = '    payload = _build_log_payload()'
new2 = '    payload = await _build_log_payload()'
assert old2 in src, "[2] _build_log_payload() call not found"
src = src.replace(old2, new2, 1)
print("[2] _run_analytics_query -> await _build_log_payload()")

# 3. cmd_stats: replace full try block with API client version
old3_lines = [
    '    try:',
    '        from harun_site.utils.data_manager import load_chat_logs',
    '        from harun_site.telegram_bot.notifier import load_watchlist',
    '        logs = load_chat_logs()',
    '        today_str = _now().date().isoformat()',
    '        today_logs = [l for l in logs if (l.get("timestamp") or "").startswith(today_str)]',
    '        total_msgs  = sum(l.get("user_message_count", l.get("message_count", 0) // 2) for l in logs)',
    '        today_msgs  = sum(l.get("user_message_count", l.get("message_count", 0) // 2) for l in today_logs)',
    '        watchlist   = load_watchlist()',
    '        await _reply_plain(',
    '            update,',
    '            f"\U0001f4c8 <b>İstatistikler</b>\\n\\n"',
    '            f"\U0001f4c1 Toplam kayıt: <b>{len(logs)}</b>\\n"',
    '            f"\U0001f4ac Toplam kullanıcı mesajı: <b>{total_msgs}</b>\\n"',
    '            f"\U0001f465 Bugünkü oturum: <b>{len(today_logs)}</b>\\n"',
    '            f"\U0001f4e9 Bugünkü kullanıcı mesajı: <b>{today_msgs}</b>\\n"',
    '            f"\U0001f440 Watchlist: {chr(44).join(watchlist) if watchlist else chr(8212)}",',
    '        )',
]
old3 = "\n".join(old3_lines)
assert old3 in src, f"[3] cmd_stats try block not found\nLooking for:\n{old3[:200]}"

new3_lines = [
    '    try:',
    '        from harun_site.telegram_bot.api_client import api_client',
    '        from harun_site.telegram_bot.notifier import load_watchlist',
    '        stats = await api_client.get_stats()',
    '        watchlist = load_watchlist()',
    '        if stats:',
    '            await _reply_plain(',
    '                update,',
    '                f"\U0001f4c8 <b>İstatistikler</b>\\n\\n"',
    '                f"\U0001f4c1 Toplam kayıt: <b>{stats.get(chr(39)+chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(115)+chr(101)+chr(115)+chr(115)+chr(105)+chr(111)+chr(110)+chr(115)+chr(39), 0)}</b>\\n"',
    '                f"\U0001f4ac Toplam kullanıcı mesajı: <b>{stats.get(chr(39)+chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(117)+chr(115)+chr(101)+chr(114)+chr(95)+chr(109)+chr(101)+chr(115)+chr(115)+chr(97)+chr(103)+chr(101)+chr(115)+chr(39), 0)}</b>\\n"',
    '                f"\U0001f465 Bugünkü oturum: <b>{stats.get(chr(39)+chr(116)+chr(111)+chr(100)+chr(97)+chr(121)+chr(95)+chr(115)+chr(101)+chr(115)+chr(115)+chr(105)+chr(111)+chr(110)+chr(115)+chr(39), 0)}</b>\\n"',
    '                f"\U0001f4e9 Bugünkü kullanıcı mesajı: <b>{stats.get(chr(39)+chr(116)+chr(111)+chr(100)+chr(97)+chr(121)+chr(95)+chr(117)+chr(115)+chr(101)+chr(114)+chr(95)+chr(109)+chr(101)+chr(115)+chr(115)+chr(97)+chr(103)+chr(101)+chr(115)+chr(39), 0)}</b>\\n"',
    '                f"\U0001f440 Watchlist: {chr(44).join(watchlist) if watchlist else chr(8212)}",',
    '            )',
    '        else:',
    '            await _reply_plain(update, "⚠️ İstatistikler alınamadı — API yanıtı boş.")',
]
new3 = "\n".join(new3_lines)
src = src.replace(old3, new3, 1)
print("[3] cmd_stats -> API client")

p.write_text(src, encoding="utf-8")
print("\nAll patches applied and saved to:", p)
