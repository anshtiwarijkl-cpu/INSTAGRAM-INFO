from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader
import time
import random
import hashlib
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db as firebase_db
import os

# ============================================================
# FIREBASE INIT
# ============================================================
firebase_config = {
    "apiKey": "AIzaSyCIOu1N7PEaDbrduIFPVpOBLw_upyefESE",
    "authDomain": "ansh-aft.firebaseapp.com",
    "databaseURL": "https://ansh-aft-default-rtdb.firebaseio.com",
    "projectId": "ansh-aft",
    "storageBucket": "ansh-aft.firebasestorage.app",
    "messagingSenderId": "856621572011",
    "appId": "1:856621572011:web:76f866cbea624c5f5c7cee"
}

# Initialize Firebase Admin
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": "ansh-aft",
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL', ''),
    "client_id": os.getenv('FIREBASE_CLIENT_ID', ''),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL', '')
})

firebase_admin.initialize_app(cred, {
    'databaseURL': firebase_config['databaseURL']
})

db = firebase_db

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)
CORS(app)

# ============================================================
# DEVICE FINGERPRINTS
# ============================================================
class DeviceFingerprint:
    def __init__(self):
        self.fingerprints = [
            {'id': 1, 'country': 'USA', 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
            {'id': 2, 'country': 'UK', 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'},
            {'id': 3, 'country': 'India', 'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'},
            {'id': 4, 'country': 'Japan', 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'},
            {'id': 5, 'country': 'Germany', 'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:122.0) Gecko/20100101 Firefox/122.0'},
            {'id': 6, 'country': 'Australia', 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'},
            {'id': 7, 'country': 'Brazil', 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/106.0.0.0'},
            {'id': 8, 'country': 'UAE', 'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'}
        ]
        self.index = 0
    
    def get_next(self):
        fp = self.fingerprints[self.index % len(self.fingerprints)]
        self.index += 1
        return fp

device_fp = DeviceFingerprint()

# ============================================================
# INSTAGRAM SCANNER
# ============================================================
def scan_instagram(username):
    try:
        fp = device_fp.get_next()
        loader = instaloader.Instaloader(
            max_connection_attempts=3,
            request_timeout=30,
            user_agent=fp['user_agent'],
            sleep=True,
            quiet=True
        )
        
        profile = instaloader.Profile.from_username(loader.context, username)
        
        return {
            'status': 'success',
            'username': profile.username,
            'user_id': profile.userid,
            'full_name': profile.full_name or 'N/A',
            'biography': profile.biography[:200] if profile.biography else 'No bio',
            'external_url': profile.external_url or 'None',
            'followers': profile.followers,
            'following': profile.followees,
            'total_posts': profile.mediacount,
            'is_private': profile.is_private,
            'is_verified': profile.is_verified,
            'is_business': profile.is_business_account,
            'scraped_at': datetime.now().isoformat(),
            'developer': 'DeveloperBhai',
            'owner': 'ANSH_AFT'
        }
    except instaloader.exceptions.ProfileNotExistsException:
        return {'status': 'error', 'error': '❌ Profile @{} does not exist'.format(username), 'code': 'INVALID_USER'}
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        return {'status': 'error', 'error': '🔒 Profile @{} is private'.format(username), 'code': 'PRIVATE_ACCOUNT'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)[:100], 'code': 'SCAN_ERROR'}

# ============================================================
# API ENDPOINTS
# ============================================================
@app.route('/api/scan', methods=['POST'])
def scan_profile():
    start_time = time.time()
    
    # Get API key
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'status': 'error', 'error': '❌ API key required', 'code': 'NO_API_KEY'}), 401
    
    # Validate API key
    users_ref = db.reference('users')
    users = users_ref.get()
    if not users:
        return jsonify({'status': 'error', 'error': '❌ Invalid API key', 'code': 'INVALID_KEY'}), 401
    
    user = None
    user_id = None
    for uid, data in users.items():
        if data.get('api_key') == api_key:
            user = data
            user_id = uid
            break
    
    if not user:
        return jsonify({'status': 'error', 'error': '❌ Invalid API key', 'code': 'INVALID_KEY'}), 401
    
    if user.get('active') == False:
        return jsonify({'status': 'error', 'error': '⛔ User account is disabled', 'code': 'ACCOUNT_DISABLED'}), 403
    
    # Check API status
    settings_ref = db.reference('settings')
    settings = settings_ref.get() or {}
    api_status = settings.get('api_status', 'online')
    
    if api_status == 'offline':
        return jsonify({
            'status': 'error',
            'error': '❌ API is currently OFFLINE. Please try again later.',
            'code': 'API_OFFLINE'
        }), 503
    
    if api_status == 'maintenance':
        return jsonify({
            'status': 'error',
            'error': '🔧 API is under MAINTENANCE. Please try again later.',
            'code': 'MAINTENANCE'
        }), 503
    
    # Check limits
    plan = user.get('plan', 'free')
    limit_key = 'premium_limit' if plan == 'premium' else 'free_limit'
    limit = settings.get(limit_key, 10000 if plan == 'premium' else 1000)
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
    
    # Get username
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({'status': 'error', 'error': '❌ Username required', 'code': 'NO_USERNAME'}), 400
    
    username = data['username'].strip()
    if not username:
        return jsonify({'status': 'error', 'error': '❌ Username cannot be empty', 'code': 'EMPTY_USERNAME'}), 400
    
    # Scan
    result = scan_instagram(username)
    
    # Log
    log_ref = db.reference('logs')
    log_ref.push({
        'api_key': api_key,
        'username': username,
        'success': result.get('status') == 'success',
        'response_time': (time.time() - start_time) * 1000,
        'timestamp': datetime.now().isoformat()
    })
    
    # Increment count
    today = datetime.now().strftime('%Y-%m-%d')
    if result.get('status') == 'success':
        users_ref.child(user_id).update({
            'requests_count': current_requests + 1,
            'last_request': datetime.now().isoformat()
        })
        users_ref.child(user_id).child('daily_requests').child(today).transaction(lambda x: (x or 0) + 1)
    
    result['plan'] = plan
    result['limit_used'] = current_requests + 1 if result.get('status') == 'success' else current_requests
    result['limit_total'] = limit
    result['api_key'] = api_key[:16] + '...'
    result['developer'] = 'DeveloperBhai'
    result['owner'] = 'ANSH_AFT'
    result['channel'] = 'https://t.me/+iDnVRYTDnAJmNDE1'
    result['backup_channel'] = 'https://t.me/+aWlMH56c06ZiZTE1'
    
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health_check():
    settings_ref = db.reference('settings')
    settings = settings_ref.get() or {}
    
    users_ref = db.reference('users')
    users = users_ref.get() or {}
    
    return jsonify({
        'status': 'running',
        'api_status': settings.get('api_status', 'online'),
        'maintenance': settings.get('api_status') == 'maintenance',
        'total_users': len(users),
        'uptime': datetime.now().isoformat(),
        'version': '2.0.0',
        'developer': 'DeveloperBhai',
        'owner': 'ANSH_AFT'
    })

# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    print('🔥 Instagram Scanner API Started!')
    print('👑 Owner: ANSH_AFT')
    print('💻 Developer: DeveloperBhai')
    print('🔑 Login: ANSHAFT127987 / ANSHAFTAK47')
    print('📊 API Endpoint: /api/scan')
    app.run(host='0.0.0.0', port=5000, debug=True)
