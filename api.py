from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import instaloader
import time
import random
import hashlib
import json
import os
import secrets
import platform
import re
from datetime import datetime
from pathlib import Path
from instaloader import Instaloader, Profile
import traceback

try:
    import firebase_admin
    from firebase_admin import credentials, db as firebase_db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase not installed")

app = Flask(__name__, static_folder='.')
CORS(app)

# ============================================================
# DEVELOPER & OWNER INFO
# ============================================================
DEVELOPER = {
    "name": "KINGFFAIAK47x",
    "telegram": "https://t.me/KINGFFAIAK47x",
    "channel": "https://t.me/+iDnVRYTDnAJmNDE1",
    "backup_channel": "https://t.me/+aWlMH56c06ZiZTE1"
}

OWNER = {
    "name": "ANSH_AFT",
    "telegram": "https://t.me/ANSH_AFT"
}

# ============================================================
# ADMIN CREDENTIALS
# ============================================================
ADMIN = {
    "username": "ANSHAFT127987",
    "password": "ANSHAFTAK47"
}

# ============================================================
# API KEYS
# ============================================================
API_KEYS = {
    "premium": "ANSHAFTAK47",
    "user": "DEMOFUCK"
}

# ============================================================
# FIREBASE INIT - YOUR CREDENTIALS DIRECTLY
# ============================================================
db = None
FIREBASE_READY = False

def init_firebase():
    global db, FIREBASE_READY
    
    if not FIREBASE_AVAILABLE:
        return False
    
    try:
        if firebase_admin._apps:
            db = firebase_db
            FIREBASE_READY = True
            return True
        
        # YOUR FIREBASE CREDENTIALS - DIRECTLY PASTED
        cred_dict = {
            "type": "service_account",
            "project_id": "ansh-aft",
            "private_key_id": "54a495a8815a68f488b2e97a627b3768561f9730",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDAdBVfG2zWAgnP\n0LK4OCxjHWGA7Elcojb4//8/KMuuvUUZDZ1xxn6Wm1T1+ILWMvvbVZs4iCPsK9+e\n7mhIsNGWD3EtbIRPXCkpnBRJ7KZ8dm0kIgI1L7WG8NQYY9/hBUJkw9ZptWpg2TaN\nAVWjbfWpqx+O4nieeKd3kzyTl1C5zNaZvde2lVCcHavQvfyfkTDsW5I9XIsnUZsu\n3A+jQFNSFqwfbufxCTSvjI09hYV/GGp8BP7eoLgcx+IXPRJAGfx3jab2wtPMERWs\nLDDcWdXbH9BiZHvG7UiyBSVPopx73zUZ5bO3gzbuWIHeP3s71X9Fo5g/CYvbxfEY\nyNcA7EktAgMBAAECgf9OLtp/yKRuTGWwBxiTvj5KBaWWumcTOtMaVOVcwzX7xuhL\nRTyw+/JxPKlHQ63jVtL6R8zHKodtamVuK2wyG6MJUzynN26Izufp/34+ieUYqwOr\nqiU7diZIq41+WxSYVYqjZOu2Bf0xWwzOO7yOqB0k0GABq/9UYa+m5Cm3y8D/uYLF\nYE38hs40kupIxCDV32AYRg37xKO/qlXyYTn+2aNVtSYbxkq0zwAnwnsyYlBe4J8X\nazlhAWNO6d2G9y7JSEaKooOVPNeqw2NZPtwK+ebu1LRQIP8iaCr+CSuFdZ3srdaA\nIW/1EJf5aXgKKsdYWoonQeqxTyNLDyZx+FD/TgECgYEA7ASDHZUXzamix9vmG1Gk\nR/MOc4ZPu8IyVrgCqs0lJfKiMr/sOPnpvrULH+q08ixiH4waxLqqCE+VmSUPpVhu\n1Th3/lC4G+7gmomdi/HLbBuJRVchEtjsc/d88O6wFPCXEWTxByZSzGwf2HTY65Vq\nhZa5+/9eObeRJsHbFWB7nh0CgYEA0L9aingPQSU9Dibbyat2PL8WmSi3lYHo5+Fl\nRl/DdsOG+dNkKNvMfXO2A5WboDwWT+/Q1bcXQrjDFqFc6JfBJ64TD39Ev3uyzo1O\nIb6nKfjcW+usfm94s770HNp5kugXfld+rFnMmS6D4OpL7mOhaap9IUtrvPdp2lQr\n4bUQqlECgYEAj9IwE9bGqoy0pRVbI0qc0TtLkxpFfCTah/2ZontgJ7+zFzncuNuR\nlKS+IrTjjq99G7xEk50r/+R/RNNQtXEuGMBQXqjRiDQIqiMx3hV54GbnP1nYzaNi\nc0hc2nSY2CnD5NWeCr1Pt0IsJbsOdICYaM9whh8XTBSQXw3Cc0RYEAECgYEAi7Vm\nDYKpAvq/UDdlpiWhbqqdn0gHBoL5tCfANkdldJkMPyvhvw7MX7IPwXphu+47KKji\nZgayBK/PsdexbOIUHlB85URSaK2LUH52KlOFYavzH3ot6jkE2ZgVnTIDZ/T5tE8u\nsn8vVd4x2Vg2FYiMwUGfmab2pnQYXk0zSU57puECgYBdxuwP43Iu3rYXkImm/AtF\nlaUNUDCLxvhZCqMaqfSWcapPrTswCq47fQCEVloRSS6j0i8za1mHqPr6Eum8MHOA\nWEc5Rh6BrHjdlF7TdK8HOJJVc744HgGaXl6s/3Gu9go+iKvm8m1QjOF7pm2VRs5o\ndNo69GveqJ+h1FWs8H5gDw==\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-fbsvc@ansh-aft.iam.gserviceaccount.com",
            "client_id": "116996985410373827841",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40ansh-aft.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://ansh-aft-default-rtdb.firebaseio.com'
        })
        
        db = firebase_db
        FIREBASE_READY = True
        print("🔥 Firebase initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Firebase init error: {e}")
        return False

# Initialize Firebase
init_firebase()

# ============================================================
# 8 REAL DEVICE FINGERPRINTS
# ============================================================
class UltimateDeviceFingerprint:
    def __init__(self):
        self.generation_count = 0
        self.fingerprint_list = self._create_fingerprints()
        self.current_fingerprint = None
        self._get_next_fingerprint()
    
    def _create_fingerprints(self):
        return [
            {
                'id': 1, 'country': 'USA', 'timezone': 'America/New_York', 
                'utc_offset': 'UTC-5:00', 'language': 'en-US',
                'browser': {'name': 'Chrome', 'version': '120.0.6099.109',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
                'screen': {'width': 1920, 'height': 1080}, 'platform': 'Windows',
                'cpu_cores': 8, 'memory': '16 GB', 'gpu': 'NVIDIA GeForce RTX 3060',
                'canvas_hash': 'a7f8e9d1c3b5a6f8', 'webgl_hash': 'b8c9d0e2f4a6b7c9'
            },
            {
                'id': 2, 'country': 'UK', 'timezone': 'Europe/London',
                'utc_offset': 'UTC+0:00', 'language': 'en-GB',
                'browser': {'name': 'Firefox', 'version': '121.0',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'},
                'screen': {'width': 2560, 'height': 1440}, 'platform': 'Windows',
                'cpu_cores': 12, 'memory': '32 GB', 'gpu': 'AMD Radeon RX 6800 XT',
                'canvas_hash': 'b8c9d0e2f4a6b7c9', 'webgl_hash': 'c9d0e1f3a5b7c8d0'
            },
            {
                'id': 3, 'country': 'India', 'timezone': 'Asia/Kolkata',
                'utc_offset': 'UTC+5:30', 'language': 'en-IN',
                'browser': {'name': 'Chrome', 'version': '119.0.6045.199',
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'},
                'screen': {'width': 1680, 'height': 1050}, 'platform': 'Darwin',
                'cpu_cores': 10, 'memory': '16 GB', 'gpu': 'Apple M2 GPU',
                'canvas_hash': 'c9d0e1f3a5b7c8d0', 'webgl_hash': 'd0e1f2a4b6c8d9e0'
            },
            {
                'id': 4, 'country': 'Japan', 'timezone': 'Asia/Tokyo',
                'utc_offset': 'UTC+9:00', 'language': 'ja-JP',
                'browser': {'name': 'Edge', 'version': '120.0.2210.121',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'},
                'screen': {'width': 3840, 'height': 2160}, 'platform': 'Windows',
                'cpu_cores': 16, 'memory': '64 GB', 'gpu': 'NVIDIA GeForce RTX 4090',
                'canvas_hash': 'd0e1f2a4b6c8d9e0', 'webgl_hash': 'e1f2a3b5c7d9e0f1'
            },
            {
                'id': 5, 'country': 'Germany', 'timezone': 'Europe/Berlin',
                'utc_offset': 'UTC+1:00', 'language': 'de-DE',
                'browser': {'name': 'Firefox', 'version': '122.0',
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:122.0) Gecko/20100101 Firefox/122.0'},
                'screen': {'width': 1440, 'height': 900}, 'platform': 'Darwin',
                'cpu_cores': 8, 'memory': '16 GB', 'gpu': 'Apple M3 GPU',
                'canvas_hash': 'e1f2a3b5c7d9e0f1', 'webgl_hash': 'f2a3b4c6d8e0f1a2'
            },
            {
                'id': 6, 'country': 'Australia', 'timezone': 'Australia/Sydney',
                'utc_offset': 'UTC+11:00', 'language': 'en-AU',
                'browser': {'name': 'Chrome', 'version': '121.0.6167.85',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'},
                'screen': {'width': 1366, 'height': 768}, 'platform': 'Windows',
                'cpu_cores': 6, 'memory': '8 GB', 'gpu': 'Intel Iris Xe Graphics',
                'canvas_hash': 'f2a3b4c6d8e0f1a2', 'webgl_hash': 'a3b4c5d7e9f0a1b2'
            },
            {
                'id': 7, 'country': 'Brazil', 'timezone': 'America/Sao_Paulo',
                'utc_offset': 'UTC-3:00', 'language': 'pt-BR',
                'browser': {'name': 'Opera', 'version': '106.0.4998.70',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/106.0.0.0'},
                'screen': {'width': 1600, 'height': 900}, 'platform': 'Windows',
                'cpu_cores': 8, 'memory': '16 GB', 'gpu': 'AMD Radeon RX 7900 XTX',
                'canvas_hash': 'a3b4c5d7e9f0a1b2', 'webgl_hash': 'b4c5d6e8f0a1b2c3'
            },
            {
                'id': 8, 'country': 'UAE', 'timezone': 'Asia/Dubai',
                'utc_offset': 'UTC+4:00', 'language': 'ar-SA',
                'browser': {'name': 'Safari', 'version': '17.1',
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'},
                'screen': {'width': 2560, 'height': 1600}, 'platform': 'Darwin',
                'cpu_cores': 12, 'memory': '32 GB', 'gpu': 'Apple M3 Max GPU',
                'canvas_hash': 'b4c5d6e8f0a1b2c3', 'webgl_hash': 'c5d6e7f9a1b2c3d4'
            }
        ]
    
    def _get_next_fingerprint(self):
        self.generation_count += 1
        index = (self.generation_count - 1) % len(self.fingerprint_list)
        self.current_fingerprint = self.fingerprint_list[index].copy()
        self.current_fingerprint['generation'] = self.generation_count
        self.current_fingerprint['fingerprint_id'] = hashlib.md5(
            str(time.time() + random.random() + self.generation_count).encode()
        ).hexdigest()[:24]
        return self.current_fingerprint
    
    def get_fingerprint(self):
        return self._get_next_fingerprint()
    
    def get_headers(self):
        fp = self.get_fingerprint()
        return {
            'User-Agent': fp['browser']['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': f"{fp['language']},en;q=0.9",
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-GPC': '1',
            'Referer': 'https://www.google.com/',
            'Sec-Ch-Ua': f'"{fp["browser"]["name"]}"; v="{fp["browser"]["version"].split(".")[0]}"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': f'"{fp["platform"]}"'
        }

# ============================================================
# INSTAGRAM SCANNER CLASS
# ============================================================
class InstagramScanner:
    def __init__(self):
        self.fingerprint = UltimateDeviceFingerprint()
        self.loader = None
    
    def initialize_loader(self):
        try:
            fp = self.fingerprint.get_fingerprint()
            user_agent = fp['browser']['user_agent']
            
            self.loader = Instaloader(
                max_connection_attempts=5,
                request_timeout=45,
                user_agent=user_agent,
                sleep=True,
                quiet=True
            )
            
            if hasattr(self.loader, 'context') and hasattr(self.loader.context, '_session'):
                headers = self.fingerprint.get_headers()
                for key, value in headers.items():
                    self.loader.context._session.headers.update({key: value})
            
            return True
            
        except Exception as e:
            print(f"Loader init error: {e}")
            return False
    
    def scan_profile(self, username):
        start_time = time.time()
        result = {}
        
        try:
            if not self.initialize_loader():
                return {'error': 'Failed to initialize Instagram loader'}
            
            profile = Profile.from_username(self.loader.context, username)
            fp = self.fingerprint.current_fingerprint
            response_time = (time.time() - start_time) * 1000
            
            result = {
                'status': 'success',
                'username': profile.username,
                'user_id': profile.userid,
                'full_name': profile.full_name if profile.full_name else 'N/A',
                'biography': profile.biography[:200] if profile.biography else 'No bio',
                'external_url': profile.external_url if profile.external_url else 'None',
                'followers': profile.followers,
                'following': profile.followees,
                'total_posts': profile.mediacount,
                'is_private': profile.is_private,
                'is_verified': profile.is_verified,
                'is_business': profile.is_business_account,
                'response_time_ms': round(response_time, 0),
                'scraped_at': datetime.now().isoformat(),
                'developer': 'KINGFFAIAK47x',
                'owner': 'ANSH_AFT',
                'telegram_channel': 'https://t.me/+iDnVRYTDnAJmNDE1',
                'backup_channel': 'https://t.me/+aWlMH56c06ZiZTE1',
                'device_fingerprint': {
                    'id': fp['id'],
                    'country': fp['country'],
                    'timezone': fp['timezone'],
                    'platform': fp['platform'],
                    'browser': fp['browser']['name'],
                    'browser_version': fp['browser']['version'],
                    'screen': f"{fp['screen']['width']}x{fp['screen']['height']}",
                    'cpu_cores': fp['cpu_cores'],
                    'memory': fp['memory'],
                    'gpu': fp['gpu']
                }
            }
            
            return result
            
        except instaloader.exceptions.ProfileNotExistsException:
            return {'status': 'error', 'error': f'❌ Profile @{username} does not exist', 'code': 'INVALID_USER'}
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            return {'status': 'error', 'error': f'🔒 Profile @{username} is private', 'code': 'PRIVATE_ACCOUNT'}
        except Exception as e:
            if "401" in str(e):
                time.sleep(2)
                return self.scan_profile(username)
            else:
                return {'status': 'error', 'error': str(e)[:100], 'code': 'SCAN_ERROR'}

scanner = InstagramScanner()

# ============================================================
# ROUTES
# ============================================================

@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/dashboard')
def dashboard_page():
    return send_from_directory('.', 'dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return jsonify({'error': 'File not found'}), 404

@app.route('/')
def home():
    return send_from_directory('.', 'login.html')

# ============================================================
# API: HEALTH CHECK
# ============================================================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'running',
        'firebase_connected': FIREBASE_READY,
        'timestamp': datetime.now().isoformat(),
        'service': 'Instagram Scanner API',
        'version': '2.0.0',
        'developer': 'KINGFFAIAK47x',
        'owner': 'ANSH_AFT',
        'telegram': 'https://t.me/+iDnVRYTDnAJmNDE1',
        'backup': 'https://t.me/+aWlMH56c06ZiZTE1',
        'api_keys': {
            'premium': 'ANSHAFTAK47',
            'user': 'DEMOFUCK'
        },
        'admin': {
            'username': 'ANSHAFT127987'
        }
    })

# ============================================================
# API: ADMIN LOGIN
# ============================================================
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if username == ADMIN['username'] and password == ADMIN['password']:
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'username': username,
            'redirect': '/dashboard',
            'developer': 'KINGFFAIAK47x',
            'owner': 'ANSH_AFT'
        })
    else:
        if FIREBASE_READY and db:
            db.reference('failed_logins').push({
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'ip': request.remote_addr
            })
        return jsonify({
            'status': 'error',
            'error': '❌ Invalid credentials'
        }), 401

# ============================================================
# API: SCAN PROFILE
# ============================================================
@app.route('/api/scan', methods=['POST'])
def scan_profile():
    start_time = time.time()
    
    # Get API key
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'status': 'error', 'error': '❌ API key required', 'code': 'NO_API_KEY'}), 401
    
    # Check API keys
    plan = 'free'
    limit = 1000
    
    if api_key == API_KEYS['premium']:
        plan = 'premium'
        limit = 10000
    elif api_key == API_KEYS['user']:
        plan = 'free'
        limit = 1000
    else:
        # Check Firebase for custom keys
        if FIREBASE_READY and db:
            users_ref = db.reference('users')
            users = users_ref.get()
            user = None
            if users:
                for uid, data in users.items():
                    if data.get('api_key') == api_key:
                        user = data
                        plan = user.get('plan', 'free')
                        limit = 10000 if plan == 'premium' else 1000
                        break
            
            if not user:
                return jsonify({'status': 'error', 'error': '❌ Invalid API key', 'code': 'INVALID_KEY'}), 401
            
            if user.get('active') == False:
                return jsonify({'status': 'error', 'error': '⛔ Account disabled', 'code': 'ACCOUNT_DISABLED'}), 403
        else:
            return jsonify({'status': 'error', 'error': '❌ Invalid API key', 'code': 'INVALID_KEY'}), 401
    
    # Get username
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({'status': 'error', 'error': '❌ Username required', 'code': 'NO_USERNAME'}), 400
    
    username = data['username'].strip()
    if not username:
        return jsonify({'status': 'error', 'error': '❌ Username cannot be empty', 'code': 'EMPTY_USERNAME'}), 400
    
    # Scan profile
    result = scanner.scan_profile(username)
    
    # Log request
    if FIREBASE_READY and db:
        db.reference('logs').push({
            'api_key': api_key[:16] + '...',
            'username': username,
            'success': result.get('status') == 'success',
            'response_time': (time.time() - start_time) * 1000,
            'timestamp': datetime.now().isoformat()
        })
    
    # Add metadata
    result['plan'] = plan
    result['limit_total'] = limit
    result['api_key'] = api_key[:16] + '...'
    result['developer'] = 'KINGFFAIAK47x'
    result['owner'] = 'ANSH_AFT'
    result['telegram_channel'] = 'https://t.me/+iDnVRYTDnAJmNDE1'
    result['backup_channel'] = 'https://t.me/+aWlMH56c06ZiZTE1'
    
    return jsonify(result)

# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    print('='*60)
    print('🔥 INSTAGRAM SCANNER API - PREMIUM')
    print('='*60)
    print(f'👑 Owner: {OWNER["name"]}')
    print(f'💻 Developer: {DEVELOPER["name"]}')
    print(f'📺 Channel: {DEVELOPER["channel"]}')
    print(f'📺 Backup: {DEVELOPER["backup_channel"]}')
    print('='*60)
    print(f'🔑 Admin: {ADMIN["username"]} / {ADMIN["password"]}')
    print(f'⭐ Premium Key: {API_KEYS["premium"]}')
    print(f'🆓 User Key: {API_KEYS["user"]}')
    print(f'🔥 Firebase: {"✅ Connected" if FIREBASE_READY else "❌ Not Connected"}')
    print('='*60)
    print('📊 Admin Panel: /login')
    print('📊 Dashboard: /dashboard')
    print('📊 API Health: /api/health')
    print('📊 API Scan: /api/scan (POST)')
    print('='*60)
    app.run(host='0.0.0.0', port=5000, debug=True)
