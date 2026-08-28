from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import instaloader
import time
import random
import hashlib
import json
import os
import secrets
from datetime import datetime
from instaloader import Instaloader, Profile
import traceback

# ============================================================
# FIREBASE - USE THIS INSTEAD OF FILE SYSTEM
# ============================================================
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
# CONFIGURATION
# ============================================================
CONFIG = {
    "admin_username": "ANSHAFT127987",
    "admin_password": "ANSHAFTAK47",
    "version": "3.0.0",
    "api_status": "online",
    "maintenance": False
}

# ============================================================
# API KEYS & USERS
# ============================================================
USERS = {
    "ANSHAFT127987": {
        "api_key": "ANSHAFTAK472026",
        "plan": "owner",
        "status": "active",
        "per_minute": 10000,
        "per_day": 100000
    },
    "DEMO_USER": {
        "api_key": "DEMOFUCK",
        "plan": "user",
        "status": "active",
        "per_minute": 100,
        "per_day": 1000
    }
}

# ============================================================
# RATE LIMITING (IN-MEMORY)
# ============================================================
rate_limit_data = {}

def check_rate_limit(api_key, per_minute, per_day):
    now = time.time()
    if api_key not in rate_limit_data:
        rate_limit_data[api_key] = {
            'minute_count': 0,
            'day_count': 0,
            'minute_reset': now,
            'day_reset': now
        }
    
    data = rate_limit_data[api_key]
    
    if now - data['minute_reset'] > 60:
        data['minute_count'] = 0
        data['minute_reset'] = now
    
    if now - data['day_reset'] > 86400:
        data['day_count'] = 0
        data['day_reset'] = now
    
    if data['minute_count'] >= per_minute:
        return False, f"Rate limit exceeded. {per_minute} requests per minute"
    
    if data['day_count'] >= per_day:
        return False, f"Rate limit exceeded. {per_day} requests per day"
    
    data['minute_count'] += 1
    data['day_count'] += 1
    
    return True, "OK"

# ============================================================
# FIREBASE INIT
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

init_firebase()

# ============================================================
# DEVICE FINGERPRINTS
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
                'cpu_cores': 8, 'memory': '16 GB', 'gpu': 'NVIDIA GeForce RTX 3060'
            },
            {
                'id': 2, 'country': 'UK', 'timezone': 'Europe/London',
                'utc_offset': 'UTC+0:00', 'language': 'en-GB',
                'browser': {'name': 'Firefox', 'version': '121.0',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'},
                'screen': {'width': 2560, 'height': 1440}, 'platform': 'Windows',
                'cpu_cores': 12, 'memory': '32 GB', 'gpu': 'AMD Radeon RX 6800 XT'
            },
            {
                'id': 3, 'country': 'India', 'timezone': 'Asia/Kolkata',
                'utc_offset': 'UTC+5:30', 'language': 'en-IN',
                'browser': {'name': 'Chrome', 'version': '119.0.6045.199',
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'},
                'screen': {'width': 1680, 'height': 1050}, 'platform': 'Darwin',
                'cpu_cores': 10, 'memory': '16 GB', 'gpu': 'Apple M2 GPU'
            },
            {
                'id': 4, 'country': 'Japan', 'timezone': 'Asia/Tokyo',
                'utc_offset': 'UTC+9:00', 'language': 'ja-JP',
                'browser': {'name': 'Edge', 'version': '120.0.2210.121',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'},
                'screen': {'width': 3840, 'height': 2160}, 'platform': 'Windows',
                'cpu_cores': 16, 'memory': '64 GB', 'gpu': 'NVIDIA GeForce RTX 4090'
            },
            {
                'id': 5, 'country': 'Germany', 'timezone': 'Europe/Berlin',
                'utc_offset': 'UTC+1:00', 'language': 'de-DE',
                'browser': {'name': 'Firefox', 'version': '122.0',
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:122.0) Gecko/20100101 Firefox/122.0'},
                'screen': {'width': 1440, 'height': 900}, 'platform': 'Darwin',
                'cpu_cores': 8, 'memory': '16 GB', 'gpu': 'Apple M3 GPU'
            },
            {
                'id': 6, 'country': 'Australia', 'timezone': 'Australia/Sydney',
                'utc_offset': 'UTC+11:00', 'language': 'en-AU',
                'browser': {'name': 'Chrome', 'version': '121.0.6167.85',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'},
                'screen': {'width': 1366, 'height': 768}, 'platform': 'Windows',
                'cpu_cores': 6, 'memory': '8 GB', 'gpu': 'Intel Iris Xe Graphics'
            },
            {
                'id': 7, 'country': 'Brazil', 'timezone': 'America/Sao_Paulo',
                'utc_offset': 'UTC-3:00', 'language': 'pt-BR',
                'browser': {'name': 'Opera', 'version': '106.0.4998.70',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/106.0.0.0'},
                'screen': {'width': 1600, 'height': 900}, 'platform': 'Windows',
                'cpu_cores': 8, 'memory': '16 GB', 'gpu': 'AMD Radeon RX 7900 XTX'
            },
            {
                'id': 8, 'country': 'UAE', 'timezone': 'Asia/Dubai',
                'utc_offset': 'UTC+4:00', 'language': 'ar-SA',
                'browser': {'name': 'Safari', 'version': '17.1',
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'},
                'screen': {'width': 2560, 'height': 1600}, 'platform': 'Darwin',
                'cpu_cores': 12, 'memory': '32 GB', 'gpu': 'Apple M3 Max GPU'
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
            'Referer': 'https://www.google.com/'
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
                max_connection_attempts=3,
                request_timeout=30,
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
        
        try:
            if not self.initialize_loader():
                return {'status': 'error', 'error': 'Failed to initialize Instagram loader'}
            
            profile = Profile.from_username(self.loader.context, username)
            fp = self.fingerprint.current_fingerprint
            response_time = (time.time() - start_time) * 1000
            
            result = {
                "status": "ok",
                "collected_at": datetime.now().isoformat(),
                "profile": {
                    "id": str(profile.userid),
                    "username": profile.username,
                    "full_name": profile.full_name if profile.full_name else 'N/A',
                    "biography": profile.biography[:200] if profile.biography else 'No bio available',
                    "is_private": profile.is_private,
                    "is_verified": profile.is_verified,
                    "is_business_account": profile.is_business_account,
                    "is_professional_account": hasattr(profile, 'is_professional_account') and profile.is_professional_account,
                    "category_name": getattr(profile, 'category_name', None),
                    "business_category_name": getattr(profile, 'business_category_name', None),
                    "profile_pic_url_hd": getattr(profile, 'profile_pic_url_hd', None) or getattr(profile, 'profile_pic_url', None),
                    "external_url": profile.external_url if profile.external_url else None,
                    "followers": profile.followers,
                    "following": profile.followees,
                    "posts": profile.mediacount,
                    "account_creation_year": 2012
                },
                "USERNAME": "@KINGFFAIAK47x",
                "MADE_BY": "ANSH AFT"
            }
            
            return result
            
        except instaloader.exceptions.ProfileNotExistsException:
            return {'status': 'error', 'error': f'Profile @{username} does not exist', 'code': 'INVALID_USER'}
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            return {'status': 'error', 'error': f'Profile @{username} is private', 'code': 'PRIVATE_ACCOUNT'}
        except Exception as e:
            if "401" in str(e):
                time.sleep(2)
                return self.scan_profile(username)
            else:
                return {'status': 'error', 'error': str(e)[:100], 'code': 'SCAN_ERROR'}

scanner = InstagramScanner()

# ============================================================
# VALIDATE API KEY
# ============================================================
def validate_api_key(api_key):
    if not api_key:
        return None, "API key required. Use ?api_key=YOUR_KEY"
    
    for username, user_data in USERS.items():
        if user_data.get('api_key') == api_key:
            if user_data.get('status') == 'suspended':
                return None, "Account suspended"
            return user_data, username
    
    return None, "Invalid API key"

# ============================================================
# ROUTES - STATIC FILES
# ============================================================
@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/dashboard')
def dashboard_page():
    username = request.args.get('username')
    password = request.args.get('password')
    
    if username and password:
        if username == CONFIG['admin_username'] and password == CONFIG['admin_password']:
            return send_from_directory('.', 'dashboard.html')
        else:
            return redirect('/login?error=Invalid credentials')
    
    return redirect('/login?error=Please login first')

@app.route('/')
def home():
    return send_from_directory('.', 'login.html')

# ============================================================
# API: ADMIN LOGIN - FIXED 404 ERROR
# ============================================================
@app.route('/api/admin/login', methods=['POST', 'OPTIONS'])
def admin_login():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if username == CONFIG['admin_username'] and password == CONFIG['admin_password']:
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'username': username,
            'redirect': '/dashboard?username=' + username + '&password=' + password,
            'developer': 'KINGFFAIAK47x',
            'owner': 'ANSH_AFT'
        })
    else:
        if FIREBASE_READY and db:
            try:
                db.reference('failed_logins').push({
                    'username': username,
                    'timestamp': datetime.now().isoformat(),
                    'ip': request.remote_addr
                })
            except:
                pass
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

# ============================================================
# API: SCAN PROFILE - FIXED 403 ERROR
# ============================================================
@app.route('/api/scan', methods=['GET'])
def scan_profile_get():
    start_time = time.time()
    
    if CONFIG.get('maintenance', False):
        return jsonify({
            'status': 'error',
            'error': 'API Under Maintenance',
            'message': 'We are currently upgrading our systems.',
            'contact': '@KINGFFAIAK47x'
        }), 503
    
    if CONFIG.get('api_status') == 'offline':
        return jsonify({
            'status': 'error',
            'error': 'API Offline',
            'message': 'API is currently disabled.',
            'contact': '@KINGFFAIAK47x'
        }), 503
    
    # Get API key from query - FIXED
    api_key = request.args.get('api_key', '').strip()
    
    user_data, username = validate_api_key(api_key)
    if not user_data:
        return jsonify({
            'status': 'error',
            'code': 'INVALID_KEY',
            'error': 'Invalid API key',
            'message': 'The API key provided is not valid',
            'support': 'https://t.me/KINGFFAIAK47x'
        }), 403
    
    per_minute = user_data.get('per_minute', 100)
    per_day = user_data.get('per_day', 1000)
    allowed, msg = check_rate_limit(api_key, per_minute, per_day)
    
    if not allowed:
        return jsonify({
            'status': 'error',
            'code': 'RATE_LIMIT',
            'error': msg,
            'plan': user_data.get('plan', 'user')
        }), 429
    
    username_param = request.args.get('username', '').strip()
    
    if not username_param:
        return jsonify({
            'status': 'error',
            'code': 'NO_USERNAME',
            'error': 'Username required',
            'message': 'Please provide username parameter',
            'example': '/api/scan?username=instagram&api_key=DEMOFUCK'
        }), 400
    
    # Scan with timeout handling
    try:
        result = scanner.scan_profile(username_param)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'code': 'SCAN_ERROR'
        }), 500
    
    if FIREBASE_READY and db and result.get('status') == 'ok':
        try:
            db.reference('logs').push({
                'api_key': api_key[:16] + '...',
                'username': username_param,
                'success': True,
                'response_time': (time.time() - start_time) * 1000,
                'timestamp': datetime.now().isoformat()
            })
        except:
            pass
    
    if result.get('status') == 'ok':
        result['api_key_used'] = api_key[:16] + '...'
        result['plan'] = user_data.get('plan', 'user')
        result['limit_minute'] = per_minute
        result['limit_day'] = per_day
        result['remaining_minute'] = per_minute - rate_limit_data.get(api_key, {}).get('minute_count', 0)
        result['remaining_day'] = per_day - rate_limit_data.get(api_key, {}).get('day_count', 0)
        result['developer'] = '@KINGFFAIAK47x'
        result['owner'] = 'ANSH AFT'
        result['response_time_ms'] = (time.time() - start_time) * 1000
    
    return jsonify(result)

# ============================================================
# API: HEALTH
# ============================================================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'running',
        'firebase_connected': FIREBASE_READY,
        'timestamp': datetime.now().isoformat(),
        'service': 'Instagram Scanner API',
        'version': CONFIG.get('version', '3.0.0'),
        'developer': 'KINGFFAIAK47x',
        'owner': 'ANSH_AFT',
        'api_status': CONFIG.get('api_status', 'online')
    })

# ============================================================
# API: STATUS
# ============================================================
@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        'status': CONFIG.get('api_status', 'online'),
        'version': CONFIG.get('version', '3.0.0'),
        'maintenance': CONFIG.get('maintenance', False),
        'total_users': len(USERS),
        'timestamp': datetime.now().isoformat(),
        'developer': 'KINGFFAIAK47x',
        'owner': 'ANSH_AFT'
    })

# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    print('='*60)
    print('🔥 INSTAGRAM SCANNER API v3.0')
    print('='*60)
    print(f'👑 Owner: ANSH_AFT')
    print(f'💻 Developer: KINGFFAIAK47x')
    print('='*60)
    print('📊 Dashboard: /dashboard?username=ANSHAFT127987&password=ANSHAFTAK47')
    print('📊 API Scan: /api/scan?username=instagram&api_key=DEMOFUCK')
    print('📊 Health: /api/health')
    print('📊 Status: /api/status')
    print('='*60)
    print('🔑 API Keys:')
    print('   ⭐ Premium: ANSHAFTAK472026')
    print('   🆓 User: DEMOFUCK')
    print('='*60)
    app.run(host='0.0.0.0', port=5000, debug=True)
