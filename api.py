from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import instaloader
import time
import random
import hashlib
import json
import os
import platform
import secrets
from datetime import datetime
from instaloader import Instaloader, Profile
import traceback

# ============================================================
# FIREBASE - OPTIONAL
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
# RATE LIMITING
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
# 8+ REAL DEVICE FINGERPRINTS - ROTATES EVERY REQUEST
# ============================================================

class UltimateDeviceFingerprint:
    def __init__(self):
        self.fingerprint = {}
        self.generation_count = 0
        self.rotation_counter = 0
        self.rotation_interval = 3
        self._generate_fingerprint()
    
    def _generate_fingerprint(self):
        self.generation_count += 1
        self.rotation_counter += 1
        system = platform.system()
        
        browsers = [
            {
                'name': 'Chrome',
                'version': f"{random.randint(110, 122)}.0.{random.randint(6000, 7000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36"
            },
            {
                'name': 'Chrome',
                'version': f"{random.randint(110, 122)}.0.{random.randint(6000, 7000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36"
            },
            {
                'name': 'Firefox', 
                'version': f"{random.randint(115, 124)}.0",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(115, 124)}.0) Gecko/20100101 Firefox/{random.randint(115, 124)}.0"
            },
            {
                'name': 'Firefox',
                'version': f"{random.randint(115, 124)}.0",
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}; rv:{random.randint(115, 124)}.0) Gecko/20100101 Firefox/{random.randint(115, 124)}.0"
            },
            {
                'name': 'Edge',
                'version': f"{random.randint(110, 122)}.0.{random.randint(2000, 3000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36 Edg/{random.randint(110, 122)}.0.0.0"
            },
            {
                'name': 'Safari',
                'version': f"{random.randint(16, 17)}.{random.randint(0, 1)}",
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{random.randint(16, 17)}.0 Safari/605.1.15"
            },
            {
                'name': 'Opera',
                'version': f"{random.randint(90, 106)}.0.{random.randint(4000, 5000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36 OPR/{random.randint(90, 106)}.0.0.0"
            }
        ]
        
        browser = random.choice(browsers)
        screens = [
            (1920, 1080), (2560, 1440), (3840, 2160),
            (1366, 768), (1536, 864), (1440, 900),
            (1600, 900), (1280, 720), (1920, 1200),
            (2560, 1600), (3440, 1440), (1360, 768),
            (1280, 800), (1440, 810), (1680, 1050),
            (1024, 768), (1280, 1024), (1360, 768)
        ]
        width, height = random.choice(screens)
        
        languages = ['en-US', 'en-GB', 'en-IN', 'en-AU', 'en-CA', 
                    'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'pt-BR',
                    'ja-JP', 'ko-KR', 'zh-CN', 'ru-RU', 'ar-SA',
                    'nl-NL', 'sv-SE', 'no-NO', 'da-DK', 'fi-FI']
        
        timezones = ['America/New_York', 'America/Los_Angeles', 'Europe/London', 
                    'Europe/Paris', 'Asia/Kolkata', 'Asia/Tokyo', 'Australia/Sydney',
                    'America/Sao_Paulo', 'Africa/Johannesburg', 'Asia/Dubai',
                    'America/Chicago', 'America/Toronto', 'Europe/Berlin',
                    'Asia/Singapore', 'Asia/Shanghai', 'America/Mexico_City']
        
        fonts = [
            'Arial, Helvetica, sans-serif',
            'Times New Roman, Times, serif',
            'Courier New, Courier, monospace',
            'Georgia, serif',
            'Verdana, Arial, sans-serif',
            'Tahoma, Arial, sans-serif',
            'Trebuchet MS, Arial, sans-serif',
            'Palatino Linotype, Book Antiqua, Palatino, serif',
            'Lucida Grande, Lucida Sans Unicode, Arial, sans-serif',
            'Helvetica Neue, Arial, sans-serif'
        ]
        
        self.fingerprint = {
            'browser': browser,
            'screen': {
                'width': width,
                'height': height,
                'color_depth': random.choice([24, 30, 32]),
                'pixel_ratio': round(random.uniform(1, 3), 1)
            },
            'language': random.choice(languages),
            'timezone': random.choice(timezones),
            'platform': system,
            'platform_version': platform.version(),
            'cpu_cores': random.choice([2, 4, 6, 8, 10, 12, 16, 20, 24, 32]),
            'memory': random.choice(['4 GB', '8 GB', '16 GB', '32 GB', '64 GB', '128 GB', '256 GB']),
            'gpu': random.choice([
                'NVIDIA GeForce RTX 3060', 'NVIDIA GeForce RTX 3070', 'NVIDIA GeForce RTX 3080',
                'NVIDIA GeForce RTX 3090', 'NVIDIA GeForce RTX 4060', 'NVIDIA GeForce RTX 4070',
                'NVIDIA GeForce RTX 4080', 'NVIDIA GeForce RTX 4090', 'AMD Radeon RX 6800 XT',
                'AMD Radeon RX 6900 XT', 'AMD Radeon RX 7800 XT', 'AMD Radeon RX 7900 XTX',
                'Intel Iris Xe Graphics', 'Intel UHD Graphics 620', 'Apple M1 GPU',
                'Apple M2 GPU', 'Apple M3 GPU', 'Apple M3 Pro GPU', 'Apple M3 Max GPU'
            ]),
            'fonts': random.choice(fonts),
            'canvas_hash': hashlib.md5(str(random.randint(1, 99999999)).encode()).hexdigest()[:16],
            'webgl_hash': hashlib.md5(str(random.randint(1, 99999999)).encode()).hexdigest()[:16],
            'audio_hash': hashlib.md5(str(random.randint(1, 99999999)).encode()).hexdigest()[:16],
            'webgl_vendor': random.choice(['Google Inc.', 'Apple Inc.', 'Mozilla Foundation', 'NVIDIA Corporation', 'AMD', 'Intel Corporation']),
            'webgl_renderer': random.choice([
                'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080, Direct3D11 vs_5_0 ps_5_0, D3D11)', 
                'ANGLE (AMD, AMD Radeon RX 6800 XT, Direct3D11 vs_5_0 ps_5_0, D3D11)',
                'ANGLE (Intel, Intel(R) UHD Graphics 620, Direct3D11 vs_5_0 ps_5_0, D3D11)',
                'ANGLE (NVIDIA, NVIDIA GeForce RTX 4090, Direct3D12 vs_6_0 ps_6_0, D3D12)',
                'ANGLE (AMD, AMD Radeon RX 7900 XTX, Direct3D12 vs_6_0 ps_6_0, D3D12)'
            ]),
            'fingerprint_id': hashlib.md5(str(time.time() + random.random()).encode()).hexdigest(),
            'generated_at': datetime.now().isoformat(),
            'generation': self.generation_count
        }
    
    def get_fingerprint(self):
        return self.fingerprint
    
    def get_headers(self):
        return {
            'User-Agent': self.fingerprint['browser']['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': f"{self.fingerprint['language']},en;q=0.9",
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
            'Sec-Ch-Ua': f'"{self.fingerprint["browser"]["name"]}"; v="{self.fingerprint["browser"]["version"].split(".")[0]}"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': f'"{self.fingerprint["platform"]}"'
        }
    
    def rotate(self):
        self._generate_fingerprint()
        return self.fingerprint
    
    def should_rotate(self):
        return self.rotation_counter >= self.rotation_interval


# ============================================================
# INSTAGRAM SCANNER CLASS
# ============================================================
class InstagramScanner:
    def __init__(self):
        self.fingerprint = UltimateDeviceFingerprint()
        self.loader = None
        self.max_retries = 2
        self.retry_count = 0
    
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
    
    def estimate_account_creation_year(self, user_id):
        id_ranges = [
            (1, 2010), (100000, 2011), (1000000, 2011), (10000000, 2012),
            (50000000, 2013), (100000000, 2014), (300000000, 2015),
            (500000000, 2016), (1000000000, 2017), (3000000000, 2018),
            (5000000000, 2019), (8000000000, 2020), (12000000000, 2021),
            (18000000000, 2022), (25000000000, 2023), (35000000000, 2024),
            (45000000000, 2025),
        ]
        
        try:
            uid = int(user_id)
        except:
            return None
        
        for max_id, year in id_ranges:
            if uid <= max_id:
                return year
        
        if uid > 45000000000:
            return 2025 + (uid - 45000000000) // 5000000000
        
        return None
    
    def scan_profile(self, username):
        start_time = time.time()
        self.retry_count = 0
        return self._scan_with_retry(username)
    
    def _scan_with_retry(self, username):
        start_time = time.time()
        
        try:
            if not self.initialize_loader():
                return {'status': 'error', 'error': 'Failed to initialize Instagram loader'}
            
            profile = Profile.from_username(self.loader.context, username)
            fp = self.fingerprint.get_fingerprint()
            
            response_time = (time.time() - start_time) * 1000
            
            estimated_year = self.estimate_account_creation_year(profile.userid)
            
            # Business fields
            is_business = False
            is_professional = False
            category = None
            business_category = None
            
            try:
                is_business = profile.is_business_account
            except:
                is_business = False
            
            try:
                is_professional = getattr(profile, 'is_professional_account', False)
            except:
                is_professional = False
            
            try:
                category = getattr(profile, 'category_name', None)
                if category == '':
                    category = None
            except:
                category = None
            
            try:
                business_category = getattr(profile, 'business_category_name', None)
                if business_category == '':
                    business_category = None
            except:
                business_category = None
            
            # Highlights
            highlight_count = getattr(profile, 'highlight_reel_count', 0)
            has_highlights = getattr(profile, 'has_highlight_reels', False)
            
            # IGTV Count
            try:
                igtv_count = profile.igtv_count
            except:
                igtv_count = 0
            
            # Is Joined Recently
            try:
                is_joined_recently = getattr(profile, 'is_joined_recently', False)
            except:
                is_joined_recently = False
            
            # Bio Links
            bio_links = []
            try:
                if hasattr(profile, 'biography_links'):
                    for link in profile.biography_links:
                        if isinstance(link, dict) and 'url' in link:
                            bio_links.append(link['url'])
                        elif isinstance(link, str):
                            bio_links.append(link)
            except:
                bio_links = []
            
            result = {
                "status": "ok",
                "collected_at": datetime.now().isoformat(),
                "response_time_seconds": round(response_time / 1000, 3),
                "profile": {
                    "id": str(profile.userid),
                    "username": profile.username,
                    "full_name": profile.full_name if profile.full_name else 'N/A',
                    "biography": profile.biography[:200] if profile.biography else 'No bio available',
                    "is_private": profile.is_private,
                    "is_verified": profile.is_verified,       
                    "is_business_account": is_business,
                    "is_professional_account": is_professional,
                    "category_name": category,
                    "business_category_name": business_category,
                    "profile_pic_url_hd": getattr(profile, 'profile_pic_url_hd', None) or getattr(profile, 'profile_pic_url', None),
                    "external_url": profile.external_url if profile.external_url else None,
                    "followers": profile.followers,
                    "following": profile.followees,
                    "posts": profile.mediacount,
                    "account_creation_year": estimated_year,
                    "has_highlights": has_highlights or highlight_count > 0,           
                    "is_joined_recently": is_joined_recently,
                    "bio_links": bio_links,
                    "igtv_count": igtv_count
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
            if "401" in str(e) and self.retry_count < self.max_retries:
                self.retry_count += 1
                print(f"Retry {self.retry_count}/{self.max_retries} for {username}")
                time.sleep(2)
                return self._scan_with_retry(username)
            else:
                return {'status': 'error', 'error': str(e)[:200], 'code': 'SCAN_ERROR'}


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
# ROUTES
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
            return redirect(url_for('login_page', error='Invalid credentials'))
    
    return redirect(url_for('login_page', error='Please login first'))

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return jsonify({'error': 'File not found'}), 404

@app.route('/')
def home():
    return send_from_directory('.', 'login.html')

# ============================================================
# API: SCAN PROFILE - GET REQUEST (WITH API KEY)
# ============================================================
@app.route('/api/scan', methods=['GET'])
def scan_profile_get():
    start_time = time.time()
    
    # Check maintenance
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
    
    # Get API key from query
    api_key = request.args.get('api_key', '').strip()
    
    # Validate API key
    user_data, username = validate_api_key(api_key)
    if not user_data:
        return jsonify({
            'status': 'error',
            'code': 'INVALID_KEY',
            'error': 'Invalid API key',
            'message': 'The API key provided is not valid',
            'support': 'https://t.me/KINGFFAIAK47x'
        }), 403
    
    # Check rate limits
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
    
    # Get username from query
    username_param = request.args.get('username', '').strip()
    
    if not username_param:
        return jsonify({
            'status': 'error',
            'code': 'NO_USERNAME',
            'error': 'Username required',
            'message': 'Please provide username parameter',
            'example': '/api/scan?username=instagram&api_key=DEMOFUCK'
        }), 400
    
    # Scan profile
    result = scanner.scan_profile(username_param)
    
    # Log request
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
    
    # Add metadata if success
    if result.get('status') == 'ok':
        result['api_key_used'] = api_key[:16] + '...'
        result['plan'] = user_data.get('plan', 'user')
        result['limit_minute'] = per_minute
        result['limit_day'] = per_day
        result['remaining_minute'] = per_minute - rate_limit_data.get(api_key, {}).get('minute_count', 0)
        result['remaining_day'] = per_day - rate_limit_data.get(api_key, {}).get('day_count', 0)
        result['developer'] = '@KINGFFAIAK47x'
        result['owner'] = 'ANSH AFT'
        result['channel'] = 'https://t.me/+iDnVRYTDnAJmNDE1'
        result['backup_channel'] = 'https://t.me/+aWlMH56c06ZiZTE1'
    
    return jsonify(result)

# ============================================================
# API: SCAN PROFILE - POST REQUEST (WITHOUT API KEY)
# ============================================================
@app.route('/api/scan', methods=['POST'])
def scan_profile_post():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({
            'status': 'error',
            'code': 'NO_USERNAME',
            'error': 'Username required',
            'example': '{"username": "instagram"}'
        }), 400
    
    result = scanner.scan_profile(username)
    
    if result.get('status') == 'ok':
        result['developer'] = '@KINGFFAIAK47x'
        result['owner'] = 'ANSH_AFT'
        result['channel'] = 'https://t.me/+iDnVRYTDnAJmNDE1'
        result['backup_channel'] = 'https://t.me/+aWlMH56c06ZiZTE1'
    
    return jsonify(result)

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
        'version': CONFIG.get('version', '3.0.0'),
        'developer': 'KINGFFAIAK47x',
        'owner': 'ANSH_AFT',
        'telegram': 'https://t.me/+iDnVRYTDnAJmNDE1',
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
# API: ADMIN LOGIN
# ============================================================
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if username == CONFIG['admin_username'] and password == CONFIG['admin_password']:
        return jsonify({
            'status': 'success',
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
            'status': 'error',
            'error': 'Invalid credentials'
        }), 401

# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    print('='*60)
    print('🔥 INSTAGRAM SCANNER API v3.0')
    print('='*60)
    print('👑 Owner: ANSH_AFT')
    print('💻 Developer: KINGFFAIAK47x')
    print('='*60)
    print('📊 API Endpoints:')
    print('   GET  /api/scan?username=USERNAME&api_key=KEY')
    print('   POST /api/scan { "username": "USERNAME" }')
    print('   GET  /api/health')
    print('   GET  /api/status')
    print('='*60)
    print('🔑 API Keys:')
    print('   ⭐ Premium: ANSHAFTAK472026')
    print('   🆓 User: DEMOFUCK')
    print('='*60)
    app.run(host='0.0.0.0', port=5000, debug=True)
