from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from instagram_fetcher import InstagramFetcher
import os
import time
from datetime import datetime

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
# INIT FETCHER
# ============================================================
fetcher = InstagramFetcher()

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

@app.route('/')
def home():
    return send_from_directory('.', 'login.html')

# ============================================================
# API: SCAN PROFILE
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
    
    # Fetch profile from Instagram
    result = fetcher.fetch_profile(username_param)
    
    # Add metadata if success
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
# API: SCAN PROFILE - POST (NO API KEY)
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
    
    result = fetcher.fetch_profile(username)
    
    if result.get('status') == 'ok':
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
    print('📊 URL FORMAT:')
    print('   GET  /api/scan?username=USERNAME&api_key=KEY')
    print('   POST /api/scan { "username": "USERNAME" }')
    print('='*60)
    print('🔑 API Keys:')
    print('   ⭐ Premium: ANSHAFTAK472026')
    print('   🆓 User: DEMOFUCK')
    print('='*60)
    app.run(host='0.0.0.0', port=5000, debug=True)
