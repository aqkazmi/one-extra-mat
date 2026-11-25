# One Extra Mat

Weekly Jummah reminder: one approved Qur'an verse or hadith per week, rendered as a feed post (4:5), story (9:16) and a 12-second Reel (9:16 MP4).

- `content_bank.json` — the **only** source of religious content. Every entry was reviewed and approved before it was added. Nothing is generated on the fly.
- `template.html` — brand template (feed, story, avatar, cover) and the Reel animation.
- `render.py` — renders assets with Playwright + FFmpeg.

```
pip install playwright && playwright install chromium   # FFmpeg also required
python3 render.py stills samples/week01.json out
python3 render.py reel   samples/week01.json out 12
python3 render.py brand  out
```

Fonts: Noto Naskh Arabic, Inter, Playfair Display — SIL Open Font License 1.1.
