import os
import threading
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from instagrapi import Client
import json

app = Flask(__name__)

BOT_THREAD = None
STOP_EVENT = threading.Event()
LOGS = []
SESSION_FILE = "session.json"


def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    LOGS.append(full_msg)
    print(full_msg)


def run_bot(username, password, welcome_messages, group_ids, delay, poll_interval, custom_name, client=None):
    cl = client or Client()

    log("Bot started — Running in 24×7 spam mode...")
    message_count = 0

    while not STOP_EVENT.is_set():
        try:
            for gid in group_ids:
                if STOP_EVENT.is_set():
                    break

                for msg in welcome_messages:
                    if STOP_EVENT.is_set():
                        break

                    final_msg = f"{custom_name} {msg}".strip() if custom_name else msg

                    try:
                        cl.direct_send(final_msg, thread_ids=[gid])
                        message_count += 1
                        log(f"[{message_count}] Sent to {gid}: {final_msg}")

                        for _ in range(delay):
                            if STOP_EVENT.is_set():
                                break
                            time.sleep(1)

                    except Exception as e:
                        log(f"Error sending to {gid}: {e}")

            if STOP_EVENT.is_set():
                break

            log(f"Cycle finished. Waiting {poll_interval}s before next round...")
            for _ in range(poll_interval):
                if STOP_EVENT.is_set():
                    break
                time.sleep(1)

        except Exception as e:
            log(f"Main loop error: {e}")
            time.sleep(10)

    log(f"Bot stopped. Total messages sent: {message_count}")


@app.route("/")
def index():
    return render_template_string(PAGE_HTML)


@app.route("/start", methods=["POST"])
def start_bot():
    global BOT_THREAD

    if BOT_THREAD and BOT_THREAD.is_alive():
        return jsonify({"message": "Bot is already running!"})

    session_input = request.form.get("sessionid", "").strip()

    welcome = request.form.get("welcome", "").splitlines()
    welcome = [m.strip() for m in welcome if m.strip()]

    group_ids = [g.strip() for g in request.form.get("group_ids", "").split(",") if g.strip()]
    delay = int(request.form.get("delay", 5))
    poll = int(request.form.get("poll", 30))
    custom_name = request.form.get("custom_name", "").strip()

    if not welcome == [] or group_ids == []:
        return jsonify({"message": "Please enter messages and at least one Group ID"})

    cl = Client()

    # Try pasted session string first
    if session_input:
        try:
            settings = json.loads(session_input)
            cl.set_settings(settings)
            log("Session loaded from pasted string")
        except:
            return jsonify({"message": "Invalid session string! Copy exactly from cl.get_settings()"})
    # Fallback: load from session.json
    elif os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            log("Session loaded from session.json file")
        except:
            return jsonify({"message": "session.json is corrupted. Delete it and paste fresh session string."})
    else:
        return jsonify({"message": "No session found! Paste your session string below."})

    # Verify session works
    try:
        user = cl.account_info()
        log(f"Logged in as: @{user.username} ({user.full_name})")
    except Exception as e:
        log(f"Session invalid or expired: {e}")
        return jsonify({"message": "Session is dead or blocked. Get a new one."})

    STOP_EVENT.clear()
    BOT_THREAD = threading.Thread(
        target=run_bot,
        args=(None, None, welcome, group_ids, delay, poll, custom_name, cl),
        daemon=True
    )
    BOT_THREAD.start()

    return jsonify({"message": f"24×7 SPAM BOT STARTED as @{user.username}! Spamming {len(group_ids)} groups non-stop"})


@app.route("/stop", methods=["POST"])
def stop_bot():
    STOP_EVENT.set()
    log("Stop signal sent...")
    return jsonify({"message": "Bot stopping..."})


@app.route("/logs")
def get_logs():
    return jsonify({"logs": LOGS[-200:]})


PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>INSTA 24x7 SPAM BOT – SESSION ID ONLY</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Poppins',sans-serif; background:radial-gradient(circle at top left,#0f00ff,#8a2be2,#00ffff); color:#fff; min-height:100vh; padding:20px; display:flex; justify-content:center; align-items:center; }
.container { max-width:1200px; width:100%; background:rgba(0,0,0,0.4); backdrop-filter:blur(15px); border-radius:30px; padding:50px; box-shadow:0 0 60px rgba(138,43,226,0.6); }
h1 { text-align:center; font-size:42px; background:-webkit-linear-gradient(#ff00ff,#00ffff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:40px; }
.input-group { margin-bottom:25px; }
label { display:block; margin-bottom:10px; color:#ff00ff; font-weight:600; }
textarea, input { width:100%; padding:18px; background:rgba(255,255,255,0.1); border:2px solid #ff00ff; border-radius:15px; color:#fff; font-family:monospace; }
textarea { min-height:180px; resize:vertical; }
button { padding:18px 40px; margin:10px; border:none; border-radius:15px; font-size:18px; font-weight:700; cursor:pointer; color:white; }
.start { background:linear-gradient(135deg,#ff00ff,#8a2be2); }
.stop { background:linear-gradient(135deg,#ff0066,#ff3300); }
.log-box { background:rgba(0,0,0,0.6); padding:25px; border-radius:20px; height:380px; overflow-y:auto; margin-top:40px; font-family:monospace; border:2px solid #ff00ff; }
button:hover { transform:scale(1.05); }
</style></head>
<body>
<div class="container">
  <h1>INSTA 24×7 SPAMMER<br><small style="font-size:18px;color:#0ff;">Session ID Login Only</small></h1>

  <form id="f">
    <div class="input-group">
      <label>Session ID (Paste full cl.get_settings() output)</label>
      <textarea name="sessionid" placeholder="Paste the HUGE JSON string here after running cl.get_settings() once..."></textarea>
      <small style="color:#ffff00;">Leave empty if session.json exists in folder</small>
    </div>

    <div class="input-group">
      <label>Spam Messages (one per line – sent 24×7)</label>
      <textarea name="welcome" placeholder="Line 1&#10;Line 2&#10;Line 3"></textarea>
    </div>

    <div class="input-group">
      <label>Custom Name / @Username (optional)</label>
      <input type="text" name="custom_name" placeholder="@promo_king or Rahul Sharma">
    </div>

    <div class="input-group">
      <label>Group Chat IDs (comma separated)</label>
      <input type="text" name="group_ids" placeholder="123456789, 987654321">
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
      <div class="input-group">
        <label>Delay Between Messages (sec)</label>
        <input type="number" name="delay" value="5" min="1">
      </div>
      <div class="input-group">
        <label>Delay Between Cycles (sec)</label>
        <input type="number" name="poll" value="30" min="5">
      </div>
    </div>

    <div style="text-align:center;margin:40px 0;">
      <button type="button" class="start" onclick="startBot()">START 24×7 SPAM</button>
      <button type="button" class="stop" onclick="stopBot()">STOP BOT</button>
    </div>

    <div class="log-box" id="logs">Bot logs will appear here in real-time...</div>
  </form>
</div>

<script>
async function startBot() {
  let f = new FormData(document.getElementById('f'));
  let r = await fetch('/start', {method:'POST', body:f});
  let j = await r.json();
  alert(j.message);
}
async function stopBot() {
  {
  await fetch('/stop', {method:'POST'});
  alert("Stop command sent!");
}
async function upd() {
  let r = await fetch('/logs');
  let j = await r.json();
  let box = document.getElementById('logs');
  box.innerHTML = j.logs.length ? j.logs.join('<br>') : "Waiting for activity...";
  box.scrollTop = box.scrollHeight;
}
setInterval(upd, 2000);
upd();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
