# COSMOX MCP - Automated Token Refresh Setup

**Problem:** COSMOX tokens expire in 1 hour and need manual refresh to use authenticated metrics.

**Solution:** Automated cron-based token refresh with manual token input.

---

## ⚠️ Current Token Status

```bash
/auto/smartdev/bin/python3.10 /nobackup/lcv/cosmox-mcp-server/refresh_token.py --check
```

---

## 🚀 Setup Steps

### Step 1: Get Your First Fresh Token (Manual)

1. Open browser → https://cosmosx.cisco.com
2. **Log in completely** (wait 5-10 seconds for full page load)
3. Press **F12** (Developer Tools)
4. Go to **Application** → **Storage** → **localStorage**
5. Find `access_token` key
6. **Right-click** → **Copy Value** (get the entire long string)
7. Run refresh script:

```bash
/auto/smartdev/bin/python3.10 /nobackup/lcv/cosmox-mcp-server/refresh_token.py --manual
```

8. **Paste the token** when prompted
9. Script verifies it's valid and updates `.env`

---

### Step 2: Setup Hourly Auto-Refresh via Cron

Once you have a valid token in `.env`, set up cron:

```bash
bash /nobackup/lcv/cosmox-mcp-server/setup_cron.sh auto
```

This adds a cron job that runs every hour at **:55** (e.g., 10:55, 11:55, etc.)
- Runs before token expiry
- Quietly logs to: `/nobackup/lcv/cosmox-mcp-server/.token-refresh.log`

---

### Step 3: Verify Cron Setup

```bash
crontab -l | grep refresh_token
```

Should output:
```
55 * * * * /auto/smartdev/bin/python3.10 /nobackup/lcv/cosmox-mcp-server/refresh_token.py >> /nobackup/lcv/cosmox-mcp-server/.token-refresh.log 2>&1
```

---

## 📋 Available Commands

| Command | Purpose |
|---------|---------|
| `python3.10 refresh_token.py --check` | Check current token status |
| `python3.10 refresh_token.py --manual` | Manually refresh token (paste from browser) |
| `bash setup_cron.sh auto` | Setup hourly cron job |
| `crontab -l` | View all cron jobs |
| `tail -f .token-refresh.log` | Watch refresh logs |

---

## 🔄 How It Works

```
Every hour at :55 minutes
         ↓
Cron runs refresh_token.py
         ↓
Script checks if token expires within 30 min
         ↓
If yes: Alerts user to run --manual refresh
If no:  Logs "still valid" and exits quietly
         ↓
Token stays fresh for next 24 hours after manual refresh
```

---

## ⚠️ Important Notes

1. **First token must be manual** (copy from browser localStorage)
2. **Cron job only checks** - it doesn't auto-login
3. **Browser login still required** every ~55 minutes to refresh
4. **Why not fully automated?**
   - Requires SSO integration (complex)
   - Requires stored credentials (security risk)
   - Manual refresh every 55 min is simpler for occasional use

---

## 🎯 When to Use Each Approach

| Use Case | Approach | Effort |
|----------|----------|--------|
| Occasional testing | Manual only (`--manual`) | 2 min |
| Daily monitoring | Cron + hourly browser login | 5 min setup |
| Production 24/7 | Get service token from COSMOX team | Contact them |
| No auth needed | Use only 6 no-token metrics | 0 |

---

## 📊 No-Token Metrics (Always Available)

If you don't want to bother with token refresh, these 6 metrics work forever:

- `config` - Suite configuration & ownership
- `pass_rate` - Test success rates
- `timing` - Execution timing metrics
- `violations` - Policy violations
- `violation_count` - Violation trends
- `violations_trend` - Historical trends

Suggested MCP configuration: Use only no-token metrics + provide all 6 as MCP tools.

---

## ❓ Troubleshooting

**Token expired immediately after refresh?**
- Make sure you're at https://cosmosx.cisco.com (not just logged in elsewhere)
- Log out completely first, then log in fresh
- Wait full 10 seconds for page to load before copying token

**Cron job not running?**
```bash
# Check if cron is running
ps aux | grep cron

# Check logs
tail -50 /nobackup/lcv/cosmox-mcp-server/.token-refresh.log
```

**Token keeps being invalid?**
- Paste entire token (should be ~1500 characters with colon)
- Format: `JWT1:JWT2` (two JWTs separated by colon)

---

## 📝 Next Steps

1. Get fresh token: `python3.10 refresh_token.py --manual`
2. Check it works: `python3.10 refresh_token.py --check`
3. Setup cron: `bash setup_cron.sh auto`
4. Verify: `crontab -l`

Then authenticated metrics should work until you need to manually refresh again!
