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
import firebase_admin
from firebase_admin import credentials, db as firebase_db

app = Flask(__name__, static_folder='.')
CORS(app)

# ============================================================
# DEVELOPER & OWNER INFO
# ============================================================
DEVELOPER = {
    "name": "KINGFFAIAK47x",
    "telegram": "https://t.me/KINGFFAIAK47x",
    "channel": "https://t.me/+iDnVRYTDnAJmNDE1",
    "backup_channel": "https://t.me/+aWlMH56c06ZiZTE1",
    "github": "https://github.com/KINGFFAIAK47x",
    "instagram": "https://instagram.com/KINGFFAIAK47x"
}

OWNER = {
    "name": "ANSH_AFT",
    "telegram": "https://t.me/ANSH_AFT",
    "channel": "https://t.me/+iDnVRYTDnAJmNDE1"
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
# FIREBASE INIT
# ============================================================
def init_firebase():
    try:
        if firebase_admin._apps:
            return True
        
        private_key = os.getenv('FIREBASE_PRIVATE_KEY', '')
        if private_key:
            private_key = private_key.strip('"').replace('\\n', '\n')
        
        cred_dict = {
            "type": os.getenv('FIREBASE_TYPE', 'service_account'),
            "project_id": os.getenv('FIREBASE_PROJECT_ID', 'ansh-aft'),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
            "private_key": private_key,
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL', ''),
            "client_id": os.getenv('FIREBASE_CLIENT_ID', ''),
            "auth_uri": os.getenv('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            "token_uri": os.getenv('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL', '')
        }
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv('FIREBASE_DATABASE_URL', 'https://ansh-aft-default-rtdb.firebaseio.com')
        })
        
        print("🔥 Firebase initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Firebase init error: {e}")
        return False

FIREBASE_READY = init_firebase()
db = firebase_db if FIREBASE_READY else None

# ============================================================
# 8 REAL DEVICE FINGERPRINTS - ROTATES EVERY REQUEST
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

# Serve login page
@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')

# Serve dashboard page
@app.route('/dashboard')
def dashboard_page():
    return send_from_directory('.', 'dashboard.html')

# Serve static files
@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return jsonify({'error': 'File not found'}), 404

# Root - serve login page by default
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
        'firebase_connected': bool(db),
        'timestamp': datetime.now().isoformat(),
        'service': 'Instagram Scanner API',
        'version': '2.0.0',
        'developer': 'KINGFFAIAK47x',
        'owner': 'ANSH_AFT',
        'telegram': 'https://t.me/+iDnVRYTDnAJmNDE1',
        'backup': 'https://t.me/+aWlMH56c06ZiZTE1'
    })

# ============================================================
# API: SCAN PROFILE
# ============================================================
@app.route('/api/scan', methods=['POST'])
def scan_profile():
    start_time = time.time()
    
    # Check Firebase
    if not db:
        return jsonify({'status': 'error', 'error': '❌ Firebase not connected. Please check credentials.', 'code': 'DB_ERROR'}), 500
    
    # Get API key from header
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'status': 'error', 'error': '❌ API key required', 'code': 'NO_API_KEY'}), 401
    
    # Check if it's premium or user key
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
        users_ref = db.reference('users')
        users = users_ref.get()
        user = None
        user_id = None
        if users:
            for uid, data in users.items():
                if data.get('api_key') == api_key:
                    user = data
                    user_id = uid
                    plan = user.get('plan', 'free')
                    limit = 10000 if plan == 'premium' else 1000
                    break
        
        if not user:
            return jsonify({'status': 'error', 'error': '❌ Invalid API key', 'code': 'INVALID_KEY'}), 401
        
        if user.get('active') == False:
            return jsonify({'status': 'error', 'error': '⛔ User account is disabled', 'code': 'ACCOUNT_DISABLED'}), 403
        
        # Check rate limit for custom user
        settings_ref = db.reference('settings')
        settings = settings_ref.get() or {}
        limit = settings.get('premium_limit' if plan == 'premium' else 'free_limit', limit)
        current_requests = user.get('requests_count', 0)
        
        if current_requests >= limit:
            return jsonify({
                'status': 'error',
                'error': f'⚠️ {plan.upper()} limit exceeded! {current_requests}/{limit}',
                'code': 'LIMIT_EXCEEDED',
                'plan': plan,
                'current': current_requests,
                'limit': limit
            }), 429
    
    # Get username from request
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({'status': 'error', 'error': '❌ Username required', 'code': 'NO_USERNAME'}), 400
    
    username = data['username'].strip()
    if not username:
        return jsonify({'status': 'error', 'error': '❌ Username cannot be empty', 'code': 'EMPTY_USERNAME'}), 400
    
    # Check maintenance mode
    settings_ref = db.reference('settings')
    settings = settings_ref.get() or {}
    if settings.get('api_status') == 'offline':
        return jsonify({
            'status': 'error',
            'error': '❌ API is currently OFFLINE. Please try again later.',
            'code': 'API_OFFLINE'
        }), 503
    
    if settings.get('api_status') == 'maintenance':
        return jsonify({
            'status': 'error',
            'error': '🔧 API is under MAINTENANCE. Please try again later.',
            'code': 'MAINTENANCE'
        }), 503
    
    # Scan Instagram profile
    result = scanner.scan_profile(username)
    
    # Log request
    log_ref = db.reference('logs')
    log_ref.push({
        'api_key': api_key[:16] + '...',
        'username': username,
        'success': result.get('status') == 'success',
        'response_time': (time.time() - start_time) * 1000,
        'timestamp': datetime.now().isoformat()
    })
    
    # Increment request count for custom users
    if api_key not in [API_KEYS['premium'], API_KEYS['user']] and user_id and result.get('status') == 'success':
        today = datetime.now().strftime('%Y-%m-%d')
        users_ref.child(user_id).update({
            'requests_count': user.get('requests_count', 0) + 1,
            'last_request': datetime.now().isoformat()
        })
        users_ref.child(user_id).child('daily_requests').child(today).transaction(lambda x: (x or 0) + 1)
    
    # Add metadata to response
    result['plan'] = plan
    result['limit_used'] = (current_requests + 1) if result.get('status') == 'success' else current_requests
    result['limit_total'] = limit
    result['api_key'] = api_key[:16] + '...'
    result['developer'] = 'KINGFFAIAK47x'
    result['owner'] = 'ANSH_AFT'
    result['telegram_channel'] = 'https://t.me/+iDnVRYTDnAJmNDE1'
    result['backup_channel'] = 'https://t.me/+aWlMH56c06ZiZTE1'
    
    return jsonify(result)

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
        # Log failed attempt
        if db:
            db.reference('failed_logins').push({
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'ip': request.remote_addr
            })
        return jsonify({
            'status': 'error',
            'error': '❌ Invalid credentials',
            'code': 'INVALID_CREDENTIALS'
        }), 401

# ============================================================
# API: GET USERS (Admin)
# ============================================================
@app.route('/api/admin/users', methods=['GET'])
def get_users():
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    users_ref = db.reference('users')
    users = users_ref.get() or {}
    return jsonify(users)

# ============================================================
# API: CREATE USER (Admin)
# ============================================================
@app.route('/api/admin/users', methods=['POST'])
def create_user():
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    
    data = request.get_json()
    username = data.get('username', '').strip()
    plan = data.get('plan', 'free')
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    api_key = secrets.token_hex(16)
    
    users_ref = db.reference('users')
    new_user = {
        'username': username,
        'api_key': api_key,
        'plan': plan,
        'active': True,
        'requests_count': 0,
        'daily_requests': {},
        'created_at': datetime.now().isoformat(),
        'last_request': None
    }
    users_ref.push(new_user)
    
    return jsonify({
        'status': 'success',
        'user': new_user,
        'developer': 'KINGFFAIAK47x',
        'owner': 'ANSH_AFT'
    })

# ============================================================
# API: UPDATE USER (Admin)
# ============================================================
@app.route('/api/admin/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    
    data = request.get_json()
    users_ref = db.reference('users')
    
    updates = {}
    if 'plan' in data:
        updates['plan'] = data['plan']
    if 'active' in data:
        updates['active'] = data['active']
    if 'api_key' in data:
        updates['api_key'] = data['api_key']
    
    if updates:
        users_ref.child(user_id).update(updates)
    
    return jsonify({
        'status': 'success',
        'message': 'User updated',
        'developer': 'KINGFFAIAK47x',
        'owner': 'ANSH_AFT'
    })

# ============================================================
# API: GET SETTINGS (Admin)
# ============================================================
@app.route('/api/admin/settings', methods=['GET'])
def get_settings():
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    settings_ref = db.reference('settings')
    settings = settings_ref.get() or {}
    return jsonify(settings)

# ============================================================
# API: UPDATE SETTINGS (Admin)
# ============================================================
@app.route('/api/admin/settings', methods=['PUT'])
def update_settings():
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    
    data = request.get_json()
    settings_ref = db.reference('settings')
    
    updates = {}
    if 'free_limit' in data:
        updates['free_limit'] = int(data['free_limit'])
    if 'premium_limit' in data:
        updates['premium_limit'] = int(data['premium_limit'])
    if 'api_status' in data:
        updates['api_status'] = data['api_status']
    if 'maintenance_mode' in data:
        updates['maintenance_mode'] = data['maintenance_mode']
    
    updates['last_updated'] = datetime.now().isoformat()
    
    if updates:
        settings_ref.update(updates)
    
    return jsonify({
        'status': 'success',
        'message': 'Settings updated',
        'developer': 'KINGFFAIAK47x',
        'owner': 'ANSH_AFT'
    })

# ============================================================
# API: GET LOGS (Admin)
# ============================================================
@app.route('/api/admin/logs', methods=['GET'])
def get_logs():
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    logs_ref = db.reference('logs')
    logs = logs_ref.get() or {}
    return jsonify(logs)

# ============================================================
# API: GET FAILED LOGINS (Admin)
# ============================================================
@app.route('/api/admin/failed_logins', methods=['GET'])
def get_failed_logins():
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    failed_ref = db.reference('failed_logins')
    failed = failed_ref.get() or {}
    return jsonify(failed)

# ============================================================
# API: CLEAR LOGS (Admin)
# ============================================================
@app.route('/api/admin/clear_logs', methods=['DELETE'])
def clear_logs():
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    db.reference('logs').set({})
    return jsonify({'status': 'success', 'message': 'Logs cleared'})

# ============================================================
# API: CLEAR FAILED LOGINS (Admin)
# ============================================================
@app.route('/api/admin/clear_failed_logins', methods=['DELETE'])
def clear_failed_logins():
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    db.reference('failed_logins').set({})
    return jsonify({'status': 'success', 'message': 'Failed logins cleared'})

# ============================================================
# API: RESET ALL (Admin)
# ============================================================
@app.route('/api/admin/reset_all', methods=['DELETE'])
def reset_all():
    if not db:
        return jsonify({'error': 'Firebase not connected'}), 500
    db.reference('logs').set({})
    db.reference('failed_logins').set({})
    db.reference('settings').set({
        'free_limit': 1000,
        'premium_limit': 10000,
        'api_status': 'online',
        'maintenance_mode': False,
        'last_updated': datetime.now().isoformat()
    })
    return jsonify({
        'status': 'success',
        'message': 'All data reset',
        'developer': 'KINGFFAIAK47x',
        'owner': 'ANSH_AFT'
    })

# ============================================================
# RUN APP
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
    print('='*60)
    print('📊 Admin Panel: /login')
    print('📊 Dashboard: /dashboard')
    print('📊 API Health: /api/health')
    print('📊 API Scan: /api/scan (POST)')
    print('='*60)
    print('🔥 Server Starting...')
    app.run(host='0.0.0.0', port=5000, debug=True)
