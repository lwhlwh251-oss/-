# ============================================================
#  KHALED RASHQ — موقع رشق مجاني
#  دمج: Zefame + TikSpark
#  تطوير: Khaled
# ============================================================

import os
import json
import uuid
import time
import hmac
import hashlib
import requests
from urllib.parse import urlparse
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ============================================================
#  ⚙️ الإعدادات
# ============================================================
OWNER_NAME = "Khaled"
CHANNEL_LINK = "https://t.me/YOUR_CHANNEL"

TIKSPARK_USERNAME = "ضع_يوزر"
TIKSPARK_PASSWORD = "ضع_باسورد"
USE_TIKSPARK = False


# ============================================================
#  Zefame
# ============================================================
ZEFAME_URL = "https://zefame-free.com/api_free.php"
ZEFAME_HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://zefame.com",
    "referer": "https://zefame.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

ZEFAME_SERVICES = {
    "tiktok_views":      229,
    "tiktok_likes":      232,
    "tiktok_followers":  228,
    "tiktok_comments":   232,
    "telegram_views":    248,
    "facebook_views":    244,
    "instagram_views":   237,
    "twitter_views":     231,
    "youtube_views":     245,
    "share_boost":       244,
}


def zefame_request(data=None, params=None):
    try:
        if data:
            r = requests.post(ZEFAME_URL, headers=ZEFAME_HEADERS, data=data, timeout=30)
        else:
            r = requests.get(ZEFAME_URL, headers=ZEFAME_HEADERS, params=params, timeout=30)
        return r.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


def extract_video_id(url):
    try:
        parts = urlparse(url).path.split('/')
        for i, p in enumerate(parts):
            if p == 'video' and i + 1 < len(parts):
                return parts[i + 1].split('?')[0]
    except:
        pass
    return None


def extract_username(url):
    try:
        for p in urlparse(url).path.split('/'):
            if p.startswith('@'):
                return p[1:]
    except:
        pass
    return None


def zefame_order(service_id, link, extra_key=None, extra_val=None):
    device_id = str(uuid.uuid4())

    check_data = {"action": "check", "device": device_id, "service": service_id}
    if extra_key and extra_val:
        check_data[extra_key] = extra_val

    check_res = zefame_request(data=check_data)
    if not (check_res and check_res.get('success')):
        return False, check_res.get('message', 'فشل التحقق') if check_res else 'فشل الاتصال'

    order_data = {"action": "order", "service": service_id, "link": link, "uuid": device_id}
    if extra_key and extra_val:
        order_data[extra_key] = extra_val

    order_res = zefame_request(data=order_data)
    if order_res and order_res.get('success'):
        order_id = order_res.get('data', {}).get('orderId', 'N/A')
        return True, f"تم الإرسال — رقم الطلب: {order_id}"
    else:
        return False, order_res.get('message', 'فشل الطلب') if order_res else 'فشل'


def zefame_execute(service_type, link):
    sid = ZEFAME_SERVICES.get(service_type)
    if not sid:
        return False, "خدمة غير معروفة"

    if service_type == "tiktok_followers":
        username = extract_username(link)
        if not username:
            return False, "رابط غير صحيح — لازم يوزر تيك توك"
        return zefame_order(sid, link, "username", username)

    if service_type in ("tiktok_views", "tiktok_likes", "tiktok_comments"):
        video_id = extract_video_id(link)
        if not video_id:
            return False, "رابط فيديو غير صحيح"
        return zefame_order(sid, link, "videoId", video_id)

    return zefame_order(sid, link)


# ============================================================
#  TikSpark (احتياطي)
# ============================================================
DEVICE_INFO = '{"d":"61393235613366373261636533656632","n":"INFINIX Infinix Lite 30","o":"16","t":"d","v":"2.2.9","s":"0,0"}'
_B = [0x35, 0x30, 0x1c, 0x2f, 0x2c, 0x2c, 0x28, 0x31, 0x35, 0x30, 0x1c, 0x2f, 0x2c, 0x2c, 0x28, 0x31]
APP_SECRET = bytes([b ^ 0x43 for b in _B])

TS_USER_TOKEN = ""
TS_CSRF_TOKEN = ""


def ts_make_signature(ts, nonce, payload):
    msg = f"{ts}-{nonce}-{payload}"
    return hmac.new(APP_SECRET, msg.encode('utf-8'), hashlib.sha256).hexdigest()


def ts_api_request(payload, op_name, needs_auth=True):
    global TS_USER_TOKEN, TS_CSRF_TOKEN
    endpoint = "https://api.tikspark.xyz/graphql"
    payload_str = json.dumps(payload, separators=(',', ':'))

    ts = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())[:16]
    sig = ts_make_signature(ts, nonce, payload_str)

    op_ids = {
        "LoginAccount": "3522613813036d73817b2715e67743f8d23d7a85ad08b7e12aa3b29a24a17c43",
        "AttestDevice": "bfaf5a72aeb9a337811da6a6d13e0b73680a18ffde0c59a23701e55b98ac2515",
        "CreateOrder":  "ad7a6397c3970b1e7601f69d24989bff330e256ee5e39321a8d1ad3fe3879b48"
    }

    headers = {
        "X-APOLLO-OPERATION-NAME": op_name,
        "Accept": "multipart/mixed; deferSpec=20220824, application/json",
        "x-language": "ar",
        "x-app-name": "com.dev.vidspark",
        "x-device-info": DEVICE_INFO,
        "x-app-sig": sig,
        "x-app-ts": ts,
        "x-app-nonce": nonce,
        "Content-Type": "application/json",
        "User-Agent": "okhttp/4.12.0"
    }
    if op_name in op_ids:
        headers["X-APOLLO-OPERATION-ID"] = op_ids[op_name]
    if needs_auth:
        headers["token"] = TS_USER_TOKEN
        headers["x-csrf-token"] = TS_CSRF_TOKEN

    try:
        r = requests.post(endpoint, headers=headers, data=payload_str, timeout=20)
        return r, r.json()
    except Exception as e:
        return None, {"error": str(e)}


def ts_login():
    global TS_USER_TOKEN, TS_CSRF_TOKEN
    payload = {
        "operationName": "LoginAccount",
        "variables": {
            "data": {
                "id": "", "uniqueId": TIKSPARK_USERNAME, "nickname": "",
                "avatarMedium": "", "followerCount": 0, "followingCount": 0,
                "videoCount": 0, "privateAccount": False, "diggCount": 0,
                "authMethod": "local", "password": TIKSPARK_PASSWORD
            }
        },
        "query": "mutation LoginAccount($data: TiktokInfo) { loginTiktok(data: $data) { accessToken refreshToken user { _id username score } } }"
    }
    obj, js = ts_api_request(payload, "LoginAccount", False)
    if obj and "errors" not in js:
        try:
            TS_USER_TOKEN = js['data']['loginTiktok']['accessToken']
            new_csrf = obj.headers.get("x-csrf-token")
            if new_csrf:
                TS_CSRF_TOKEN = new_csrf
            return True
        except:
            return False
    return False


def ts_create_order(order_type, amount, video_link=None, username=None):
    variables = {
        "type": order_type,
        "amount": amount,
        "avatar": "",
        "initialCount": 0
    }
    if video_link:
        variables["videoLink"] = video_link
    if username:
        variables["tiktokerUsername"] = username

    payload = {
        "operationName": "CreateOrder",
        "variables": variables,
        "query": "mutation CreateOrder($type: Action!, $amount: Int!, $tiktokerUsername: String, $videoLink: String, $avatar: String, $initialCount: Int) { createOrder(orderInput: { type: $type amount: $amount tiktokerUsername: $tiktokerUsername videoLink: $videoLink avatar: $avatar initialCount: $initialCount } ) { _id type amount status } }"
    }
    _, result = ts_api_request(payload, "CreateOrder", True)
    return result


# ============================================================
#  HTML
# ============================================================
HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>✨ {{ owner }} — رشق مجاني ✨</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&family=Amiri:wght@700&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Cairo',sans-serif; }
body { background:#0a0a0f; background-image: radial-gradient(circle at 20% 20%, rgba(255,215,0,0.08), transparent 40%), radial-gradient(circle at 80% 80%, rgba(255,23,68,0.08), transparent 40%); min-height:100vh; color:#fff; padding:15px; }
.stars { position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:0; }
.star { position:absolute; width:2px; height:2px; background:#fff; border-radius:50%; animation:twinkle 3s infinite; }
@keyframes twinkle { 0%,100%{opacity:.2;transform:scale(1);} 50%{opacity:1;transform:scale(1.5);} }
.container { max-width:750px; margin:0 auto; position:relative; z-index:1; }
.hero { text-align:center; padding:20px 10px; }
.crown { font-size:45px; display:inline-block; animation:float 3s infinite; filter:drop-shadow(0 0 25px rgba(255,215,0,.7)); }
@keyframes float { 0%,100%{transform:translateY(0);} 50%{transform:translateY(-10px);} }
.owner-name { font-family:'Amiri',serif; font-size:52px; font-weight:700; background:linear-gradient(135deg,#FFD700,#FFF8DC,#FFD700,#B8860B,#FFD700); background-size:200% 200%; -webkit-background-clip:text; -webkit-text-fill-color:transparent; animation:shine 4s linear infinite; letter-spacing:3px; }
@keyframes shine { 0%{background-position:0% 50%;} 100%{background-position:200% 50%;} }
.divider { display:flex; align-items:center; justify-content:center; gap:15px; margin:10px 0; color:#FFD700; }
.divider::before, .divider::after { content:''; height:1px; width:60px; background:linear-gradient(90deg,transparent,#FFD700,transparent); }
.subtitle { color:#aaa; font-size:14px; margin-bottom:20px; }
.card { background:rgba(20,20,30,.7); backdrop-filter:blur(20px); padding:25px; border-radius:25px; border:1px solid rgba(255,215,0,.2); box-shadow:0 25px 50px rgba(0,0,0,.7); margin-bottom:20px; position:relative; overflow:hidden; }
.card::before { content:''; position:absolute; top:0; left:-100%; width:100%; height:2px; background:linear-gradient(90deg,transparent,#FFD700,transparent); animation:slide 4s linear infinite; }
@keyframes slide { 0%{left:-100%;} 100%{left:100%;} }
h2 { color:#FFD700; font-size:17px; margin-bottom:18px; text-align:center; }
.service-tabs { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-bottom:20px; }
.svc-btn { padding:14px 8px; border-radius:15px; background:rgba(255,255,255,.05); border:2px solid rgba(255,215,0,.15); color:#aaa; font-weight:700; cursor:pointer; transition:.3s; text-align:center; font-size:13px; }
.svc-btn:hover { border-color:#FFD700; }
.svc-btn.active { background:linear-gradient(135deg,rgba(255,215,0,.25),rgba(184,134,11,.25)); color:#FFD700; border-color:#FFD700; }
.inp { margin-bottom:15px; }
.inp label { display:block; color:#FFD700; font-size:13px; margin-bottom:8px; font-weight:600; }
.inp input { width:100%; padding:15px 18px; background:rgba(0,0,0,.4); border:1px solid rgba(255,215,0,.2); border-radius:12px; color:#fff; font-size:15px; }
.inp input:focus { border-color:#FFD700; outline:none; }
.inp input::placeholder { color:#666; }
.btn { width:100%; padding:16px; background:linear-gradient(135deg,#B8860B,#FFD700,#B8860B); background-size:200% 200%; border:none; border-radius:12px; color:#0a0a0f; font-size:17px; font-weight:900; cursor:pointer; font-family:'Cairo',sans-serif; animation:shine 3s linear infinite; transition:.3s; }
.btn:hover { transform:translateY(-2px); }
.btn:disabled { opacity:.5; cursor:not-allowed; }
.msg { margin-top:15px; padding:15px; border-radius:12px; text-align:center; font-weight:700; display:none; font-size:14px; }
.msg-ok { background:rgba(40,167,69,.15); color:#4ade80; border:1px solid #4ade80; }
.msg-err { background:rgba(220,53,69,.15); color:#ff4b4b; border:1px solid #ff4b4b; }
.loading { display:inline-block; width:18px; height:18px; border:2px solid rgba(0,0,0,.2); border-top-color:#0a0a0f; border-radius:50%; animation:spin 1s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.footer { text-align:center; color:#555; font-size:12px; padding:20px; }
.footer .gold { color:#FFD700; font-weight:700; }
.footer a { color:#FFD700; text-decoration:none; }
</style>
</head>
<body>
<div class="stars" id="stars"></div>
<div class="container">
    <div class="hero">
        <div class="crown">👑</div>
        <h1 class="owner-name">{{ owner }}</h1>
        <div class="divider"><span>✦</span></div>
        <p class="subtitle">🎁 رشق مجاني — بدون تسجيل، بدون باسورد</p>
    </div>

    <div class="card">
        <h2>اختر نوع الرشق 👇</h2>
        <div class="service-tabs" id="svcTabs">
            <div class="svc-btn active" data-type="tiktok_views" onclick="setSvc('tiktok_views', this)">👁️ تيك توك مشاهدات</div>
            <div class="svc-btn" data-type="tiktok_likes" onclick="setSvc('tiktok_likes', this)">❤️ تيك توك لايكات</div>
            <div class="svc-btn" data-type="tiktok_followers" onclick="setSvc('tiktok_followers', this)">👥 تيك توك متابعين</div>
            <div class="svc-btn" data-type="tiktok_comments" onclick="setSvc('tiktok_comments', this)">💬 تيك توك تعليقات</div>
            <div class="svc-btn" data-type="instagram_views" onclick="setSvc('instagram_views', this)">📸 انستا مشاهدات</div>
            <div class="svc-btn" data-type="telegram_views" onclick="setSvc('telegram_views', this)">📢 تليجرام مشاهدات</div>
            <div class="svc-btn" data-type="youtube_views" onclick="setSvc('youtube_views', this)">▶️ يوتيوب مشاهدات</div>
            <div class="svc-btn" data-type="twitter_views" onclick="setSvc('twitter_views', this)">🐦 تويتر مشاهدات</div>
            <div class="svc-btn" data-type="facebook_views" onclick="setSvc('facebook_views', this)">📘 فيسبوك مشاهدات</div>
        </div>

        <div class="inp">
            <label id="linkLabel">🔗 رابط الفيديو</label>
            <input type="text" id="linkInput" placeholder="https://www.tiktok.com/@user/video/...">
        </div>

        <button class="btn" id="sendBtn" onclick="sendOrder()">🚀 إرسال الطلب</button>

        <div class="msg" id="msg"></div>
    </div>

    <div class="footer">
        صنع بكل <span style="color:#ff4b4b;">❤</span> بواسطة <span class="gold">{{ owner }}</span><br>
        <a href="{{ channel }}" target="_blank">📢 قناتنا</a>
    </div>
</div>

<script>
const starsC = document.getElementById('stars');
for (let i = 0; i < 80; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    s.style.left = Math.random() * 100 + '%';
    s.style.top = Math.random() * 100 + '%';
    s.style.animationDelay = Math.random() * 3 + 's';
    starsC.appendChild(s);
}
let currentService = 'tiktok_views';
const labels = {
    tiktok_views: '🔗 رابط الفيديو',
    tiktok_likes: '🔗 رابط الفيديو',
    tiktok_comments: '🔗 رابط الفيديو',
    tiktok_followers: '👤 يوزر تيك توك (@username)',
    instagram_views: '🔗 رابط الريلز/البوست',
    telegram_views: '🔗 رابط المنشور',
    youtube_views: '🔗 رابط الفيديو',
    twitter_views: '🔗 رابط التغريدة',
    facebook_views: '🔗 رابط الفيديو/البوست'
};
function setSvc(type, el) {
    currentService = type;
    document.querySelectorAll('.svc-btn').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('linkLabel').textContent = labels[type];
    const inp = document.getElementById('linkInput');
    inp.placeholder = type === 'tiktok_followers' ? '@username أو https://tiktok.com/@user' : 'https://...';
    inp.value = '';
}
async function sendOrder() {
    const btn = document.getElementById('sendBtn');
    const msg = document.getElementById('msg');
    const link = document.getElementById('linkInput').value.trim();
    if (!link) return show('❌ حط الرابط الأول', 'err');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> جاري الإرسال...';
    msg.style.display = 'none';
    try {
        const r = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: currentService, link: link })
        });
        const d = await r.json();
        if (d.success) {
            show('✅ ' + d.message, 'ok');
            document.getElementById('linkInput').value = '';
        } else {
            show('❌ ' + (d.message || 'فشل الإرسال'), 'err');
        }
    } catch (e) {
        show('❌ خطأ: ' + e.message, 'err');
    }
    btn.disabled = false;
    btn.innerHTML = '🚀 إرسال الطلب';
}
function show(text, type) {
    const msg = document.getElementById('msg');
    msg.textContent = text;
    msg.className = 'msg msg-' + type;
    msg.style.display = 'block';
}
</script>
</body>
</html>
"""


@app.route('/')
def home():
    return render_template_string(HTML, owner=OWNER_NAME, channel=CHANNEL_LINK)


@app.route('/api/order', methods=['POST'])
def api_order():
    data = request.get_json() or {}
    service = data.get('type', 'tiktok_views')
    link = (data.get('link') or '').strip()

    if not link:
        return jsonify({'success': False, 'message': 'حط الرابط'})

    try:
        ok, msg = zefame_execute(service, link)
        if ok:
            return jsonify({'success': True, 'message': msg})
        if not USE_TIKSPARK:
            return jsonify({'success': False, 'message': msg})
    except Exception as e:
        if not USE_TIKSPARK:
            return jsonify({'success': False, 'message': f'خطأ: {str(e)}'})

    if USE_TIKSPARK:
        if not TS_USER_TOKEN:
            if not ts_login():
                return jsonify({'success': False, 'message': 'فشل تسجيل دخول السيرفر الاحتياطي'})

        ts_map = {
            'tiktok_views': 'views',
            'tiktok_likes': 'likes',
            'tiktok_followers': 'followers',
            'tiktok_comments': 'comments'
        }
        ts_type = ts_map.get(service)
        if not ts_type:
            return jsonify({'success': False, 'message': 'الخدمة غير متاحة في السيرفر الاحتياطي'})

        try:
            if ts_type == 'followers':
                result = ts_create_order('followers', 10, username=extract_username(link) or link.replace('@',''))
            else:
                result = ts_create_order(ts_type, 10, video_link=link)
            if result and 'errors' not in result:
                return jsonify({'success': True, 'message': 'تم الإرسال عبر السيرفر الاحتياطي ✅'})
            return jsonify({'success': False, 'message': 'فشل السيرفر الاحتياطي'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    return jsonify({'success': False, 'message': 'فشل'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'🌐 الموقع شغال على: http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port)