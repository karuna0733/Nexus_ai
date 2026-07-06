"""
NexusAI — main.py
Single-file FastAPI app. HTML is embedded directly → no templates folder → no 404 ever.
Run: python main.py
"""

import os, sys, uuid, json, base64
import httpx, aiofiles
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Resolve database module imports relative to the app folder on Vercel
sys.path.append(str(Path(__file__).parent))
import database

load_dotenv()
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL",   "llama-3.1-8b-instant")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL",   "gemini-2.5-flash")


UPLOAD_DIR = Path("/tmp/uploads") if os.getenv("VERCEL") else Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

TEXT_EXT = {".txt",".py",".js",".ts",".html",".css",".md",".json",".csv",".xml",".sh",".c",".cpp",".java",".go",".rs"}
IMG_EXT  = {".jpg",".jpeg",".png",".gif",".webp",".bmp"}

SYSTEM_PROMPT = (
    "You are Nexus AI, an advanced AI assistant built by Nexus AI. "
    "You are helpful, creative, and precise. "
    "Always format code with proper markdown code blocks with language tags. "
    "Be concise yet thorough. Use bullet points and headers for complex answers."
)

app = FastAPI(title="Nexus AI")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
database.init_db()


# ── Auth helper ───────────────────────────────────────────────────────────────
def cur_user(request: Request):
    t = request.cookies.get("nx_tok")
    return database.get_session_user(t) if t else None


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  LOGIN PAGE HTML
# ╚══════════════════════════════════════════════════════════════════════════════
LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Nexus AI — Sign In</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --p:#8b5cf6;--c:#06b6d4;--bg:#030308;
  --card:rgba(8,8,20,0.88);--border:rgba(139,92,246,0.25);
  --text:#e2e8f0;--dim:#64748b;--err:#f43f5e;
}
body{
  font-family:'Segoe UI',system-ui,sans-serif;
  background:var(--bg);color:var(--text);
  min-height:100vh;display:flex;align-items:center;justify-content:center;
  overflow:hidden;
}
#bg{position:fixed;inset:0;z-index:0;}

/* Aurora layers */
.aur{position:fixed;border-radius:50%;filter:blur(100px);pointer-events:none;z-index:1;animation:aur 12s ease-in-out infinite alternate;}
.aur1{width:600px;height:600px;background:radial-gradient(circle,rgba(139,92,246,0.18),transparent 70%);top:-200px;left:-150px;animation-delay:0s;}
.aur2{width:500px;height:500px;background:radial-gradient(circle,rgba(6,182,212,0.14),transparent 70%);bottom:-150px;right:-100px;animation-delay:4s;}
.aur3{width:300px;height:300px;background:radial-gradient(circle,rgba(168,85,247,0.12),transparent 70%);top:40%;left:50%;animation-delay:8s;}
@keyframes aur{0%{transform:translate(0,0) scale(1);}100%{transform:translate(40px,-40px) scale(1.15);}}

/* Card */
.card{
  position:relative;z-index:10;
  background:var(--card);
  border:1px solid var(--border);
  border-radius:22px;padding:40px 36px 36px;
  width:420px;max-width:95vw;
  backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);
  box-shadow:0 8px 64px rgba(0,0,0,0.7),0 0 0 1px rgba(139,92,246,0.12),inset 0 1px 0 rgba(255,255,255,0.05);
}

/* Logo */
.logo-row{display:flex;align-items:center;gap:14px;justify-content:center;margin-bottom:32px;}
.hex-wrap{position:relative;width:52px;height:52px;display:flex;align-items:center;justify-content:center;}
.hex-wrap svg{position:absolute;}
.hex-spin{animation:hexspin 8s linear infinite;}
.hex-pulse{animation:hexpulse 2.5s ease-in-out infinite;}
@keyframes hexspin{to{transform:rotate(360deg);}}
@keyframes hexpulse{0%,100%{opacity:.6;transform:scale(1);}50%{opacity:1;transform:scale(1.08);}}
.logo-txt h1{font-size:24px;font-weight:900;letter-spacing:-0.5px;}
.logo-txt h1 em{font-style:normal;background:linear-gradient(135deg,var(--p),var(--c));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.logo-txt p{font-size:12px;color:var(--dim);margin-top:2px;}

/* Tabs */
.tabs{display:flex;background:rgba(255,255,255,0.04);border-radius:12px;padding:4px;margin-bottom:26px;}
.tab{flex:1;text-align:center;padding:9px 0;border-radius:9px;cursor:pointer;font-size:13.5px;font-weight:600;color:var(--dim);border:none;background:none;transition:all .25s;}
.tab.on{background:linear-gradient(135deg,var(--p),#7c3aed);color:#fff;box-shadow:0 2px 14px rgba(139,92,246,.35);}

/* Alert */
.alert{padding:10px 14px;border-radius:9px;font-size:13px;margin-bottom:16px;display:none;}
.alert.err{background:rgba(244,63,94,.1);border:1px solid rgba(244,63,94,.3);color:#fda4af;display:block;}
.alert.ok {background:rgba(6,182,212,.1);border:1px solid rgba(6,182,212,.3);color:#67e8f9;display:block;}

/* Fields */
.field{margin-bottom:15px;}
.field label{display:block;font-size:12px;font-weight:600;color:var(--dim);margin-bottom:6px;letter-spacing:.04em;text-transform:uppercase;}
.field input{
  width:100%;padding:12px 15px;
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:10px;color:var(--text);font-size:14px;outline:none;
  transition:border-color .2s,box-shadow .2s;
}
.field input:focus{border-color:var(--p);box-shadow:0 0 0 3px rgba(139,92,246,.15);}
.field input::placeholder{color:#374151;}

/* Button */
.btn{
  width:100%;padding:13px;margin-top:4px;
  background:linear-gradient(135deg,var(--p),#7c3aed);
  color:#fff;border:none;border-radius:11px;font-size:15px;font-weight:700;cursor:pointer;
  transition:all .2s;box-shadow:0 4px 20px rgba(139,92,246,.35);
  position:relative;overflow:hidden;
}
.btn::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(255,255,255,.12),transparent);
  opacity:0;transition:opacity .2s;
}
.btn:hover::before{opacity:1;}
.btn:hover{transform:translateY(-1px);box-shadow:0 8px 28px rgba(139,92,246,.45);}
.btn:active{transform:translateY(0);}
.btn:disabled{opacity:.55;cursor:not-allowed;transform:none;}
.spin{display:none;width:18px;height:18px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:sp 0.7s linear infinite;margin:0 auto;}
@keyframes sp{to{transform:rotate(360deg)}}

.note{text-align:center;font-size:12px;color:var(--dim);margin-top:22px;}
.note a{color:var(--c);text-decoration:none;}
#p-reg{display:none;}
</style>
</head>
<body>
<canvas id="bg"></canvas>
<div class="aur aur1"></div>
<div class="aur aur2"></div>
<div class="aur aur3"></div>

<div class="card">
  <!-- Logo -->
  <div class="logo-row">
    <div class="hex-wrap">
      <!-- Outer spinning ring -->
      <svg class="hex-spin" width="52" height="52" viewBox="0 0 52 52">
        <defs><linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#8b5cf6"/><stop offset="100%" stop-color="#06b6d4"/></linearGradient></defs>
        <polygon points="26,2 48,14 48,38 26,50 4,38 4,14" fill="none" stroke="url(#g1)" stroke-width="1.5" stroke-dasharray="4 2"/>
      </svg>
      <!-- Inner pulsing icon -->
      <svg class="hex-pulse" width="34" height="34" viewBox="0 0 34 34">
        <defs><linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#8b5cf6"/><stop offset="100%" stop-color="#06b6d4"/></linearGradient></defs>
        <polygon points="17,2 30,9.5 30,24.5 17,32 4,24.5 4,9.5" fill="url(#g2)" opacity=".15"/>
        <polygon points="17,2 30,9.5 30,24.5 17,32 4,24.5 4,9.5" fill="none" stroke="url(#g2)" stroke-width="1.5"/>
        <circle cx="17" cy="17" r="5" fill="url(#g2)"/>
        <line x1="17" y1="2"  x2="17" y2="12" stroke="url(#g2)" stroke-width="0.8" opacity=".5"/>
        <line x1="17" y1="22" x2="17" y2="32" stroke="url(#g2)" stroke-width="0.8" opacity=".5"/>
        <line x1="4"  y1="9.5"  x2="12" y2="14" stroke="url(#g2)" stroke-width="0.8" opacity=".5"/>
        <line x1="30" y1="9.5"  x2="22" y2="14" stroke="url(#g2)" stroke-width="0.8" opacity=".5"/>
        <line x1="4"  y1="24.5" x2="12" y2="20" stroke="url(#g2)" stroke-width="0.8" opacity=".5"/>
        <line x1="30" y1="24.5" x2="22" y2="20" stroke="url(#g2)" stroke-width="0.8" opacity=".5"/>
      </svg>
    </div>
    <div class="logo-txt">
      <h1>Nexus <em>AI</em></h1>
      <p>Intelligent AI Companion</p>
    </div>
  </div>

  <!-- Tabs -->
  <div class="tabs">
    <button class="tab on" onclick="swTab('login',this)">Sign In</button>
    <button class="tab"    onclick="swTab('reg',this)">Create Account</button>
  </div>

  <div class="alert" id="alert"></div>

  <!-- Login -->
  <form id="p-login" onsubmit="event.preventDefault(); doLogin();">
    <div class="field"><label>Email</label><input type="email" id="le" name="email" placeholder="you@example.com" autocomplete="username email" required/></div>
    <div class="field"><label>Password</label><input type="password" id="lp" name="password" placeholder="••••••••" autocomplete="current-password" required/></div>
    <button type="submit" class="btn" id="lb"><div class="spin" id="ls"></div><span id="lt">Sign In →</span></button>
  </form>

  <!-- Register -->
  <form id="p-reg" onsubmit="event.preventDefault(); doReg();" style="display:none;">
    <div class="field"><label>Username</label><input type="text" id="rn" name="username" placeholder="YourName" autocomplete="username" required/></div>
    <div class="field"><label>Email</label><input type="email" id="re" name="email" placeholder="you@example.com" autocomplete="email" required/></div>
    <div class="field"><label>Password</label><input type="password" id="rp" name="password" placeholder="Min 6 characters" autocomplete="new-password" required/></div>
    <button type="submit" class="btn" id="rb"><div class="spin" id="rs"></div><span id="rt">Create Account →</span></button>
  </form>

  <div class="note">By continuing you agree to our <a href="#">Terms</a> &amp; <a href="#">Privacy</a></div>
</div>

<!-- Three.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(()=>{
  const cv=document.getElementById('bg');
  const re=new THREE.WebGLRenderer({canvas:cv,alpha:true,antialias:true});
  re.setPixelRatio(Math.min(devicePixelRatio,2));
  re.setSize(innerWidth,innerHeight);
  const sc=new THREE.Scene(), cam=new THREE.PerspectiveCamera(65,innerWidth/innerHeight,.1,1000);
  cam.position.z=22;

  /* Stars */
  const sv=[]; for(let i=0;i<1200;i++) sv.push((Math.random()-.5)*120,(Math.random()-.5)*120,(Math.random()-.5)*120);
  const sg=new THREE.BufferGeometry(); sg.setAttribute('position',new THREE.Float32BufferAttribute(sv,3));
  sc.add(new THREE.Points(sg,new THREE.PointsMaterial({color:0xffffff,size:.06,transparent:true,opacity:.55})));

  /* Floating hexagonal prisms */
  const hexes=[]; const COLS=[0x8b5cf6,0x06b6d4,0xa855f7,0x0891b2];
  for(let i=0;i<18;i++){
    const r=.4+Math.random()*1.6, h=.08+Math.random()*.25;
    const geo=new THREE.CylinderGeometry(r,r,h,6);
    const eg=new THREE.EdgesGeometry(geo);
    const col=COLS[Math.floor(Math.random()*COLS.length)];
    const mat=new THREE.LineBasicMaterial({color:col,transparent:true,opacity:.25+Math.random()*.35});
    const mesh=new THREE.LineSegments(eg,mat);
    mesh.position.set((Math.random()-.5)*32,(Math.random()-.5)*22,(Math.random()-.5)*12-4);
    mesh.rotation.set(Math.random()*Math.PI,Math.random()*Math.PI,Math.random()*Math.PI);
    mesh.userData={rx:(Math.random()-.5)*.006,ry:(Math.random()-.5)*.009,vy:(Math.random()-.5)*.012};
    sc.add(mesh); hexes.push(mesh);
  }

  /* Glowing orbs */
  [[0x8b5cf6,4,-6,-8],[0x06b6d4,3,5,-6],[0xa855f7,2,-2,3]].forEach(([col,r,x,y])=>{
    const m=new THREE.Mesh(new THREE.SphereGeometry(r,16,16),
      new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:.06}));
    m.position.set(x,y,-10); sc.add(m);
  });

  let mx=0,my=0;
  document.addEventListener('mousemove',e=>{mx=(e.clientX/innerWidth-.5)*2;my=(e.clientY/innerHeight-.5)*2;});

  let t=0;
  (function anim(){
    requestAnimationFrame(anim); t+=.008;
    cam.position.x+=(mx*2-cam.position.x)*.02;
    cam.position.y+=(-my*1.5-cam.position.y)*.02;
    cam.lookAt(sc.position);
    hexes.forEach(h=>{
      h.rotation.x+=h.userData.rx; h.rotation.y+=h.userData.ry;
      h.position.y+=h.userData.vy;
      if(h.position.y>13) h.position.y=-13;
      if(h.position.y<-13) h.position.y=13;
    });
    re.render(sc,cam);
  })();
  window.addEventListener('resize',()=>{
    cam.aspect=innerWidth/innerHeight; cam.updateProjectionMatrix();
    re.setSize(innerWidth,innerHeight);
  });
})();
</script>
<script>
function swTab(id,btn){
  document.getElementById('p-login').style.display=id==='login'?'block':'none';
  document.getElementById('p-reg').style.display  =id==='reg'  ?'block':'none';
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
  btn.classList.add('on'); clrAlert();
}
function showAlert(msg,type){const a=document.getElementById('alert');a.textContent=msg;a.className='alert '+type;}
function clrAlert(){const a=document.getElementById('alert');a.className='alert';a.textContent='';}
function setBusy(id,on){document.getElementById(id+'b').disabled=on;document.getElementById(id+'s').style.display=on?'block':'none';document.getElementById(id+'t').style.display=on?'none':'';}

async function doLogin(){
  const email=document.getElementById('le').value.trim(), pw=document.getElementById('lp').value;
  if(!email||!pw){showAlert('Please fill in all fields','err');return;}
  setBusy('l',true);
  try{
    const d=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password:pw})}).then(r=>r.json());
    if(d.ok){showAlert('Welcome back! Redirecting…','ok');setTimeout(()=>location.href='/',700);}
    else showAlert(d.error||'Login failed','err');
  }catch{showAlert('Network error – is the server running?','err');}
  setBusy('l',false);
}
async function doReg(){
  const name=document.getElementById('rn').value.trim(), email=document.getElementById('re').value.trim(), pw=document.getElementById('rp').value;
  if(!name||!email||!pw){showAlert('Please fill in all fields','err');return;}
  if(pw.length<6){showAlert('Password must be at least 6 characters','err');return;}
  setBusy('r',true);
  try{
    const d=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:name,email,password:pw})}).then(r=>r.json());
    if(d.ok){showAlert('Account created! Redirecting…','ok');setTimeout(()=>location.href='/',700);}
    else showAlert(d.error||'Registration failed','err');
  }catch{showAlert('Network error – is the server running?','err');}
  setBusy('r',false);
}
</script>
</body></html>"""


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  CHAT PAGE HTML  (user data injected via Python f-string)
# ╚══════════════════════════════════════════════════════════════════════════════
def build_chat_html(user: dict, backend_status: str) -> str:
    user_js = json.dumps({
        "id":       user["id"],
        "username": user["username"],
        "plan":     user["plan"],
    })
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Nexus AI</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{
  --bg:#07080c;--sb:#0c0d14;--card:#12131c;--msg-ai:#12131e;
  --p:#8b5cf6;--c:#06b6d4;--pp:#7c3aed;
  --text:#f4f4f5;--dim:#71717a;--border:rgba(255,255,255,0.06);
  --danger:#f43f5e;--gold:#f59e0b;
  --code:#090911;
}}
html,body{{height:100%;overflow:hidden;}}
body{{
  font-family:'Inter',system-ui,sans-serif;
  background:var(--bg);color:var(--text);display:flex;position:relative;
}}
::-webkit-scrollbar{{width:4px;}} ::-webkit-scrollbar-thumb{{background:#27272a;border-radius:4px;}}

/* canvas bg */
#bg{{position:fixed;inset:0;z-index:0;pointer-events:none;opacity:0.35;}}

/* ── SIDEBAR ── */
#sb{{
  width:280px;background:var(--sb);display:flex;flex-direction:column;
  border-right:1px solid var(--border);flex-shrink:0;z-index:10;
  position:relative;
  backdrop-filter:blur(20px);
}}

.sb-top{{padding:20px 18px 14px;}}
.nx-logo{{display:flex;align-items:center;gap:12px;margin-bottom:18px;}}
.nx-logo svg{{flex-shrink:0;}}
.nx-name{{font-size:19px;font-weight:700;letter-spacing:-0.5px;color:#fff;font-family:'Outfit',sans-serif;}}
.nx-sub{{font-size:11px;color:var(--dim);margin-top:1px;}}

#new-btn{{
  display:flex;align-items:center;justify-content:center;gap:8px;
  width:100%;padding:10px 14px;
  background:linear-gradient(135deg,var(--p),var(--pp));
  color:#fff;border:none;border-radius:12px;font-size:13.5px;font-weight:600;cursor:pointer;
  box-shadow:0 4px 18px rgba(139,92,246,.25);transition:all .2s;
}}
#new-btn:hover{{transform:translateY(-1px);box-shadow:0 6px 24px rgba(139,92,246,.35);}}

.sb-search-wrap{{position:relative;margin:0 14px 12px;}}
.sb-search-wrap input{{
  width:100%;padding:9px 36px 9px 34px;
  background:rgba(255,255,255,0.03);border:1px solid var(--border);
  border-radius:10px;color:var(--text);font-size:13.5px;outline:none;
  transition:all .2s;
}}
.sb-search-wrap input:focus{{border-color:var(--p);background:rgba(255,255,255,0.06);}}
.sb-search-icon{{
  position:absolute;left:11px;top:50%;transform:translateY(-50%);
  display:flex;align-items:center;color:var(--dim);
}}
.sb-search-kbd{{
  position:absolute;right:11px;top:50%;transform:translateY(-50%);
  background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
  border-radius:5px;padding:1px 5px;font-size:10px;color:var(--dim);
  font-family:monospace;
}}

/* Sidebar navigation links */
.sb-nav{{
  padding:0 10px 12px;display:flex;flex-direction:column;gap:4px;
  border-bottom:1px solid var(--border);margin-bottom:12px;
}}
.sb-nav-item{{
  display:flex;align-items:center;gap:12px;padding:9px 12px;
  color:var(--dim);text-decoration:none;font-size:13.5px;font-weight:500;
  border-radius:10px;transition:all 0.15s;
}}
.sb-nav-item:hover{{
  background:rgba(255,255,255,0.04);color:#fff;
}}
.sb-nav-item.active{{
  background:rgba(139,92,246,0.1);color:var(--p);font-weight:600;
}}
.sb-nav-icon{{
  display:flex;align-items:center;justify-content:center;
}}

.sb-lbl{{padding:14px 16px 6px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--dim);}}
#convs{{flex:1;overflow-y:auto;padding:0 8px 8px;}}

.cv{{
  display:flex;align-items:center;gap:10px;padding:8px 12px;
  border-radius:10px;cursor:pointer;font-size:13.5px;
  transition:all .15s;margin-bottom:2px;color:#e4e4e7;
}}
.cv:hover{{background:rgba(255,255,255,0.03);}}
.cv.act{{background:var(--card);border:1px solid var(--border);color:#fff;}}
.cv-ico{{font-size:14px;flex-shrink:0;opacity:.5;display:flex;align-items:center;}}
.cv-ttl{{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.cv-del{{opacity:0;background:none;border:none;color:var(--danger);cursor:pointer;padding:2px 4px;border-radius:4px;font-size:13px;}}
.cv:hover .cv-del{{opacity:1;}}

/* Usage */
.usg{{padding:12px 16px 8px;border-top:1px solid var(--border);}}
.usg-row{{display:flex;justify-content:space-between;font-size:11px;color:var(--dim);margin-bottom:5px;}}
.usg-bar{{height:3px;background:rgba(255,255,255,.05);border-radius:2px;}}
.usg-fill{{height:100%;border-radius:2px;transition:width .5s,background .5s;background:linear-gradient(90deg,var(--p),var(--c));}}

/* Profile */
.prof{{
  padding:12px 14px;border-top:1px solid var(--border);
  display:flex;align-items:center;gap:10px;background:rgba(0,0,0,0.15);
}}
.av-big{{
  width:32px;height:32px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:700;color:#fff;
  background:linear-gradient(135deg,var(--p),var(--c));
}}
.prof-info{{flex:1;min-width:0;}}
.prof-name{{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff;}}
.badge{{
  display:inline-block;font-size:9px;font-weight:700;
  padding:1px 6px;border-radius:20px;margin-top:1px;text-transform:uppercase;
}}
.b-free{{background:rgba(113,113,122,.2);color:var(--dim);}}
.b-pro {{background:rgba(139,92,246,.2);color:var(--p);}}
.b-enterprise{{background:rgba(245,158,11,.2);color:var(--gold);}}
.pi-btn{{background:none;border:none;color:var(--dim);cursor:pointer;padding:6px;border-radius:8px;font-size:15px;transition:all .15s;}}
.pi-btn:hover{{color:#fff;background:rgba(255,255,255,0.05);}}

/* ── MAIN ── */
#main{{flex:1;display:flex;flex-direction:column;overflow:hidden;z-index:10;position:relative;min-width:0;}}

/* Header */
#hdr{{
  padding:14px 24px;
  display:flex;align-items:center;gap:12px;flex-shrink:0;
  z-index:20;
}}
.assistant-dropdown{{
  position:relative;display:inline-block;
}}
.assistant-dropdown-btn{{
  background:rgba(255,255,255,0.03);
  border:1px solid var(--border);
  padding:8px 16px;border-radius:12px;
  color:#fff;font-size:14px;font-weight:600;
  cursor:pointer;display:flex;align-items:center;
  gap:8px;transition:all 0.2s;
}}
.assistant-dropdown-btn:hover{{
  background:rgba(255,255,255,0.06);
  border-color:rgba(255,255,255,0.12);
}}

.online-pill{{
  margin-left:auto;display:flex;align-items:center;gap:6px;
  font-size:11.5px;color:var(--dim);background:rgba(255,255,255,0.02);
  padding:5px 12px;border-radius:20px;border:1px solid var(--border);
}}
.odot{{width:7px;height:7px;background:#22c55e;border-radius:50%;animation:blink 2s infinite;}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}

/* Messages */
#msgs{{flex:1;overflow-y:auto;padding:20px 8% 20px;display:flex;flex-direction:column;gap:20px;}}

/* Welcome screen with orb */
#welcome{{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  flex:1;text-align:center;padding:40px 20px;
}}
.orb-container{{
  display:flex;justify-content:center;align-items:center;margin-bottom:28px;
  perspective:1000px;
}}
.glowing-orb{{
  position:relative;width:130px;height:130px;border-radius:50%;
  background:radial-gradient(circle at 35% 35%, 
    #ffffff 0%, 
    #cbd5e1 15%, 
    #a78bfa 45%, 
    #22d3ee 70%, 
    #f472b6 90%, 
    #0f172a 100%
  );
  box-shadow: 
    0 0 50px rgba(139, 92, 246, 0.45),
    0 0 100px rgba(6, 182, 212, 0.25),
    inset -12px -12px 30px rgba(244, 114, 182, 0.35),
    inset 12px 12px 30px rgba(255, 255, 255, 0.75);
  animation: orb-float 5s ease-in-out infinite, orb-morph 7s ease-in-out infinite;
}}
.orb-shine{{
  position:absolute;top:15px;left:15px;width:100px;height:100px;border-radius:50%;
  background:radial-gradient(circle at 20% 20%, 
    rgba(255, 255, 255, 0.75) 0%, 
    rgba(255, 255, 255, 0) 50%
  );
  filter:blur(1px);pointer-events:none;
}}
@keyframes orb-float {{
  0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
  50% {{ transform: translateY(-12px) rotate(180deg); }}
}}
@keyframes orb-morph {{
  0%, 100% {{ border-radius: 50% 50% 50% 50%; }}
  25% {{ border-radius: 48% 52% 49% 51% / 51% 48% 52% 49%; }}
  50% {{ border-radius: 52% 48% 53% 47% / 47% 52% 48% 53%; }}
  75% {{ border-radius: 49% 51% 48% 52% / 53% 49% 51% 48%; }}
}}

#welcome h2{{
  font-size:32px;font-weight:500;color:#fff;
  letter-spacing:-0.5px;margin-bottom:8px;font-family:'Outfit',sans-serif;
}}
.user-span{{
  background:linear-gradient(135deg,#fff,#c084fc);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}}
#welcome p{{
  font-size:26px;font-weight:500;color:var(--dim);
  letter-spacing:-0.5px;font-family:'Outfit',sans-serif;margin-bottom:10px;
}}

/* Suggestion cards */
.suggest-grid{{
  display:grid;grid-template-columns:repeat(3,1fr);gap:16px;
  width:100%;max-width:880px;margin-top:36px;
}}
.suggest-card{{
  background:rgba(255, 255, 255, 0.02);
  border:1px solid rgba(255, 255, 255, 0.04);
  border-radius:16px;padding:18px 20px;text-align:left;
  cursor:pointer;transition:all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
}}
.suggest-card:hover{{
  background:rgba(255, 255, 255, 0.05);
  border-color:rgba(139, 92, 246, 0.35);
  transform:translateY(-4px);
  box-shadow:0 12px 24px rgba(0,0,0,0.25), 0 0 0 1px rgba(139,92,246,0.1);
}}
.suggest-card-title{{
  font-size:15px;font-weight:600;color:#fff;margin-bottom:6px;
}}
.suggest-card-desc{{
  font-size:12.5px;color:var(--dim);line-height:1.45;
}}

/* Bubbles styling */
.mrow{{display:flex;gap:12px;align-items:flex-start;animation:up .2s ease;}}
@keyframes up{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
.mrow.user{{flex-direction:row-reverse;}}
.av{{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;flex-shrink:0;}}
.av.ai  {{background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.25);color:var(--p);}}
.av.user{{background:linear-gradient(135deg,var(--p),var(--pp));color:#fff;}}
.bbl{{max-width:70%;padding:13px 18px;border-radius:18px;font-size:14px;line-height:1.65;}}
.mrow.ai .bbl{{background:var(--msg-ai);border:1px solid rgba(255,255,255,0.03);color:#e4e4e7;}}
.mrow.user .bbl{{background:linear-gradient(135deg,var(--p),var(--pp));color:#fff;}}
.mts{{font-size:10.5px;color:var(--dim);margin-top:5px;padding:0 4px;}}
.mrow.user .mts{{text-align:right;}}
.cursor{{display:inline-block;width:2px;height:15px;background:var(--p);animation:blink .6s infinite;vertical-align:text-bottom;margin-left:2px;}}
.bbl pre{{background:var(--code);border:1px solid var(--border);border-radius:10px;padding:14px 16px;overflow-x:auto;font-size:13px;margin:12px 0;position:relative;}}
.bbl code{{font-family:'Cascadia Code','Consolas','Monaco',monospace;}}
.cp-btn{{position:absolute;top:8px;right:8px;background:rgba(255,255,255,0.03);border:1px solid var(--border);color:var(--dim);border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;}}
.cp-btn:hover{{color:#fff;background:rgba(255,255,255,0.08);}}
.ic{{background:var(--code);padding:2px 6px;border-radius:4px;font-family:'Cascadia Code','Consolas',monospace;font-size:13px;border:1px solid var(--border);}}
.chat-img{{max-width:100%;max-height:280px;border-radius:10px;display:block;margin-bottom:8px;}}
.fatag{{display:flex;align-items:center;gap:8px;background:rgba(139,92,246,0.06);border:1px solid rgba(139,92,246,0.15);border-radius:8px;padding:7px 11px;margin-bottom:8px;font-size:12.5px;color:var(--dim);}}

.bbl p{{margin-bottom:8px;line-height:1.6;}}
.bbl p:last-child{{margin-bottom:0;}}
.bbl h1, .bbl h2, .bbl h3, .bbl h4{{color:#fff;margin-top:16px;margin-bottom:8px;font-weight:700;line-height:1.3;}}
.bbl h1{{font-size:1.4em;}} .bbl h2{{font-size:1.25em;}} .bbl h3{{font-size:1.15em;}}
.bbl ul, .bbl ol{{margin-left:22px;margin-bottom:8px;}}
.bbl li{{margin-bottom:4px;}}
.bbl blockquote{{border-left:3px solid var(--p);padding-left:12px;color:var(--dim);margin:12px 0;font-style:italic;}}
.bbl table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:13px;}}
.bbl th, .bbl td{{border:1px solid var(--border);padding:8px 10px;text-align:left;}}
.bbl th{{background:rgba(255,255,255,0.03);font-weight:700;color:#fff;}}

/* ── INPUT AREA ── */
#inp-area{{padding:14px 8% 24px;flex-shrink:0;z-index:20;background:var(--bg);}}

#file-prev{{display:none;align-items:center;gap:10px;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 14px;margin-bottom:10px;}}
#file-prev.show{{display:flex;}}
#fp-img{{max-height:56px;border-radius:6px;display:none;}}

#voice-ind{{display:none;align-items:center;gap:10px;background:rgba(244,63,94,.08);border:1px solid rgba(244,63,94,.2);border-radius:10px;padding:8px 14px;margin-bottom:10px;font-size:13px;color:var(--danger);}}
#voice-ind.show{{display:flex;}}
.vdot{{width:10px;height:10px;background:var(--danger);border-radius:50%;animation:pvdot 1s ease-in-out infinite;}}
@keyframes pvdot{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.5);opacity:.5}}}}

/* Consolidated input container card */
#inp-container {{
  background: #0f1016;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  transition: border-color 0.25s, box-shadow 0.25s;
}}
#inp-container:focus-within {{
  border-color: rgba(139, 92, 246, 0.45);
  box-shadow: 0 8px 32px rgba(139, 92, 246, 0.05);
}}

#ui {{
  flex:1;background:none;border:none;color:var(--text);
  font-size:14.5px;resize:none;max-height:160px;outline:none;
  font-family:inherit;line-height:1.5;padding:2px 0;width:100%;
  min-height:36px;
}}
#ui::placeholder{{color:#52525b;}}

.inp-actions-row {{
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.inp-actions-left {{
  display: flex;
  align-items: center;
  gap: 8px;
}}
.inp-actions-right {{
  display: flex;
  align-items: center;
  gap: 8px;
}}

.action-btn-icon {{
  background: transparent;
  border: none;
  color: #71717a;
  cursor: pointer;
  padding: 8px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}}
.action-btn-icon:hover {{
  color: #ffffff;
  background: rgba(255, 255, 255, 0.04);
}}
.action-btn-icon.rec {{
  color: var(--danger);
  background: rgba(244, 63, 94, 0.1);
}}

.action-btn-pill {{
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 30px;
  color: #e4e4e7;
  font-size: 12.5px;
  font-weight: 500;
  padding: 6px 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}}
.action-btn-pill:hover {{
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}}

#sbtn {{
  background: linear-gradient(135deg, var(--p), var(--pp));
  border: none;
  border-radius: 10px;
  color: #ffffff;
  width: 32px;
  height: 32px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}}
#sbtn:hover {{
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.4);
}}
#sbtn:disabled {{
  background: rgba(255, 255, 255, 0.03);
  color: #52525b;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}}

.ihint{{text-align:center;font-size:11px;color:var(--dim);margin-top:8px;}}
#fi,#ii{{display:none;}}

/* ── SUBSCRIBE MODAL ── */
#moverlay{{
  display:none;position:fixed;inset:0;z-index:100;
  background:rgba(0,0,0,.75);backdrop-filter:blur(8px);
  align-items:center;justify-content:center;
}}
#moverlay.show{{display:flex;}}
.modal{{
  background:#090912;border:1px solid var(--border);border-radius:22px;
  padding:34px 32px;width:580px;max-width:95vw;
  box-shadow:0 24px 80px rgba(0,0,0,.7),0 0 0 1px rgba(139,92,246,.1);
}}
.modal h2{{font-size:22px;font-weight:900;text-align:center;margin-bottom:6px;}}
.modal h2 span{{background:linear-gradient(135deg,var(--p),var(--c));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.modal p{{text-align:center;color:var(--dim);font-size:14px;margin-bottom:28px;}}
.plans{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}}
.pc{{
  background:var(--card);border:1.5px solid var(--border);border-radius:14px;
  padding:20px 16px;text-align:center;transition:all .2s;cursor:pointer;position:relative;overflow:hidden;
}}
.pc:hover{{border-color:var(--p);transform:translateY(-2px);box-shadow:0 8px 30px rgba(139,92,246,.15);}}
.pc.rec{{border-color:var(--p);}}
.pc-badge{{
  position:absolute;top:0;right:0;
  background:linear-gradient(135deg,var(--p),var(--c));
  color:#fff;font-size:10px;font-weight:800;
  padding:3px 12px;border-radius:0 14px 0 9px;
}}
.pc-name{{font-size:15px;font-weight:800;margin-bottom:6px;}}
.pc-price{{font-size:28px;font-weight:900;margin-bottom:4px;}}
.pc-price.free{{color:var(--dim);}} .pc-price.pro{{color:var(--p);}} .pc-price.ent{{color:var(--gold);}}
.pc-price sub{{font-size:13px;font-weight:400;color:var(--dim);}}
.pc ul{{list-style:none;text-align:left;font-size:12.5px;color:var(--dim);margin:12px 0 16px;}}
.pc ul li{{padding:3px 0;}} .pc ul li::before{{content:'✦ ';color:var(--p);font-size:10px;}}
.pc-btn{{
  display:block;width:100%;padding:9px;
  border:1.5px solid var(--border);background:none;
  color:var(--text);border-radius:9px;cursor:pointer;
  font-size:13px;font-weight:700;transition:all .2s;
}}
.pc-btn:hover,.pc.rec .pc-btn{{background:linear-gradient(135deg,var(--p),var(--pp));border-color:transparent;color:#fff;}}
.m-close{{display:block;margin:22px auto 0;background:none;border:none;color:var(--dim);cursor:pointer;font-size:13px;}}
.m-close:hover{{color:var(--text);}}

/* ── TOAST ── */
#toast{{
  position:fixed;top:18px;left:50%;transform:translateX(-50%);
  background:#0f0f24;border:1px solid var(--gold);border-radius:12px;
  padding:11px 18px;z-index:200;display:none;align-items:center;gap:10px;font-size:13px;
  box-shadow:0 8px 30px rgba(0,0,0,.4);animation:slideD .3s ease;min-width:280px;
}}
#toast.show{{display:flex;}}
@keyframes slideD{{from{{opacity:0;transform:translateX(-50%) translateY(-12px)}}to{{opacity:1;transform:translateX(-50%) translateY(0)}}}}
</style>
</head>
<body>
<canvas id="bg"></canvas>

<input type="file" id="fi" accept=".txt,.py,.js,.ts,.html,.css,.md,.json,.csv,.xml,.sh,.c,.cpp,.java"/>
<input type="file" id="ii" accept="image/*"/>

<!-- ═══ SIDEBAR ═══════════════════════════════════════════════════════════ -->
<div id="sb">
  <div class="sb-top">
    <div class="nx-logo">
      <!-- Nexus AI Logo SVG -->
      <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M16 4L4 28H10L16 16L22 28H28L16 4Z" fill="url(#axGlow)"/>
        <path d="M16 12L11 22H21L16 12Z" fill="#0c0d14"/>
        <circle cx="16" cy="19" r="2.5" fill="#06b6d4"/>
        <defs>
          <linearGradient id="axGlow" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#8b5cf6"/>
            <stop offset="100%" stop-color="#06b6d4"/>
          </linearGradient>
        </defs>
      </svg>
      <div>
        <div class="nx-name">Nexus AI</div>
        <div class="nx-sub">AI Assistant</div>
      </div>
    </div>
    <button id="new-btn" onclick="newChat()">✦ &nbsp;New Conversation</button>
  </div>

  <div class="sb-search-wrap">
    <div class="sb-search-icon">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    </div>
    <input type="text" placeholder="Search chats" oninput="searchConvs(this.value)"/>
    <div class="sb-search-kbd">⌘K</div>
  </div>

  <!-- Sidebar navigation list -->
  <div class="sb-nav">
    <a href="#" class="sb-nav-item active">
      <span class="sb-nav-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      </span>
      <span>Home</span>
    </a>
    <a href="#" class="sb-nav-item" onclick="openModal(); return false;">
      <span class="sb-nav-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>
      </span>
      <span>Templates</span>
    </a>
    <a href="#" class="sb-nav-item" onclick="alert('Nexus AI Explore feature coming soon!'); return false;">
      <span class="sb-nav-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>
      </span>
      <span>Explore</span>
    </a>
    <a href="#" class="sb-nav-item" onclick="document.getElementById('convs').focus(); return false;">
      <span class="sb-nav-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>
      </span>
      <span>History</span>
    </a>
    <a href="#" class="sb-nav-item" onclick="openModal(); return false;">
      <span class="sb-nav-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
      </span>
      <span>Wallet</span>
    </a>
  </div>

  <div id="convs"></div>

  <div class="usg">
    <div class="usg-row">
      <span id="usg-txt">0 / 50 messages today</span>
      <span id="usg-plan" style="color:var(--p);font-weight:700">Free</span>
    </div>
    <div class="usg-bar"><div class="usg-fill" id="usg-fill" style="width:0%"></div></div>
  </div>

  <div class="prof">
    <div class="av-big" id="pav">{user["username"][0].upper()}</div>
    <div class="prof-info">
      <div class="prof-name" id="pname">{user["username"]}</div>
      <span class="badge b-{user["plan"]}" id="pbadge">{user["plan"].title()}</span>
    </div>
    <button class="pi-btn" onclick="openModal()" title="Upgrade Plan">⚡</button>
    <button class="pi-btn" onclick="logout()" title="Sign Out">⏻</button>
  </div>
</div>

<!-- ═══ MAIN ══════════════════════════════════════════════════════════════ -->
<div id="main">
  <div id="hdr">
    <div class="assistant-dropdown">
      <button class="assistant-dropdown-btn">
        <span>AI Assistant</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
      </button>
    </div>
    <div class="online-pill"><div class="odot"></div>Online</div>
  </div>

  <div id="msgs">
    <div id="welcome">
      <div class="orb-container">
        <div class="glowing-orb">
          <div class="orb-shine"></div>
        </div>
      </div>
      <h2 id="welcome-title">Good Evening, <span class="user-span">{user["username"]}</span>.</h2>
      <p id="welcome-subtitle">Can I help you with anything ?</p>
      
      <!-- Suggestion Grid -->
      <div class="suggest-grid">
        <div class="suggest-card" onclick="useSuggest('Smart Budget')">
          <div class="suggest-card-title">Smart Budget</div>
          <div class="suggest-card-desc">A budget that fits your lifestyle, not the other way around</div>
        </div>
        <div class="suggest-card" onclick="useSuggest('Analytics')">
          <div class="suggest-card-title">Analytics</div>
          <div class="suggest-card-desc">Analytics empowers individuals and businesses to make smarter</div>
        </div>
        <div class="suggest-card" onclick="useSuggest('Spending')">
          <div class="suggest-card-title">Spending</div>
          <div class="suggest-card-desc">Spending is the way individuals and businesses use their financial</div>
        </div>
      </div>
    </div>
  </div>

  <div id="inp-area">
    <div id="file-prev">
      <span id="fp-ico">📄</span>
      <img id="fp-img" src="" alt=""/>
      <span id="fp-name" style="flex:1;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"></span>
      <button onclick="clearFile()" style="background:none;border:none;color:var(--danger);cursor:pointer;font-size:18px;">✕</button>
    </div>
    <div id="voice-ind">
      <div class="vdot"></div>
      Recording… click the mic again to stop and send
    </div>
    
    <!-- Consolidated input card -->
    <div id="inp-container">
      <textarea id="ui" rows="1" placeholder="Message Nexus AI…" onkeydown="hkey(event)" oninput="ars(this)"></textarea>
      
      <div class="inp-actions-row">
        <div class="inp-actions-left">
          <!-- Attach File -->
          <button class="action-btn-icon" onclick="document.getElementById('fi').click()" title="Attach File">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
          </button>
          
          <!-- Attach Image -->
          <button class="action-btn-icon" onclick="document.getElementById('ii').click()" title="Attach Image">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          </button>

          <!-- Create Image Pill -->
          <button class="action-btn-pill" onclick="triggerPill('image')" title="Create an image">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-12.728l.707.707m11.32 11.32l.707.707M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"/></svg>
            <span>Create an image</span>
          </button>

          <!-- Search Web Pill -->
          <button class="action-btn-pill" onclick="triggerPill('search')" title="Search the web">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20M2 12h20"/></svg>
            <span>Search the web</span>
          </button>
        </div>

        <div class="inp-actions-right">
          <!-- Voice Record -->
          <button class="action-btn-icon" id="vbtn" onclick="toggleVoice()" title="Voice Input">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8"/></svg>
          </button>
          
          <!-- Send Button -->
          <button id="sbtn" onclick="send()" title="Send">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
          </button>
        </div>
      </div>
    </div>

    <div class="ihint">Enter to send · Shift+Enter new line · Drag &amp; drop to upload files</div>
  </div>
</div>

<!-- ═══ SUBSCRIBE MODAL ════════════════════════════════════════════════════ -->
<div id="moverlay" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <h2>⚡ <span>Upgrade Nexus AI</span></h2>
    <p>Unlock more power — more messages, priority speed, and advanced features</p>
    <div class="plans">
      <div class="pc" onclick="subscribe('free')">
        <div class="pc-name">Free</div>
        <div class="pc-price free">₹0<sub>/mo</sub></div>
        <ul><li>50 messages/day</li><li>Text chat</li><li>File uploads</li><li>Chat history</li><li>Voice input</li></ul>
        <button class="pc-btn">Current Plan</button>
      </div>
      <div class="pc rec" onclick="subscribe('pro')">
        <div class="pc-badge">POPULAR</div>
        <div class="pc-name">Pro</div>
        <div class="pc-price pro">₹299<sub>/mo</sub></div>
        <ul><li>500 messages/day</li><li>Priority speed</li><li>Image analysis</li><li>Extended context</li><li>All Free features</li></ul>
        <button class="pc-btn">Go Pro →</button>
      </div>
      <div class="pc" onclick="subscribe('enterprise')">
        <div class="pc-name">Enterprise</div>
        <div class="pc-price ent">₹999<sub>/mo</sub></div>
        <ul><li>Unlimited messages</li><li>All Pro features</li><li>API access</li><li>Priority support</li><li>Custom model</li></ul>
        <button class="pc-btn">Go Enterprise →</button>
      </div>
    </div>
    <button class="m-close" onclick="closeModal()">✕ Close</button>
  </div>
</div>

<!-- ═══ TOAST ══════════════════════════════════════════════════════════════ -->
<div id="toast">
  <span>⚠️</span>
  <span id="toast-msg">You're running low on messages.</span>
  <button onclick="openModal();hideToast()" style="background:linear-gradient(135deg,var(--p),var(--pp));border:none;color:#fff;padding:5px 12px;border-radius:7px;cursor:pointer;font-size:12px;font-weight:700;flex-shrink:0;">Upgrade</button>
  <button onclick="hideToast()" style="background:none;border:none;color:var(--dim);cursor:pointer;font-size:17px;flex-shrink:0;">✕</button>
</div>

<!-- ═══ SCRIPTS ════════════════════════════════════════════════════════════ -->
<script>
/* ── Inject user from server ── */
const NX = {user_js};

/* ── Canvas Particle Nebula ─────────────────────────────────────────────── */
(()=>{{
  const cv=document.getElementById('bg'),ctx=cv.getContext('2d');
  let W=cv.width=innerWidth,H=cv.height=innerHeight;
  const COLS=['rgba(139,92,246,','rgba(6,182,212,','rgba(168,85,247,','rgba(91,33,182,'];
  const pts=Array.from({{length:60}},()=>{{
    const c=COLS[Math.floor(Math.random()*COLS.length)];
    return {{x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.3,vy:(Math.random()-.5)*.3,r:1+Math.random()*2,c,ph:Math.random()*Math.PI*2}};
  }});
  let t=0;
  function draw(){{
    t+=.004; ctx.clearRect(0,0,W,H);
    pts.forEach((p,i)=>{{
      p.x+=p.vx; p.y+=p.vy;
      if(p.x<0||p.x>W) p.vx*=-1;
      if(p.y<0||p.y>H) p.vy*=-1;
      const op=.2+.12*Math.sin(t+p.ph);
      /* glow */
      const gr=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,p.r*3.5);
      gr.addColorStop(0,p.c+(op+.15)+')');
      gr.addColorStop(1,p.c+'0)');
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r*3.5,0,Math.PI*2);
      ctx.fillStyle=gr; ctx.fill();
      /* dot */
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=p.c+op+')'; ctx.fill();
    }});
    requestAnimationFrame(draw);
  }}
  draw();
  window.addEventListener('resize',()=>{{W=cv.width=innerWidth;H=cv.height=innerHeight;}});
}})();

/* ── State ── */
let sid=null,busy=false,pendFile=null,recog=null,recOn=false;

/* ── Helpers ── */
const $=id=>document.getElementById(id);
const esc=t=>String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function ars(el){{el.style.height='auto';el.style.height=Math.min(el.scrollHeight,160)+'px';}}
function hkey(e){{if(e.key==='Enter'&&!e.shiftKey){{e.preventDefault();send();}}}}
function useSuggest(type){{
  let text = '';
  if (type === 'Smart Budget') text = "Can you help me design a smart budget fits for my lifestyle?";
  else if (type === 'Analytics') text = "How can business analytics help me make better financial decisions?";
  else if (type === 'Spending') text = "Provide strategies for managing and tracking personal spending.";
  $('ui').value=text;
  $('ui').focus();
  ars($('ui'));
}}
function triggerPill(type) {{
  const inp = $('ui');
  if (type === 'image') {{
    inp.value = "Create an image of: " + inp.value;
  }} else if (type === 'search') {{
    inp.value = "Search the web for: " + inp.value;
  }}
  inp.focus();
  ars(inp);
}}
function tstamp(){{return new Date().toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}});}}

/* ── Dynamic Greeting ── */
function updateGreeting() {{
  const hr = new Date().getHours();
  let greet = "Good Evening";
  if (hr < 12) greet = "Good Morning";
  else if (hr < 17) greet = "Good Afternoon";
  const titleEl = $('welcome-title');
  if (titleEl) {{
    titleEl.innerHTML = `${{greet}}, <span class="user-span">${{NX.username}}</span>.`;
  }}
}}

/* ── Refresh usage ── */
async function refreshUsage(){{
  const d=await fetch('/api/usage').then(r=>r.json());
  const pct=Math.min(100,(d.used/d.limit)*100);
  $('usg-txt').textContent=`${{d.used}} / ${{d.limit}} messages today`;
  $('usg-plan').textContent=d.plan.charAt(0).toUpperCase()+d.plan.slice(1);
  const f=$('usg-fill'); f.style.width=pct+'%';
  if(pct>=90) f.style.background='var(--danger)';
  else if(pct>=70) f.style.background='var(--gold)';
  else f.style.background='linear-gradient(90deg,var(--p),var(--c))';
  if(pct>=80&&pct<100) showToast(`${{d.remaining}} messages left today.`);
  if(pct>=100) showToast('Daily limit reached — upgrade to continue.');
}}

/* ── Toast ── */
function showToast(msg){{$('toast-msg').textContent=msg;$('toast').classList.add('show');setTimeout(hideToast,6000);}}
function hideToast(){{$('toast').classList.remove('show');}}

/* ── Modal ── */
function openModal(){{$('moverlay').classList.add('show');}}
function closeModal(){{$('moverlay').classList.remove('show');}}

async function subscribe(plan){{
  const r=await fetch('/api/subscribe',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{plan}})}}).then(r=>r.json());
  if(r.ok){{
    $('pbadge').textContent=plan.charAt(0).toUpperCase()+plan.slice(1);
    $('pbadge').className='badge b-'+plan;
    closeModal(); refreshUsage();
    showToast('✦ Plan upgraded to '+plan+'!');
  }}
}}

/* ── Logout ── */
async function logout(){{await fetch('/api/auth/logout',{{method:'POST'}});location.href='/login';}}

/* ── New chat ── */
function newChat(){{
  sid=null; pendFile=null; clearFile();
  $('msgs').innerHTML=buildWelcome();
  updateGreeting();
  document.querySelectorAll('.cv').forEach(e=>e.classList.remove('act'));
  $('ui').focus();
}}

function buildWelcome(){{
  return `<div id="welcome">
    <div class="orb-container">
      <div class="glowing-orb">
        <div class="orb-shine"></div>
      </div>
    </div>
    <h2 id="welcome-title">Good Evening, <span class="user-span">${{NX.username}}</span>.</h2>
    <p id="welcome-subtitle">Can I help you with anything ?</p>
    <div class="suggest-grid">
      <div class="suggest-card" onclick="useSuggest('Smart Budget')">
        <div class="suggest-card-title">Smart Budget</div>
        <div class="suggest-card-desc">A budget that fits your lifestyle, not the other way around</div>
      </div>
      <div class="suggest-card" onclick="useSuggest('Analytics')">
        <div class="suggest-card-title">Analytics</div>
        <div class="suggest-card-desc">Analytics empowers individuals and businesses to make smarter</div>
      </div>
      <div class="suggest-card" onclick="useSuggest('Spending')">
        <div class="suggest-card-title">Spending</div>
        <div class="suggest-card-desc">Spending is the way individuals and businesses use their financial</div>
      </div>
    </div>
  </div>`;
}}

/* ── Load conversations grouped ── */
async function loadConvs(search=''){{
  const url=search?`/api/convs?search=${{encodeURIComponent(search)}}`:`/api/convs`;
  const data=await fetch(url).then(r=>r.json());
  const el=$('convs');
  if(!data.length){{el.innerHTML='<div style="padding:14px 16px;color:var(--dim);font-size:13px;text-align:center;">No conversations yet</div>';return;}}
  
  const recent = [];
  const older = [];
  data.forEach(c => {{
    const created = new Date(c.created_at);
    const diffTime = Math.abs(new Date() - created);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays <= 2) {{
      recent.push(c);
    }} else {{
      older.push(c);
    }}
  }});

  let html = '';
  if (recent.length > 0) {{
    html += `<div class="sb-lbl">Recent</div>`;
    html += recent.map(c => `
      <div class="cv ${{c.sid===sid?'act':''}}" onclick="loadChat('${{c.sid}}')">
        <span class="cv-ico">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </span>
        <span class="cv-ttl">${{esc(c.title)}}</span>
        <button class="cv-del" onclick="delChat(event,'${{c.sid}}')" title="Delete">⊗</button>
      </div>
    `).join('');
  }}
  if (older.length > 0) {{
    html += `<div class="sb-lbl">Older</div>`;
    html += older.map(c => `
      <div class="cv ${{c.sid===sid?'act':''}}" onclick="loadChat('${{c.sid}}')">
        <span class="cv-ico">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </span>
        <span class="cv-ttl">${{esc(c.title)}}</span>
        <button class="cv-del" onclick="delChat(event,'${{c.sid}}')" title="Delete">⊗</button>
      </div>
    `).join('');
  }}
  
  if (recent.length === 0 && older.length === 0) {{
    html = '<div style="padding:14px 16px;color:var(--dim);font-size:13px;text-align:center;">No conversations yet</div>';
  }}
  el.innerHTML = html;
}}

function searchConvs(v){{loadConvs(v);}}

async function loadChat(s){{
  sid=s;
  const msgs=await fetch(`/api/history/${{s}}`).then(r=>r.json());
  const cont=$('msgs'); cont.innerHTML='';
  msgs.forEach(m=>addBubble(m.role,m.content,false,m.file_name,m.file_type,m.ts));
  cont.scrollTop=cont.scrollHeight;
  loadConvs();
}}

async function delChat(e,s){{
  e.stopPropagation();
  await fetch(`/api/convs/${{s}}`,{{method:'DELETE'}});
  if(sid===s) newChat(); else loadConvs();
}}

/* ── File uploads ── */
$('fi').addEventListener('change',async function(){{
  if(!this.files[0]) return;
  await uploadFile(this.files[0]); this.value='';
}});
$('ii').addEventListener('change',async function(){{
  if(!this.files[0]) return;
  await uploadFile(this.files[0]); this.value='';
}});

async function uploadFile(file){{
  const form=new FormData(); form.append('file',file);
  const d=await fetch('/api/upload',{{method:'POST',body:form}}).then(r=>r.json());
  if(d.error){{alert(d.error);return;}}
  pendFile=d;
  $('file-prev').classList.add('show');
  $('fp-name').textContent=d.filename;
  const img=$('fp-img');
  if(d.type==='image'){{$('fp-ico').textContent='🖼';img.src=d.url;img.style.display='block';}}
  else{{$('fp-ico').textContent='📄';img.style.display='none';}}
}}
function clearFile(){{pendFile=null;$('file-prev').classList.remove('show');$('fp-img').style.display='none';}}

/* ── Voice ── */
function toggleVoice(){{
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){{alert('Voice is supported in Chrome only. Please use Chrome browser.');return;}}
  if(recOn){{recog.stop();return;}}
  recog=new SR(); recog.lang='en-US'; recog.interimResults=true; recog.continuous=false;
  recog.onstart=()=>{{recOn=true;$('vbtn').classList.add('rec');$('voice-ind').classList.add('show');}};
  recog.onresult=e=>{{
    const t=Array.from(e.results).map(r=>r[0].transcript).join('');
    $('ui').value=t; ars($('ui'));
  }};
  recog.onend=()=>{{recOn=false;$('vbtn').classList.remove('rec');$('voice-ind').classList.remove('show');}};
  recog.onerror=()=>{{recOn=false;$('vbtn').classList.remove('rec');$('voice-ind').classList.remove('show');}};
  recog.start();
}}

/* ── Format message ── */
function fmt(text, streaming=false){{
  if(!text) return '';
  let html = '';
  try {{
    const renderer = new marked.Renderer();
    renderer.code = function(code, lang) {{
      const id = 'cb' + Math.random().toString(36).slice(2, 8);
      return '<pre id="' + id + '"><button class="cp-btn" onclick="cpCode(\\\'' + id + '\\\')">Copy</button><code class="language-' + (lang || '') + '">' + esc(code.trim()) + '</code></pre>';
    }};
    marked.setOptions({{ renderer: renderer, gfm: true, breaks: true }});
    html = marked.parse(text);
  }} catch(e) {{
    html = esc(text);
  }}
  if(streaming) {{
    if(html.endsWith('</p>\n')) {{
      html = html.slice(0, -5) + '<span class="cursor"></span></p>\n';
    }} else if(html.endsWith('</p>')) {{
      html = html.slice(0, -4) + '<span class="cursor"></span></p>';
    }} else if(html.endsWith('</li>\n')) {{
      html = html.slice(0, -6) + '<span class="cursor"></span></li>\n';
    }} else {{
      html += '<span class="cursor"></span>';
    }}
  }}
  return html;
}}

function cpCode(id){{
  navigator.clipboard.writeText(document.querySelector(`#${{id}} code`).innerText).then(()=>{{
    const b=document.querySelector(`#${{id}} .cp-btn`);
    b.textContent='Copied!'; setTimeout(()=>b.textContent='Copy',2000);
  }});
}}

/* ── Add bubble ── */
function addBubble(role,content,streaming=false,fileName=null,fileType=null,ts=null){{
  const w=document.getElementById('welcome'); if(w) w.remove();
  const cont=$('msgs');
  const row=document.createElement('div');
  row.className='mrow '+role;
  if(streaming) row.id='srow';
  const init=role==='user'?(NX.username||'U')[0].toUpperCase():'A';
  let fHtml='';
  if(fileName){{
    if(fileType==='image') fHtml=`<img class="chat-img" src="/uploads/${{esc(fileName)}}" alt="img" onerror="this.style.display='none'"/>`;
    else fHtml=`<div class="fatag"><span>📄</span><span>${{esc(fileName)}}</span></div>`;
  }}
  const time=ts?new Date(ts).toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}}):tstamp();
  row.innerHTML=`
    <div class="av ${{role}}">${{init}}</div>
    <div>
      <div class="bbl" ${{streaming?'id="sc"':''}}>
        ${{fHtml}}
        ${{streaming?'<span class="cursor"></span>':fmt(content)}}
      </div>
      <div class="mts">${{time}}</div>
    </div>`;
  cont.appendChild(row);
  cont.scrollTop=cont.scrollHeight;
  return row;
}}

/* ── SEND ── */
async function send(){{
  if(busy) return;
  const inp=$('ui'), msg=inp.value.trim();
  if(!msg&&!pendFile) return;
  inp.value=''; inp.style.height='auto';
  $('sbtn').disabled=true; busy=true;

  const fName=pendFile?.filename||null, fType=pendFile?.type||null;
  addBubble('user',msg,false,fName,fType);
  const fp=pendFile?{{...pendFile}}:null; clearFile();
  addBubble('ai','',true);
  const sc=$('sc'), cont=$('msgs');
  let full='';

  try{{
    const res=await fetch('/api/chat',{{
      method:'POST',headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify({{message:msg,sid,file:fp}})
    }});
    if(!res.ok){{
      const d=await res.json().catch(()=>({{}}));
      const errText=d.error||`Server error: ${{res.status}}`;
      sc.innerHTML=`<span style="color:var(--danger)">⚠️ ${{esc(errText)}}</span>`;
      const sr=$('srow'); if(sr) sr.id=''; sc.id='';
      busy=false; $('sbtn').disabled=false; return;
    }}
    const reader=res.body.getReader(), dec=new TextDecoder();
    while(true){{
      const {{value,done}}=await reader.read(); if(done) break;
      const chunk=dec.decode(value);
      for(const line of chunk.split('\n')){{
        if(!line.startsWith('data: ')) continue;
        try{{
          const d=JSON.parse(line.slice(6));
          if(d.token){{full+=d.token;sc.innerHTML=fmt(full,true);cont.scrollTop=cont.scrollHeight;}}
          if(d.sid&&!sid) sid=d.sid;
          if(d.done){{sc.innerHTML=fmt(full,false);const sr=$('srow');if(sr)sr.id='';sc.id='';loadConvs();refreshUsage();}}
          if(d.error){{sc.innerHTML=`<span style="color:var(--danger)">⚠️ ${{esc(d.error)}}</span>`;}}
        }}catch(_){{}}
      }}
    }}
    if(sc.id==='sc'){{
      if(full){{
        sc.innerHTML=fmt(full,false);
      }}else{{
        sc.innerHTML=`<span style="color:var(--danger)">⚠️ Connection closed with no response.</span>`;
      }}
      const sr=$('srow'); if(sr) sr.id=''; sc.id='';
    }}
  }}catch(err){{
    sc.innerHTML=`<span style="color:var(--danger)">⚠️ Could not reach the server.<br><small>Check if the python server is running.</small></span>`;
  }}
  busy=false; $('sbtn').disabled=false; inp.focus();
}}

/* ── Boot ── */
loadConvs(); refreshUsage(); updateGreeting(); $('ui').focus();
</script>
</body></html>"""



# ╔══════════════════════════════════════════════════════════════════════════════
# ║  ROUTES
# ╚══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    u = cur_user(request)
    if not u:
        return RedirectResponse("/login")
    if GEMINI_API_KEY and GEMINI_API_KEY.strip():
        status = "Gemini AI ⚡ Ultra Fast"
    elif GROQ_API_KEY and GROQ_API_KEY.strip():
        status = "Groq Cloud ⚡ Ultra Fast"
    else:
        status = "Local Ollama ◈ Normal Speed"
    return HTMLResponse(build_chat_html(u, status))


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if cur_user(request):
        return RedirectResponse("/")
    return HTMLResponse(LOGIN_HTML)

# Auth
@app.post("/api/auth/register")
async def register(request: Request):
    b = await request.json()
    un, em, pw = b.get("username","").strip(), b.get("email","").strip().lower(), b.get("password","")
    if not un or not em or not pw:
        return JSONResponse({"error":"All fields required"},status_code=400)
    if len(pw) < 6:
        return JSONResponse({"error":"Password must be ≥ 6 characters"},status_code=400)
    u = database.create_user(un, em, pw)
    if not u:
        return JSONResponse({"error":"Email or username already exists"},status_code=409)
    tok = database.create_session(u["id"])
    res = JSONResponse({"ok":True})
    res.set_cookie("nx_tok", tok, httponly=True, max_age=7*86400, samesite="lax", path="/")
    return res

@app.post("/api/auth/login")
async def login(request: Request):
    b  = await request.json()
    em = b.get("email","").strip().lower()
    pw = b.get("password","")
    u  = database.get_user_by_email(em)
    if not u or not database.verify_pw(pw, u["password_hash"], u["salt"]):
        return JSONResponse({"error":"Invalid email or password"},status_code=401)
    tok = database.create_session(u["id"])
    res = JSONResponse({"ok":True})
    res.set_cookie("nx_tok", tok, httponly=True, max_age=7*86400, samesite="lax", path="/")
    return res

@app.post("/api/auth/logout")
async def logout_api(request: Request):
    tok = request.cookies.get("nx_tok")
    if tok: database.delete_session(tok)
    res = JSONResponse({"ok":True})
    res.delete_cookie("nx_tok")
    return res

# Conversations
@app.get("/api/convs")
async def convs(request: Request, search: str = ""):
    u = cur_user(request)
    if not u: return JSONResponse({"error":"Unauthorised"},status_code=401)
    return database.get_convs(u["id"], search)

@app.get("/api/history/{sid}")
async def history(sid: str, request: Request):
    u = cur_user(request)
    if not u: return JSONResponse({"error":"Unauthorised"},status_code=401)
    return database.get_msgs(sid)

@app.delete("/api/convs/{sid}")
async def del_conv(sid: str, request: Request):
    u = cur_user(request)
    if not u: return JSONResponse({"error":"Unauthorised"},status_code=401)
    database.del_conv(sid, u["id"])
    return {"ok":True}

# Usage & Subscription
@app.get("/api/usage")
async def usage_api(request: Request):
    u = cur_user(request)
    if not u: return JSONResponse({"error":"Unauthorised"},status_code=401)
    return database.get_usage(u["id"])

@app.post("/api/subscribe")
async def sub_api(request: Request):
    u = cur_user(request)
    if not u: return JSONResponse({"error":"Unauthorised"},status_code=401)
    b = await request.json()
    plan = b.get("plan","free")
    if plan not in database.PLAN_LIMITS:
        return JSONResponse({"error":"Invalid plan"},status_code=400)
    database.upgrade_plan(u["id"], plan)
    return {"ok":True,"plan":plan,"limit":database.PLAN_LIMITS[plan]}

# File upload
@app.post("/api/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    u = cur_user(request)
    if not u: return JSONResponse({"error":"Unauthorised"},status_code=401)
    ext  = Path(file.filename).suffix.lower()
    data = await file.read()
    if len(data) > 10*1024*1024:
        return JSONResponse({"error":"File too large (max 10 MB)"},status_code=413)
    fid   = str(uuid.uuid4())
    fname = f"{fid}{ext}"
    async with aiofiles.open(UPLOAD_DIR/fname,"wb") as f:
        await f.write(data)
    ftype = "image" if ext in IMG_EXT else ("text" if ext in TEXT_EXT else "binary")
    content = None
    if ftype == "text":
        try: content = data.decode("utf-8","replace")[:8000]
        except: pass
    return {"file_id":fid,"filename":file.filename,"saved_as":fname,
            "type":ftype,"url":f"/uploads/{fname}","content":content}

# Chat (streaming)
@app.post("/api/chat")
async def chat_api(request: Request):
    u = cur_user(request)
    if not u: return JSONResponse({"error":"Unauthorised"},status_code=401)
    if database.is_limited(u["id"]):
        ug = database.get_usage(u["id"])
        return JSONResponse({"error":f"Daily limit of {ug['limit']} messages reached. Upgrade your plan to continue.","limit_reached":True},status_code=429)

    b    = await request.json()
    msg  = b.get("message","").strip()
    sid  = b.get("sid") or str(uuid.uuid4())
    fi   = b.get("file")

    if not msg and not fi:
        return JSONResponse({"error":"Empty message"},status_code=400)

    fname_db = ftype_db = None
    prompt   = msg

    if fi:
        fname_db = fi.get("filename")
        ftype_db = fi.get("type")
        if ftype_db == "text" and fi.get("content"):
            prompt = (f"[Attached file: {fname_db}]\n```\n{fi['content'][:6000]}\n```\n\n"
                      f"User says: {msg}" if msg else
                      f"[Attached file: {fname_db}]\n```\n{fi['content'][:6000]}\n```\n\nPlease analyse this file.")
        elif ftype_db == "image":
            prompt = f"[User attached image: {fname_db}]\n{msg or 'Please describe this image.'}"

    database.save_msg(sid, u["id"], "user", msg or f"[File: {fname_db}]", fname_db, ftype_db)
    database.bump_usage(u["id"])

    history  = database.get_msgs(sid)
    is_gemini = bool(GEMINI_API_KEY and GEMINI_API_KEY.strip())

    if is_gemini:
        # Build contents array in Gemini format, merging consecutive user/model messages
        gemini_contents = []
        for idx, m in enumerate(history):
            role = "user" if m["role"] == "user" else "model"
            text_content = m["content"] if idx != len(history) - 1 or m["role"] != "user" else prompt
            
            if gemini_contents and gemini_contents[-1]["role"] == role:
                for part in gemini_contents[-1]["parts"]:
                    if "text" in part:
                        part["text"] += "\n\n" + text_content
                        break
                else:
                    gemini_contents[-1]["parts"].append({"text": text_content})
            else:
                gemini_contents.append({"role": role, "parts": [{"text": text_content}]})
                
        # Attach image inlineData to the last user message if applicable
        if ftype_db == "image" and fi:
            img_path = UPLOAD_DIR / fi.get("saved_as")
            if img_path.exists():
                try:
                    with open(img_path, "rb") as img_f:
                        b64_img = base64.b64encode(img_f.read()).decode("utf-8")
                    ext = img_path.suffix.lower()
                    mime_type = "image/jpeg"
                    if ext == ".png": mime_type = "image/png"
                    elif ext == ".gif": mime_type = "image/gif"
                    elif ext == ".webp": mime_type = "image/webp"
                    
                    for item in reversed(gemini_contents):
                        if item["role"] == "user":
                            item["parts"].insert(0, {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": b64_img
                                }
                            })
                            break
                except:
                    pass
                    
        gemini_payload = {
            "contents": gemini_contents,
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            }
        }
    else:
        messages = [{"role":"system","content":SYSTEM_PROMPT}]
        is_groq_vision = bool(GROQ_API_KEY and GROQ_API_KEY.strip()) and ftype_db == "image" and fi

        for i,m in enumerate(history):
            if i == len(history)-1 and m["role"] == "user":
                if is_groq_vision:
                    img_path = UPLOAD_DIR / fi.get("saved_as")
                    if img_path.exists():
                        try:
                            with open(img_path, "rb") as img_f:
                                b64_img = base64.b64encode(img_f.read()).decode("utf-8")
                            ext = img_path.suffix.lower()
                            mime_type = "image/jpeg"
                            if ext == ".png": mime_type = "image/png"
                            elif ext == ".gif": mime_type = "image/gif"
                            elif ext == ".webp": mime_type = "image/webp"
                            
                            content = [
                                {"type": "text", "text": msg or "Describe this image."},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{b64_img}"
                                    }
                                }
                            ]
                        except:
                            content = prompt
                    else:
                        content = prompt
                else:
                    content = prompt
            else:
                content = m["content"]
            messages.append({"role":m["role"],"content":content})

    model = GROQ_MODEL
    if GROQ_API_KEY and GROQ_API_KEY.strip() and ftype_db == "image":
        model = "llama-3.2-11b-vision-preview"

    async def stream():
        full = ""
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                if is_gemini:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}"
                    async with client.stream("POST", url, json=gemini_payload) as resp:
                        if resp.status_code != 200:
                            err_content = await resp.aread()
                            try:
                                err_json = json.loads(err_content)
                                err_msg = err_json.get("error", {}).get("message", "Gemini API error")
                            except:
                                err_msg = f"Gemini API returned status code {resp.status_code}"
                            yield f"data: {json.dumps({'error': err_msg})}\n\n"
                            return

                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if not line: continue
                            if line.startswith("data: "):
                                try:
                                    d = json.loads(line[6:])
                                    tok = d.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                    if tok:
                                        full += tok
                                        yield f"data: {json.dumps({'token': tok, 'sid': sid})}\n\n"
                                except json.JSONDecodeError: continue
                elif GROQ_API_KEY and GROQ_API_KEY.strip():
                    headers = {
                        "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
                        "Content-Type": "application/json"
                    }
                    async with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json={"model": model, "messages": messages, "stream": True}) as resp:
                        
                        if resp.status_code != 200:
                            err_content = await resp.aread()
                            try:
                                err_json = json.loads(err_content)
                                err_msg = err_json.get("error", {}).get("message", "Groq API error")
                            except:
                                err_msg = f"Groq API returned status code {resp.status_code}"
                            yield f"data: {json.dumps({'error': err_msg})}\n\n"
                            return

                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if not line: continue
                            if line == "data: [DONE]": break
                            if line.startswith("data: "):
                                try:
                                    d = json.loads(line[6:])
                                    tok = d.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if tok:
                                        full += tok
                                        yield f"data: {json.dumps({'token': tok, 'sid': sid})}\n\n"
                                except json.JSONDecodeError: continue
                else:
                    async with client.stream("POST", f"{OLLAMA_URL}/api/chat",
                        json={"model": OLLAMA_MODEL, "messages": messages, "stream": True}) as resp:
                        
                        if resp.status_code != 200:
                            err_content = await resp.aread()
                            yield f"data: {json.dumps({'error': f'Ollama returned status code {resp.status_code}'})}\n\n"
                            return

                        async for line in resp.aiter_lines():
                            if not line: continue
                            try:
                                d = json.loads(line)
                                tok = d.get("message", {}).get("content", "")
                                if tok:
                                    full += tok
                                    yield f"data: {json.dumps({'token': tok, 'sid': sid})}\n\n"
                                if d.get("done"): break
                            except json.JSONDecodeError: continue
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        if full:
            database.save_msg(sid, u["id"], "assistant", full)
        ug = database.get_usage(u["id"])
        yield f"data: {json.dumps({'done': True, 'sid': sid, 'usage': ug})}\n\n"


    return StreamingResponse(stream(), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})


if __name__ == "__main__":
    import uvicorn
    print("\n* NexusAI starting at http://localhost:8000\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
