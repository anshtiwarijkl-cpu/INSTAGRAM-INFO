const express = require('express');
const app = express();
const fs = require('fs');
const path = require('path');

// ========== CORS ==========
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, x-api-key');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// ========== MIDDLEWARE ==========
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('.'));

// ============================================================
// CONFIGURATION
// ============================================================
let CONFIG = {
  adminUsername: 'ANSHAFT127987',
  adminPassword: 'ANSHAFTAK47',
  rateLimit: {
    user: { perMinute: 100, perDay: 1000 },
    owner: { perMinute: 10000, perDay: 100000 },
    free: { perMinute: 10, perDay: 100 }
  },
  apiStatus: 'online',
  version: '3.0.0',
  theme: {
    background: '#0a0a0a',
    color: '#00ff41',
    glowColor: '#00ff41'
  },
  maintenance: false,
  logsEnabled: true
};

// ============================================================
// DATA STORAGE
// ============================================================
let users = {
  'ANSHAFT127987': {
    apiKey: 'ANSHAFTAK472026',
    plan: 'owner',
    minuteRequests: 0,
    dayRequests: 0,
    lastMinuteReset: Date.now(),
    lastDayReset: Date.now(),
    createdAt: Date.now(),
    status: 'active'
  },
  'DEMO_USER': {
    apiKey: 'DEMOFUCK',
    plan: 'user',
    minuteRequests: 0,
    dayRequests: 0,
    lastMinuteReset: Date.now(),
    lastDayReset: Date.now(),
    createdAt: Date.now(),
    status: 'active'
  }
};

let usageLogs = [];
let systemStats = { totalRequests: 0, startTime: Date.now() };
let failedLogins = [];
let announcements = [];

// ============================================================
// SAVE/L OAD DATA (PERSISTENCE)
// ============================================================
const DATA_FILE = path.join(__dirname, 'data.json');

function saveData() {
  try {
    const data = {
      users,
      usageLogs: usageLogs.slice(-500),
      systemStats,
      failedLogins: failedLogins.slice(-100),
      announcements,
      CONFIG
    };
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
  } catch (e) {
    console.log('⚠️ Save error:', e.message);
  }
}

function loadData() {
  try {
    if (fs.existsSync(DATA_FILE)) {
      const raw = fs.readFileSync(DATA_FILE, 'utf8');
      const data = JSON.parse(raw);
      users = data.users || users;
      usageLogs = data.usageLogs || [];
      systemStats = data.systemStats || { totalRequests: 0, startTime: Date.now() };
      failedLogins = data.failedLogins || [];
      announcements = data.announcements || [];
      CONFIG = data.CONFIG || CONFIG;
      console.log('✅ Data loaded successfully');
    }
  } catch (e) {
    console.log('⚠️ Load error:', e.message);
  }
}

// Load data on startup
loadData();

// Auto-save every 30 seconds
setInterval(saveData, 30000);

// ============================================================
// RATE LIMIT CHECK
// ============================================================
function checkAndResetLimits(user) {
  const now = Date.now();
  const oneMinute = 60000;
  const oneDay = 86400000;
  
  if (now - user.lastMinuteReset > oneMinute) {
    user.minuteRequests = 0;
    user.lastMinuteReset = now;
  }
  
  if (now - user.lastDayReset > oneDay) {
    user.dayRequests = 0;
    user.lastDayReset = now;
  }
}

// ============================================================
// VALIDATE API KEY
// ============================================================
function validateApiKey(req, res, next) {
  if (CONFIG.maintenance) {
    return res.status(503).json({
      error: 'API Under Maintenance',
      message: 'We are currently upgrading our systems.',
      contact: '@KINGFFAIAK47x'
    });
  }
  
  if (CONFIG.apiStatus === 'offline') {
    return res.status(503).json({
      error: 'API Offline',
      message: 'API is currently disabled.',
      contact: '@KINGFFAIAK47x'
    });
  }

  const apiKey = req.query.api_key || req.headers['x-api-key'];
  
  if (!apiKey) {
    return res.status(401).json({
      error: 'API Key Required',
      message: 'Please provide api_key parameter',
      get_key: 'Contact @KINGFFAIAK47x'
    });
  }

  let user = null;
  let username = null;
  for (const [key, value] of Object.entries(users)) {
    if (value.apiKey === apiKey) {
      user = value;
      username = key;
      break;
    }
  }

  if (!user) {
    return res.status(403).json({
      error: 'Invalid API Key',
      message: 'The API key provided is not valid',
      support: 'https://t.me/KINGFFAIAK47x'
    });
  }

  if (user.status === 'suspended') {
    return res.status(403).json({
      error: 'Account Suspended',
      message: 'Your account has been suspended.',
      support: 'https://t.me/KINGFFAIAK47x'
    });
  }

  checkAndResetLimits(user);

  let limits;
  if (user.plan === 'owner') {
    limits = CONFIG.rateLimit.owner;
  } else if (user.plan === 'user') {
    limits = CONFIG.rateLimit.user;
  } else {
    limits = CONFIG.rateLimit.free;
  }

  if (user.minuteRequests >= limits.perMinute) {
    return res.status(429).json({
      error: 'Rate Limit Exceeded (Minute)',
      message: 'You have exceeded ' + limits.perMinute + ' requests per minute',
      plan: user.plan,
      reset_in: Math.ceil((user.lastMinuteReset + 60000 - Date.now()) / 1000) + ' seconds'
    });
  }

  if (user.dayRequests >= limits.perDay) {
    return res.status(429).json({
      error: 'Rate Limit Exceeded (Daily)',
      message: 'You have exceeded ' + limits.perDay + ' requests per day',
      plan: user.plan,
      reset_at: new Date(user.lastDayReset + 86400000).toISOString()
    });
  }

  user.minuteRequests++;
  user.dayRequests++;
  systemStats.totalRequests++;
  
  if (CONFIG.logsEnabled) {
    usageLogs.push({
      username: username,
      apiKey: apiKey.substring(0, 8) + '...',
      timestamp: new Date().toISOString(),
      ip: req.ip || req.headers['x-forwarded-for'] || 'self',
      plan: user.plan
    });
    if (usageLogs.length > 1000) {
      usageLogs = usageLogs.slice(-500);
    }
  }

  req.user = { username: username, ...user };
  next();
}

// ============================================================
// INSTAGRAM SCANNER (SIMULATED - REAL DATA)
// ============================================================
async function scanInstagram(username) {
  try {
    // Using fetch to get real Instagram data
    const response = await fetch(`https://www.instagram.com/${username}/?__a=1&__d=1`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });

    if (!response.ok) {
      return {
        status: 'error',
        error: `Profile @${username} does not exist or is private`,
        code: 'INVALID_USER'
      };
    }

    const data = await response.json();
    const userData = data.graphql?.user || data.user;

    if (!userData) {
      return {
        status: 'error',
        error: `Profile @${username} not found`,
        code: 'INVALID_USER'
      };
    }

    return {
      status: 'ok',
      collected_at: new Date().toISOString(),
      profile: {
        id: userData.id,
        username: userData.username,
        full_name: userData.full_name || 'N/A',
        biography: userData.biography?.substring(0, 200) || 'No bio available',
        is_private: userData.is_private || false,
        is_verified: userData.is_verified || false,
        is_business_account: userData.is_business_account || false,
        is_professional_account: userData.is_professional_account || false,
        category_name: userData.category_name || null,
        business_category_name: userData.business_category_name || null,
        profile_pic_url_hd: userData.profile_pic_url_hd || userData.profile_pic_url,
        external_url: userData.external_url || null,
        followers: userData.edge_followed_by?.count || 0,
        following: userData.edge_follow?.count || 0,
        posts: userData.edge_owner_to_timeline_media?.count || 0,
        account_creation_year: 2012
      },
      USERNAME: '@KINGFFAIAK47x',
      MADE_BY: 'ANSH AFT'
    };
  } catch (error) {
    console.error('Instagram scan error:', error.message);
    return {
      status: 'error',
      error: error.message || 'Failed to scan profile',
      code: 'SCAN_ERROR'
    };
  }
}

// ============================================================
// ROUTES - STATIC FILES
// ============================================================
app.get('/login', (req, res) => {
  res.sendFile(path.join(__dirname, 'login.html'));
});

app.get('/dashboard', (req, res) => {
  const { username, password } = req.query;
  
  if (username && password) {
    if (username === CONFIG.adminUsername && password === CONFIG.adminPassword) {
      return res.sendFile(path.join(__dirname, 'dashboard.html'));
    } else {
      return res.redirect('/login?error=Invalid credentials');
    }
  }
  
  res.redirect('/login?error=Please login first');
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'login.html'));
});

// ============================================================
// API: SCAN PROFILE
// ============================================================
app.get('/api/scan', validateApiKey, async (req, res) => {
  const startTime = Date.now();
  const username = req.query.username;

  if (!username) {
    return res.status(400).json({
      status: 'error',
      code: 'NO_USERNAME',
      error: 'Username required',
      message: 'Please provide username parameter',
      example: '/api/scan?username=instagram&api_key=DEMOFUCK',
      MADE_BY: 'ANSH AFT',
      USERNAME: '@KINGFFAIAK47x'
    });
  }

  try {
    const result = await scanInstagram(username);
    
    // Add metadata
    if (result.status === 'ok') {
      const limits = CONFIG.rateLimit[req.user.plan] || CONFIG.rateLimit.user;
      result.api_key_used = req.user.apiKey.substring(0, 16) + '...';
      result.plan = req.user.plan;
      result.limit_minute = limits.perMinute;
      result.limit_day = limits.perDay;
      result.remaining_minute = limits.perMinute - req.user.minuteRequests;
      result.remaining_day = limits.perDay - req.user.dayRequests;
      result.response_time = Date.now() - startTime;
      result.developer = '@KINGFFAIAK47x';
      result.owner = 'ANSH AFT';
      result.channel = 'https://t.me/+iDnVRYTDnAJmNDE1';
    }

    // Save data periodically
    if (systemStats.totalRequests % 10 === 0) {
      saveData();
    }

    res.json(result);
  } catch (error) {
    res.status(500).json({
      status: 'error',
      error: error.message,
      code: 'SERVER_ERROR'
    });
  }
});

// ============================================================
// API: HEALTH
// ============================================================
app.get('/api/health', (req, res) => {
  res.json({
    status: 'running',
    timestamp: new Date().toISOString(),
    service: 'Instagram Scanner API',
    version: CONFIG.version,
    developer: 'KINGFFAIAK47x',
    owner: 'ANSH AFT',
    api_status: CONFIG.apiStatus,
    uptime: Math.floor((Date.now() - systemStats.startTime) / 1000)
  });
});

// ============================================================
// API: STATUS
// ============================================================
app.get('/api/status', (req, res) => {
  res.json({
    status: CONFIG.apiStatus,
    version: CONFIG.version,
    uptime: Math.floor((Date.now() - systemStats.startTime) / 1000),
    total_requests: systemStats.totalRequests,
    total_users: Object.keys(users).length,
    maintenance: CONFIG.maintenance,
    timestamp: new Date().toISOString(),
    developer: 'KINGFFAIAK47x',
    owner: 'ANSH AFT'
  });
});

// ============================================================
// ADMIN API ENDPOINTS
// ============================================================

// Admin Login
app.post('/admin/login', (req, res) => {
  const { username, password } = req.body;
  if (username === CONFIG.adminUsername && password === CONFIG.adminPassword) {
    res.json({ success: true, redirect: '/dashboard?username=' + username + '&password=' + password });
  } else {
    failedLogins.push({ 
      username, 
      timestamp: new Date().toISOString(), 
      ip: req.ip || req.headers['x-forwarded-for'] || 'unknown' 
    });
    saveData();
    res.json({ success: false });
  }
});

// Admin Stats - REAL-TIME DATA
app.get('/admin/stats', (req, res) => {
  const userList = Object.entries(users).map(([username, data]) => ({
    username,
    ...data,
    remaining_minute: CONFIG.rateLimit[data.plan]?.perMinute - data.minuteRequests || 0,
    remaining_day: CONFIG.rateLimit[data.plan]?.perDay - data.dayRequests || 0
  }));
  
  res.json({
    totalUsers: Object.keys(users).length,
    totalRequests: systemStats.totalRequests,
    ownerUsers: Object.values(users).filter(u => u.plan === 'owner').length,
    userUsers: Object.values(users).filter(u => u.plan === 'user').length,
    freeUsers: Object.values(users).filter(u => u.plan === 'free').length,
    apiStatus: CONFIG.apiStatus,
    theme: CONFIG.theme,
    version: CONFIG.version,
    users: userList,
    logs: usageLogs.slice(-50),
    failedLogins: failedLogins.slice(-20),
    announcements: announcements,
    uptime: Math.floor((Date.now() - systemStats.startTime) / 1000),
    maintenance: CONFIG.maintenance,
    logsEnabled: CONFIG.logsEnabled,
    timestamp: new Date().toISOString()
  });
});

// Update API Status
app.post('/admin/api-status', (req, res) => {
  const { status } = req.body;
  if (['online', 'maintenance', 'offline'].includes(status)) {
    CONFIG.apiStatus = status;
    saveData();
    res.json({ success: true, status: CONFIG.apiStatus });
  } else {
    res.json({ success: false, error: 'Invalid status' });
  }
});

// Update API Keys
app.post('/admin/update-keys', (req, res) => {
  const { ownerKey, userKey, freeKey } = req.body;
  if (ownerKey && users['ANSHAFT127987']) {
    users['ANSHAFT127987'].apiKey = ownerKey;
  }
  if (userKey && users['DEMO_USER']) {
    users['DEMO_USER'].apiKey = userKey;
  }
  if (freeKey && users['FREE_USER']) {
    users['FREE_USER'].apiKey = freeKey;
  }
  saveData();
  res.json({ success: true });
});

// Update Rate Limits
app.post('/admin/rate-limits', (req, res) => {
  const { userMin, userDay, ownerMin, ownerDay, freeMin, freeDay } = req.body;
  if (userMin) CONFIG.rateLimit.user.perMinute = parseInt(userMin);
  if (userDay) CONFIG.rateLimit.user.perDay = parseInt(userDay);
  if (ownerMin) CONFIG.rateLimit.owner.perMinute = parseInt(ownerMin);
  if (ownerDay) CONFIG.rateLimit.owner.perDay = parseInt(ownerDay);
  if (freeMin) CONFIG.rateLimit.free.perMinute = parseInt(freeMin);
  if (freeDay) CONFIG.rateLimit.free.perDay = parseInt(freeDay);
  saveData();
  res.json({ success: true });
});

// Update Theme
app.post('/admin/update-theme', (req, res) => {
  const { background, color, glowColor } = req.body;
  if (background) CONFIG.theme.background = background;
  if (color) CONFIG.theme.color = color;
  if (glowColor) CONFIG.theme.glowColor = glowColor;
  saveData();
  res.json({ success: true });
});

// Add User
app.post('/admin/add-user', (req, res) => {
  const { username, plan } = req.body;
  if (!username) {
    return res.json({ success: false, error: 'Username required' });
  }
  if (users[username]) {
    return res.json({ success: false, error: 'User already exists' });
  }
  
  let apiKey;
  if (plan === 'owner') {
    apiKey = username.toUpperCase() + '-OWNER-2026';
  } else if (plan === 'user') {
    apiKey = username.toUpperCase() + '-USER-2026';
  } else {
    apiKey = username.toUpperCase() + '-FREE-2026';
  }
  
  users[username] = {
    apiKey: apiKey,
    plan: plan || 'user',
    minuteRequests: 0,
    dayRequests: 0,
    lastMinuteReset: Date.now(),
    lastDayReset: Date.now(),
    createdAt: Date.now(),
    status: 'active'
  };
  
  saveData();
  res.json({ success: true, apiKey: apiKey });
});

// Delete User
app.post('/admin/delete-user', (req, res) => {
  const { username } = req.body;
  if (!users[username]) {
    return res.json({ success: false, error: 'User not found' });
  }
  if (username === 'ANSHAFT127987') {
    return res.json({ success: false, error: 'Cannot delete owner' });
  }
  delete users[username];
  saveData();
  res.json({ success: true });
});

// Toggle User
app.post('/admin/toggle-user', (req, res) => {
  const { username } = req.body;
  if (!users[username]) {
    return res.json({ success: false, error: 'User not found' });
  }
  users[username].status = users[username].status === 'active' ? 'suspended' : 'active';
  saveData();
  res.json({ success: true });
});

// Reset All
app.post('/admin/reset-all', (req, res) => {
  for (const key in users) {
    users[key].minuteRequests = 0;
    users[key].dayRequests = 0;
    users[key].lastMinuteReset = Date.now();
    users[key].lastDayReset = Date.now();
  }
  saveData();
  res.json({ success: true });
});

// Clear Logs
app.post('/admin/clear-logs', (req, res) => {
  usageLogs = [];
  saveData();
  res.json({ success: true });
});

// Clear Failed Logins
app.post('/admin/clear-failed-logins', (req, res) => {
  failedLogins = [];
  saveData();
  res.json({ success: true });
});

// Reset Config
app.post('/admin/reset-config', (req, res) => {
  CONFIG.rateLimit.user.perMinute = 100;
  CONFIG.rateLimit.user.perDay = 1000;
  CONFIG.rateLimit.owner.perMinute = 10000;
  CONFIG.rateLimit.owner.perDay = 100000;
  CONFIG.rateLimit.free.perMinute = 10;
  CONFIG.rateLimit.free.perDay = 100;
  CONFIG.theme.background = '#0a0a0a';
  CONFIG.theme.color = '#00ff41';
  CONFIG.theme.glowColor = '#00ff41';
  CONFIG.apiStatus = 'online';
  CONFIG.maintenance = false;
  CONFIG.logsEnabled = true;
  saveData();
  res.json({ success: true });
});

// Export Logs
app.get('/admin/export-logs', (req, res) => {
  const data = JSON.stringify({ 
    users, 
    logs: usageLogs.slice(-500), 
    stats: systemStats, 
    config: CONFIG, 
    failedLogins: failedLogins.slice(-100), 
    announcements 
  }, null, 2);
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Content-Disposition', 'attachment; filename=dark_panel_backup.json');
  res.send(data);
});

// Add Announcement
app.post('/admin/add-announcement', (req, res) => {
  const { message } = req.body;
  if (!message) {
    return res.json({ success: false, error: 'Message required' });
  }
  announcements.push({ id: Date.now(), message, timestamp: new Date().toISOString() });
  saveData();
  res.json({ success: true });
});

// Delete Announcement
app.post('/admin/delete-announcement', (req, res) => {
  const { id } = req.body;
  announcements = announcements.filter(a => a.id !== parseInt(id));
  saveData();
  res.json({ success: true });
});

// Toggle Logs
app.post('/admin/toggle-logs', (req, res) => {
  CONFIG.logsEnabled = !CONFIG.logsEnabled;
  saveData();
  res.json({ success: true, logsEnabled: CONFIG.logsEnabled });
});

// Toggle Maintenance
app.post('/admin/toggle-maintenance', (req, res) => {
  CONFIG.maintenance = !CONFIG.maintenance;
  saveData();
  res.json({ success: true, maintenance: CONFIG.maintenance });
});

// ============================================================
// REAL-TIME UPDATES (WebSocket - Optional)
// ============================================================
const server = require('http').createServer(app);
const io = require('socket.io')(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Send real-time updates every 5 seconds
setInterval(() => {
  const stats = {
    totalUsers: Object.keys(users).length,
    totalRequests: systemStats.totalRequests,
    uptime: Math.floor((Date.now() - systemStats.startTime) / 1000),
    apiStatus: CONFIG.apiStatus,
    maintenance: CONFIG.maintenance,
    timestamp: new Date().toISOString()
  };
  io.emit('stats_update', stats);
}, 5000);

io.on('connection', (socket) => {
  console.log('🔌 Client connected');
  socket.emit('connected', { message: 'Connected to real-time updates' });
});

// ============================================================
// START SERVER
// ============================================================
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log('='.repeat(60));
  console.log('🔥 INSTAGRAM SCANNER API v3.0 (REAL-TIME)');
  console.log('='.repeat(60));
  console.log('👑 Owner: ANSH_AFT');
  console.log('💻 Developer: KINGFFAIAK47x');
  console.log('='.repeat(60));
  console.log('📊 Dashboard: /dashboard?username=ANSHAFT127987&password=ANSHAFTAK47');
  console.log('📊 API Scan: /api/scan?username=instagram&api_key=DEMOFUCK');
  console.log('📊 Health: /api/health');
  console.log('📊 Status: /api/status');
  console.log('='.repeat(60));
  console.log('🔑 API Keys:');
  console.log('   ⭐ Premium: ANSHAFTAK472026');
  console.log('   🆓 User: DEMOFUCK');
  console.log('='.repeat(60));
  console.log('✅ Server running on port ' + PORT);
});
