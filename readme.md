# 📊 Live Analyser - Multi-Timeframe Trading Score System

Real-time multi-timeframe trading indicator score calculator with **Flask + React + ApexCharts**, WebSocket live updates, SQLite database storage, and Telegram alerts.

## 🎯 Features

- ✅ **Multi-Timeframe Analysis** - Calculates scores across 5 timeframes (1d, 1h, 15m, 5m, 1m)
- ✅ **Weighted Scoring** - Customizable weights for each timeframe
- ✅ **6 Technical Indicators** - RSI, MACD, ADX, Bollinger Bands, SMA, Supertrend
- ✅ **Support/Resistance** - Auto-calculated pivot points per interval
- ✅ **Real-time Updates** - WebSocket streaming every 5 minutes
- ✅ **SQLite Storage** - One database per symbol with auto-cleanup
- ✅ **Candlestick Charts** - ApexCharts with S/R levels
- ✅ **Multi-line Indicators Chart** - Toggle individual indicators
- ✅ **Telegram/Ntfy Alerts** - Notifications for breakout signals
- ✅ **React Frontend** - Modern responsive UI with Tailwind CSS

## 🗂️ Project Structure

```
live-analyser/
├── backend/
│   ├── app.py                 # Flask + WebSocket + REST API
│   ├── db_manager.py          # SQLite operations with auto-cleanup
│   ├── indicators.py          # Technical indicators + support/resistance
│   ├── data_fetcher.py        # Yahoo Finance data fetcher
│   ├── notifications.py       # Telegram/Ntfy alerts
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── ScoreDisplay.jsx
│   │   │   ├── IntervalBreakdown.jsx
│   │   │   ├── CandlestickChart.jsx    # ApexCharts candlestick
│   │   │   ├── IndicatorsChart.jsx     # ApexCharts multi-line
│   │   │   └── AlertRules.jsx
│   │   ├── services/
│   │   │   └── websocket.js            # Socket.io client
│   │   ├── App.jsx
│   │   ├── index.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── db/                        # Database folder (auto-created)
│   ├── BTC-USD.sqlite
│   └── ETH-USD.sqlite
├── settings.json              # Configuration
├── start.bat                  # Windows startup script
├── start.sh                   # Linux/Mac startup script
└── README.md
```

## 📦 Installation

### Prerequisites
- **Python 3.8+**
- **Node.js 18+**
- **npm or yarn**

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

## 🚀 Quick Start

### Option 1: Using Start Scripts (Recommended)

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Application

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:5001/api/symbols

## 🗄️ Database Structure

Each symbol gets its own SQLite database in `db/{symbol}.sqlite`:

### Tables Created:

**Candles Tables (per interval):**
```sql
candles_1day, candles_1hr, candles_15min, candles_5min, candles_1min
- timestamp (PRIMARY KEY)
- open, high, low, close, volume
```

**Indicators Score Table:**
```sql
indicators_score
- timestamp (UNIQUE)
- score_1d, score_1h, score_15m, score_5m, score_1m
- support_1d, resistance_1d, support_1h, resistance_1h, ...
- weighted_total_score
```

### Auto-Cleanup

Old data is automatically deleted to keep database small:
- **Candles:** Keeps last N candles (configurable in `settings.json`)
- **Scores:** Keeps last 500 scores

## ⚙️ Configuration (`settings.json`)

```json
{
  "symbols": ["BTC-USD", "ETH-USD"],
  "intervals": ["1d", "1h", "15m", "5m", "1m"],
  "updateIntervalMinutes": 5,
  
  "candlesPerInterval": {
    "1m": 100,
    "5m": 100,
    "15m": 100,
    "1h": 100,
    "1d": 100
  },
  
  "maxCandlesStored": {
    "1m": 100,
    "5m": 100,
    "15m": 100,
    "1h": 100,
    "1d": 200
  },
  
  "timeframeWeights": {
    "1d": 0.35,
    "1h": 0.25,
    "15m": 0.20,
    "5m": 0.15,
    "1m": 0.05
  },
  
  "api_server": {
    "host": "0.0.0.0",
    "port": 5001
  },
  
  "frontend_server": {
    "port": 3000
  },
  
  "notifications": {
    "enabled": false,
    "method": "telegram",
    "telegram": {
      "token": "YOUR_BOT_TOKEN",
      "chat_id": "YOUR_CHAT_ID"
    }
  },
  
  "breakout_rules": {
    "total_score_threshold": 30,
    "rsi_overbought": 70,
    "rsi_oversold": 30
  }
}
```

### Key Parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `candlesPerInterval` | Candles to fetch per update | `100` |
| `maxCandlesStored` | Max candles stored in DB (auto-cleanup) | `100-200` |
| `updateIntervalMinutes` | Update frequency | `5` |
| `timeframeWeights` | Weight for each timeframe | See above |
| `total_score_threshold` | Alert trigger level | `30` |

## 📡 API Endpoints

### REST API

| Endpoint | Description |
|----------|-------------|
| `GET /api/symbols` | List all symbols |
| `GET /api/settings` | Get configuration |
| `GET /api/candles/<symbol>/<interval>` | Get OHLCV data |
| `GET /api/scores/<symbol>` | Latest score for symbol |
| `GET /api/scores/<symbol>/history` | Score history (100 points) |

### WebSocket Events

```javascript
// Connect to WebSocket
socket.on('score_update', (data) => {
  // { symbol, timestamp, weighted_total_score, intervals }
});

socket.on('alert', (data) => {
  // { symbol, type, message, timestamp }
});
```

## 📊 Charts

### 1. Candlestick Chart (ApexCharts)
- OHLCV data for selected interval
- Support/Resistance lines overlaid
- Zoom/Pan controls
- Real-time updates every 30 seconds

### 2. Indicators Score Chart (ApexCharts)
- Multi-line chart with 6 indicators:
  - **RSI** (Purple)
  - **MACD** (Blue)
  - **ADX** (Orange)
  - **Bollinger Bands** (Green)
  - **SMA** (Cyan)
  - **Supertrend** (Red)
- Toggle indicators on/off
- Threshold lines at +30, 0, -30
- Smooth animations

## 🔔 Notification Setup

### Telegram

1. Create bot: [@BotFather](https://t.me/botfather)
2. Get Chat ID: [@userinfobot](https://t.me/userinfobot)
3. Update `settings.json`:

```json
{
  "notifications": {
    "enabled": true,
    "method": "telegram",
    "telegram": {
      "token": "123456:ABC-DEF...",
      "chat_id": "987654321"
    }
  }
}
```

### Ntfy.sh (Simpler Alternative)

```json
{
  "notifications": {
    "enabled": true,
    "method": "ntfy",
    "ntfy": {
      "endpoint": "https://ntfy.sh/my-trading-alerts"
    }
  }
}
```

Subscribe: https://ntfy.sh/my-trading-alerts

## 🧪 Testing

### 1. Test Backend

```bash
cd backend
python app.py
```

Check console output:
```
📊 Updating BTC-USD - 2025-11-05 10:30:00
✅ 1d: Score = -37.3 | S/R = 96213.17 / 113524.42
✅ 1h: Score = -17.1 | S/R = 100416.64 / 105164.32
🎯 Final Weighted Score: -7.68
💾 Saved to database: db/BTC-USD.sqlite
```

Test API:
```bash
curl http://localhost:5001/api/symbols
curl http://localhost:5001/api/scores/BTC-USD
```

### 2. Test Frontend

```bash
cd frontend
npm run dev
```

Open: http://localhost:3000

Check browser console for WebSocket connection:
```
✅ WebSocket Connected
📊 Score update: {...}
```

## 🛠️ Troubleshooting

### Backend Issues

**No data fetching:**
- Check internet connection
- Verify symbol format (Yahoo Finance)
- Check console for errors

**Database not created:**
- Check `db/` folder permissions
- Verify Python has write access

### Frontend Issues

**WebSocket not connecting:**
- Ensure backend is running on port 5001
- Check browser console for CORS errors
- Verify `BACKEND_URL` in `websocket.js`

**Charts not showing:**
- Wait 5 minutes for first data update
- Check browser console for errors
- Verify API endpoints are responding

### Common Errors

**"Module not found":**
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

**"Port already in use":**
- Change ports in `settings.json`
- Kill existing processes

## 📈 Performance Tips

1. **Reduce Update Frequency:** Set `updateIntervalMinutes: 10` (less API calls)
2. **Limit Stored Candles:** Reduce `maxCandlesStored` values
3. **Fewer Intervals:** Remove `1m` and `5m` for less frequent trading
4. **Database Cleanup:** Periodically delete old `db/*.sqlite` files

## 🔒 Security

- Never commit `settings.json` with real tokens
- Add to `.gitignore`:
  ```
  settings.json
  db/*.sqlite
  ```
- Use environment variables for production tokens
- Run behind reverse proxy (nginx) in production

## 📜 License

MIT License - Free to use and modify!

## 🙏 Credits

Built with:
- **Flask** - Backend API
- **React** - Frontend UI
- **ApexCharts** - Beautiful charts
- **Socket.io** - Real-time updates
- **Tailwind CSS** - Styling
- **Yahoo Finance** - Market data
- **pandas-ta** - Technical indicators

---

**Happy Trading! 📈💰**
