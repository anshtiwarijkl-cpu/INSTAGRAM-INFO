from flask import Flask, request, jsonify, send_from_directory, redirect, url_for, session
from flask_cors import CORS
import instaloader
import time
import random
import hashlib
import platform
import os
from datetime import datetime, timedelta
from instaloader import Instaloader, Profile
import secrets
import jwt
from functools import wraps

app = Flask(__name__, static_folder='.')
app.secret_key = secrets.token_hex(32)  # Secret key for sessions
CORS(app)

# ============================================================
# CONFIGURATION
# ============================================================
CONFIG = {
    "admin_username": "ANSHAFT127987",
    "admin_password": "ANSHAFTAK47",
    "version": "3.0.0",
    "api_status": "online",
    "maintenance": False,
    "secret_key": secrets.token_hex(32)  # For JWT
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
# TOKEN GENERATION & VERIFICATION
# ============================================================
def generate_session_token(username):
    """Generate secure JWT token for session"""
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24),  # 24 hours expiry
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, CONFIG['secret_key'], algorithm='HS256')

def verify_session_token(token):
    """Verify JWT token and return username if valid"""
    try:
        payload = jwt.decode(token, CONFIG['secret_key'], algorithms=['HS256'])
        return payload.get('username')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    """Decorator to protect routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token') or request.cookies.get('session_token')
        if not token:
            return redirect(url_for('login_page', error='Please login first'))
        
        username = verify_session_token(token)
        if not username:
            return redirect(url_for('login_page', error='Session expired or invalid'))
        
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# GLOBAL RATE LIMITER - PREVENT MULTIPLE INSTANCES
# ============================================================
import threading
request_lock = threading.Lock()
last_request_time = 0
min_delay_between_requests = 5  # 5 SECONDS DELAY

def wait_for_rate_limit():
    """Wait to respect Instagram's rate limits"""
    global last_request_time
    with request_lock:
        current_time = time.time()
        time_since_last = current_time - last_request_time
        if time_since_last < min_delay_between_requests:
            wait_time = min_delay_between_requests - time_since_last
            print(f"⏳ Waiting {wait_time:.1f} seconds for rate limit...")
            time.sleep(wait_time)
        last_request_time = time.time()

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
# DEVICE FINGERPRINT - ROTATE USER AGENTS
# ============================================================
class DeviceFingerprint:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:122.0) Gecko/20100101 Firefox/122.0'
        ]
        self.index = 0
    
    def get_next(self):
        ua = self.user_agents[self.index % len(self.user_agents)]
        self.index += 1
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
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

device_headers = DeviceFingerprint()

# ============================================================
# INSTAGRAM SCANNER - WITH RATE LIMIT HANDLING
# ============================================================
class InstagramScanner:
    def __init__(self):
        self.loader = None
    
    def initialize_loader(self):
        try:
            wait_for_rate_limit()
            
            headers = device_headers.get_next()
            
            self.loader = Instaloader(
                max_connection_attempts=1,
                request_timeout=15,
                user_agent=headers['User-Agent'],
                sleep=True,
                quiet=True
            )
            
            if hasattr(self.loader, 'context') and hasattr(self.loader.context, '_session'):
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
        
        try:
            if not self.initialize_loader():
                return {'status': 'error', 'error': 'Failed to initialize Instagram loader'}
            
            profile = Profile.from_username(self.loader.context, username)
            
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
                "MADE_BY": "ANSH_AFT"
            }
            
            return result
            
        except instaloader.exceptions.ProfileNotExistsException:
            return {'status': 'error', 'error': f'Profile @{username} does not exist', 'code': 'INVALID_USER'}
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            return {'status': 'error', 'error': f'Profile @{username} is private', 'code': 'PRIVATE_ACCOUNT'}
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Too Many Requests" in error_msg:
                return {'status': 'error', 'error': 'Too many requests. Please wait a moment and try again.', 'code': 'RATE_LIMIT_INSTAGRAM'}
            if "timeout" in error_msg.lower():
                return {'status': 'error', 'error': 'Request timed out. Please try again.', 'code': 'TIMEOUT'}
            return {'status': 'error', 'error': error_msg[:200], 'code': 'SCAN_ERROR'}

scanner = InstagramScanner()

# ============================================================
# VALIDATE API KEY
# ============================================================
def validate_api_key(api_key):
    if not api_key:
        return None, "API key required"
    
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
@app.route('/login.html')
def login_page():
    error = request.args.get('error')
    return send_from_directory('.', 'login.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    """Protected dashboard route - only accessible with valid token"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/logout')
def logout():
    """Clear session and redirect to login"""
    resp = redirect(url_for('login_page'))
    resp.set_cookie('session_token', '', expires=0)  # Clear cookie
    return resp

@app.route('/')
def home():
    return send_from_directory('.', 'login.html')

# ============================================================
# API: SCAN PROFILE
# ============================================================
@app.route('/api/scan', methods=['GET'])
def scan_profile_get():
    start_time = time.time()
    
    # Maintenance check
    if CONFIG.get('maintenance', False):
        return jsonify({
            'status': 'error',
            'code': 'MAINTENANCE',
            'error': 'API Under Maintenance'
        }), 503
    
    if CONFIG.get('api_status') == 'offline':
        return jsonify({
            'status': 'error',
            'code': 'API_OFFLINE',
            'error': 'API Offline'
        }), 503
    
    # Get API key
    api_key = request.args.get('api_key', '').strip()
    
    if not api_key:
        return jsonify({
            'status': 'error',
            'code': 'NO_API_KEY',
            'error': 'API key required',
            'example': '/api/scan?username=instagram&api_key=DEMOFUCK'
        }), 401
    
    # Validate API key
    user_data, username = validate_api_key(api_key)
    if not user_data:
        return jsonify({
            'status': 'error',
            'code': 'INVALID_KEY',
            'error': 'Invalid API key'
        }), 403
    
    # Rate limit
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
    
    # Get username
    username_param = request.args.get('username', '').strip()
    
    if not username_param:
        return jsonify({
            'status': 'error',
            'code': 'NO_USERNAME',
            'error': 'Username required',
            'example': '/api/scan?username=instagram&api_key=DEMOFUCK'
        }), 400
    
    # Scan
    try:
        result = scanner.scan_profile(username_param)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'code': 'SCAN_ERROR',
            'error': str(e)[:100]
        }), 500
    
    # Add metadata
    if result.get('status') == 'ok':
        result['api_key_used'] = api_key[:16] + '...'
        result['plan'] = user_data.get('plan', 'user')
        result['limit_minute'] = per_minute
        result['limit_day'] = per_day
        result['remaining_minute'] = per_minute - rate_limit_data.get(api_key, {}).get('minute_count', 0)
        result['remaining_day'] = per_day - rate_limit_data.get(api_key, {}).get('day_count', 0)
        result['developer'] = '@KINGFFAIAK47x'
        result['owner'] = 'ANSH_AFT'
        result['channel'] = 'https://t.me/+iDnVRYTDnAJmNDE1'
        result['backup_channel'] = 'https://t.me/+aWlMH56c06ZiZTE1'
    
    return jsonify(result)

# ============================================================
# API: HEALTH
# ============================================================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'running',
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
# API: ADMIN LOGIN (FIXED)
# ============================================================
@app.route('/api/admin/login', methods=['POST', 'OPTIONS'])
def admin_login():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request data'
            }), 400
            
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # Validate input
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        # Check credentials
        if username == CONFIG['admin_username'] and password == CONFIG['admin_password']:
            # Generate session token
            session_token = generate_session_token(username)
            
            # Create response with token
            response = jsonify({
                'success': True,
                'message': 'Login successful',
                'username': username,
                'redirect': '/dashboard?token=' + session_token,
                'developer': 'KINGFFAIAK47x',
                'owner': 'ANSH_AFT'
            })
            
            # Set cookie for session persistence
            response.set_cookie(
                'session_token', 
                session_token,
                max_age=24*60*60,  # 24 hours
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax'
            )
            
            return response
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
            
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred during login'
        }), 500

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
    print('📊 URL FORMAT:')
    print('   /api/scan?username=USERNAME&api_key=KEY')
    print('='*60)
    print('🔑 API Keys:')
    print('   ⭐ Premium: ANSHAFTAK472026')
    print('   🆓 User: DEMOFUCK')
    print('='*60)
    print('🔐 Admin Login:')
    print(f'   Username: {CONFIG["admin_username"]}')
    print(f'   Password: {CONFIG["admin_password"]}')
    print('='*60)
    app.run(host='0.0.0.0', port=5000, debug=False)
