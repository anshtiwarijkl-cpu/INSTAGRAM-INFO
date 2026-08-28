import instaloader
import time
import random
import hashlib
import platform
from datetime import datetime

# ============================================================
# DEVICE FINGERPRINT - ROTATES
# ============================================================
class DeviceFingerprint:
    def __init__(self):
        self.fingerprint = {}
        self.generation_count = 0
        self._generate_fingerprint()
    
    def _generate_fingerprint(self):
        self.generation_count += 1
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
        ]
        
        browser = random.choice(browsers)
        screens = [
            (1920, 1080), (2560, 1440), (3840, 2160),
            (1366, 768), (1536, 864), (1440, 900),
            (1600, 900), (1280, 720), (1920, 1200),
            (2560, 1600), (3440, 1440), (1360, 768)
        ]
        width, height = random.choice(screens)
        
        languages = ['en-US', 'en-GB', 'en-IN', 'en-AU', 'en-CA', 
                    'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'pt-BR',
                    'ja-JP', 'ko-KR', 'zh-CN', 'ru-RU', 'ar-SA']
        
        timezones = ['America/New_York', 'America/Los_Angeles', 'Europe/London', 
                    'Europe/Paris', 'Asia/Kolkata', 'Asia/Tokyo', 'Australia/Sydney',
                    'America/Sao_Paulo', 'Africa/Johannesburg', 'Asia/Dubai']
        
        self.fingerprint = {
            'browser': browser,
            'screen': {'width': width, 'height': height},
            'language': random.choice(languages),
            'timezone': random.choice(timezones),
            'platform': system,
            'cpu_cores': random.choice([4, 6, 8, 10, 12, 16]),
            'memory': random.choice(['8 GB', '16 GB', '32 GB', '64 GB']),
            'gpu': random.choice([
                'NVIDIA GeForce RTX 3060', 'NVIDIA GeForce RTX 3080', 'NVIDIA GeForce RTX 4090',
                'AMD Radeon RX 6800 XT', 'AMD Radeon RX 7900 XTX', 'Apple M2 GPU', 'Apple M3 GPU'
            ]),
            'fingerprint_id': hashlib.md5(str(time.time() + random.random()).encode()).hexdigest()[:16],
            'generated_at': datetime.now().isoformat(),
            'generation': self.generation_count
        }
    
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
    
    def get_fingerprint(self):
        return self.fingerprint


# ============================================================
# INSTAGRAM FETCHER
# ============================================================
class InstagramFetcher:
    def __init__(self):
        self.fingerprint = DeviceFingerprint()
        self.loader = None
        self.max_retries = 2
        self.retry_count = 0
    
    def initialize_loader(self):
        try:
            headers = self.fingerprint.get_headers()
            
            self.loader = instaloader.Instaloader(
                max_connection_attempts=3,
                request_timeout=30,
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
    
    def fetch_profile(self, username):
        start_time = time.time()
        self.retry_count = 0
        return self._fetch_with_retry(username)
    
    def _fetch_with_retry(self, username):
        start_time = time.time()
        
        try:
            if not self.initialize_loader():
                return {'status': 'error', 'error': 'Failed to initialize Instagram loader'}
            
            profile = instaloader.Profile.from_username(self.loader.context, username)
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
                "MADE_BY": "ANSH_AFT"
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
                return self._fetch_with_retry(username)
            else:
                return {'status': 'error', 'error': str(e)[:200], 'code': 'SCAN_ERROR'}
