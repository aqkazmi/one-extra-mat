"""Render One Extra Mat assets from a content entry.

usage:
  python3 render.py stills <entry.json> <outdir>        -> feed.png, story.png
  python3 render.py brand <outdir>                       -> avatar.png, cover.png
  python3 render.py reel <entry.json> <outdir> [secs]    -> reel.mp4
"""
import json, sys, subprocess, pathlib, time
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
TPL = (HERE / "template.html").as_uri()
SIZES = {"feed": (1080, 1350), "story": (1080, 1920), "avatar": (1080, 1080), "cover": (1640, 624)}


def page_for(p, fmt, entry):
    w, h = SIZES[fmt]
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    pg.goto(TPL)
    pg.evaluate("document.fonts.ready")
    pg.evaluate("([f,e]) => build(f,e)", [fmt, entry or {}])
    pg.evaluate("document.fonts.ready.then(()=>{ if(document.getElementById('hero')) fit(); })")
    pg.wait_for_timeout(150)
    return b, pg


def shot(p, fmt, entry, out):
    b, pg = page_for(p, fmt, entry)
    if fmt == "avatar":  # circular crop preview isn't needed; platforms crop themselves
        pass
    pg.locator("#c").screenshot(path=str(out))
    scale = pg.evaluate("window.FIT_SCALE || 1")
    b.close()
    return scale


def reel(p, entry, out, secs=12.0, fps=30):
    b, pg = page_for(p, "story", entry)
    w, h = SIZES["story"]
    n = int(secs * fps)
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k",
        "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    el = pg.locator("#c")
    for i in range(n):
        pg.evaluate(f"render({i / fps})")
        ff.stdin.write(el.screenshot(type="jpeg", quality=95))
    ff.stdin.close(); ff.wait()
    b.close()


if __name__ == "__main__":
    mode = sys.argv[1]
    with sync_playwright() as p:
        if mode == "brand":
            out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
            shot(p, "avatar", {}, out / "avatar.png"); shot(p, "cover", {}, out / "cover.png")
        else:
            entry = json.loads(pathlib.Path(sys.argv[2]).read_text())
            out = pathlib.Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
            if mode == "stills":
                for f in ("feed", "story"):
                    s = shot(p, f, entry, out / f"{f}.png"); print(f, "fit scale", round(s, 2))
            elif mode == "reel":
                t = time.time(); reel(p, entry, out / "reel.mp4", float(sys.argv[4]) if len(sys.argv) > 4 else 12.0)
                print("reel rendered in", round(time.time() - t, 1), "s")
