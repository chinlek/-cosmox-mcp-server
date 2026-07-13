#!/bin/bash
# Setup hourly token refresh via cron

REFRESH_SCRIPT="/nobackup/lcv/cosmox-mcp-server/refresh_token.py"
PYTHON="/auto/smartdev/bin/python3.10"
LOG_FILE="/nobackup/lcv/cosmox-mcp-server/.token-refresh.log"

echo "="
echo "🔄 COSMOX Token Refresh - Cron Setup"
echo "="
echo ""

# Check if script exists
if [ ! -f "$REFRESH_SCRIPT" ]; then
    echo "❌ Error: $REFRESH_SCRIPT not found"
    exit 1
fi

echo "1️⃣  Checking current cron jobs..."
echo ""
crontab -l 2>/dev/null | grep -q "refresh_token.py" && echo "   ⚠️  Refresh job already exists" || echo "   ℹ️  No existing refresh job"
echo ""

echo "2️⃣  Setup options:"
echo ""
echo "   Option A: Quick setup (auto-refresh every 55 minutes)"
echo "      Run: bash /nobackup/lcv/cosmox-mcp-server/setup_cron.sh auto"
echo ""
echo "   Option B: View current cron jobs"
echo "      Run: crontab -l"
echo ""
echo "   Option C: Manual refresh (no cron)"
echo "      Run: $PYTHON $REFRESH_SCRIPT --manual"
echo ""
echo "   Option D: Check token status"
echo "      Run: $PYTHON $REFRESH_SCRIPT --check"
echo ""

if [ "$1" = "auto" ]; then
    echo "3️⃣  Setting up cron job..."
    echo ""

    # Create cron entry
    # Run at 55 minutes of every hour (before 1-hour expiry at :00)
    CRON_ENTRY="55 * * * * $PYTHON $REFRESH_SCRIPT >> $LOG_FILE 2>&1"

    # Add to crontab if not already present
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

    echo "   ✅ Cron job added!"
    echo ""
    echo "   Job runs: Every hour at :55 (e.g., 10:55, 11:55, etc.)"
    echo "   Log file: $LOG_FILE"
    echo ""
    echo "4️⃣  Verify setup:"
    echo "   Run: crontab -l | grep refresh_token"
    echo ""
    echo "5️⃣  Manual refresh (do this first!):"
    echo "   Run: $PYTHON $REFRESH_SCRIPT --manual"
    echo ""
fi
