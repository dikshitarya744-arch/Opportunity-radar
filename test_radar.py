"""Self-checks for Opportunity Radar. Run: python test_radar.py"""
import contextlib, io, logging, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import requests, radar

fails = 0
def check(name, fn):
    global fails
    try: ok = bool(fn())
    except Exception as e: ok = False; name += f" [{type(e).__name__}]"
    fails += not ok; print(("PASS  " if ok else "FAIL  ") + name)

def item(i=0): return dict(source="T", title=f"python hackathon {i}", url=f"https://x.test/{i}", desc="prize $500", score=50)
def fresh(): os.chdir(tempfile.mkdtemp()); return radar.open_db()
for k in ("ANTHROPIC_API_KEY", "TELEGRAM_TOKEN", "DISCORD_WEBHOOK", "GITHUB_TOKEN"): os.environ.pop(k, None)
cfg = {"skills": ["python", "c++"], "interests": ["ai"], "min_score": 10, "max_alerts_per_scan": 10, "interval_minutes": 60}
real_notify = radar.notify

check("skills with symbols (c++) match", lambda: radar.has("c++", "i know c++ well"))
def bom_env():
    fresh(); open(".env", "w", encoding="utf-8-sig").write("BOM_TEST=ok\n"); radar.load_env(); return os.environ.get("BOM_TEST") == "ok"
check(".env saved with BOM (Windows Notepad) is read", bom_env)
def emoji():
    code = f"import sys;sys.path.insert(0,{HERE!r});import radar;radar.notify({item()!r})"
    return subprocess.run([sys.executable, "-c", code], env={**os.environ, "PYTHONIOENCODING": "cp1252"}, capture_output=True).returncode == 0
check("alerts with emoji don't crash on Windows consoles", emoji)
def leak():
    os.environ.update(TELEGRAM_TOKEN="123456:SECRETTOKEN", TELEGRAM_CHAT_ID="1")
    buf = io.StringIO(); h = logging.StreamHandler(buf); radar.log.addHandler(h); real = requests.post
    def boom(url, **kw): raise requests.ConnectionError(f"Max retries exceeded with url: {url}")
    requests.post = boom
    with contextlib.redirect_stdout(io.StringIO()): radar.notify(item())
    requests.post = real; radar.log.removeHandler(h); os.environ.pop("TELEGRAM_TOKEN"); return "SECRETTOKEN" not in buf.getvalue()
check("bot token never appears in logs", leak)

radar.notify = lambda it: True
def partial():
    db = fresh()
    def flaky(c): yield item(1); raise RuntimeError("rate limited")
    radar.SOURCES = [flaky]; radar.scan(dict(cfg), db); return db.execute("select count(*) from seen").fetchone()[0] == 1
check("items found before a source error are kept", partial)
def strscore():
    db = fresh(); os.environ["ANTHROPIC_API_KEY"] = "test"; old = radar.llm_score
    radar.llm_score = lambda it, c: {"score": "85", "is_real_opportunity": True}
    radar.SOURCES = [lambda c: iter([item(1)])]
    try: radar.scan(dict(cfg), db); return True
    finally: radar.llm_score = old; os.environ.pop("ANTHROPIC_API_KEY")
check("AI returning score as text doesn't crash the scan", strscore)
def cap():
    db = fresh(); n = []; radar.notify = lambda it: (n.append(1) or True)
    radar.SOURCES = [lambda c: iter([item(i) for i in range(15)])]; radar.scan(dict(cfg), db)
    radar.SOURCES = [lambda c: iter([])]; radar.scan(dict(cfg), db); return len(n) == 15
check("matches beyond the per-scan alert cap are sent later, not lost", cap)
def retry():
    db = fresh(); n = []; radar.notify = lambda it: (n.append(1) or len(n) > 1)
    radar.SOURCES = [lambda c: iter([item(1)])]; radar.scan(dict(cfg), db)
    radar.SOURCES = [lambda c: iter([])]; radar.scan(dict(cfg), db); return len(n) == 2
check("failed alert is retried next scan", retry)
def conf():
    fresh(); open("config.json", "w", encoding="utf-8-sig").write('{"skills":"python, c++","interests":["ai"],"interval_minutes":1}')
    c = radar.load_config("config.json"); return c["skills"] == ["python", "c++"] and c["interval_minutes"] >= 10
check("config: BOM ok, 'skills' as text fixed, interval floor", conf)
radar.notify = real_notify

pat = re.compile(r"sk-ant-[\w-]{10,}|ghp_\w{20,}|\d{8,}:[\w-]{30,}|discord(?:app)?\.com/api/webhooks/\d+/\S+")
files = [f for f in os.listdir(HERE) if os.path.isfile(os.path.join(HERE, f))]
check("no API keys inside any shipped file", lambda: not any(pat.search(open(os.path.join(HERE, f), errors="ignore").read()) for f in files))
check("no .env shipped, and .env is git-ignored", lambda: ".env" not in files and ".env" in open(os.path.join(HERE, ".gitignore")).read().split())
print(f"\n{fails} check(s) failed"); sys.exit(1 if fails else 0)
