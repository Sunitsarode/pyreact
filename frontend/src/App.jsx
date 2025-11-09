import { useState, useEffect } from 'react';
import axios from 'axios';
import websocket from './services/websocket';
import Header from './components/Header';
import ScoreDisplay from './components/ScoreDisplay';
import IntervalBreakdown from './components/IntervalBreakdown';
import CandlestickChart from './components/CandlestickChart';
import IndicatorsChart from './components/IndicatorsChart';
import AlertRules from './components/AlertRules';

// At the top of each file
const getApiURL = () => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:5001/api`;
  }
  return 'http://localhost:5001/api';
};

const API_URL = getApiURL();

function App() {
  const [symbols, setSymbols] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC-USD');
  const [settings, setSettings] = useState({});
  const [connected, setConnected] = useState(false);
  const [currentScore, setCurrentScore] = useState({
    timestamp: 0,
    weighted_total_score: 0,
    intervals: {}
  });
  const [scoreHistory, setScoreHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);

  // Load settings and symbols on mount
  useEffect(() => {
    loadSettings();
    loadSymbols();
    loadScoreHistory(selectedSymbol);
  }, []);

  // Connect WebSocket
  useEffect(() => {
    websocket.connect();

    websocket.on('connect', () => setConnected(true));
    websocket.on('disconnect', () => setConnected(false));
    
    websocket.on('score_update', (data) => {
      if (data.symbol === selectedSymbol) {
        setCurrentScore(data);
        setScoreHistory(prev => [...prev, data].slice(-100));
      }
    });

    websocket.on('alert', (data) => {
      if (data.symbol === selectedSymbol) {
        setAlerts(prev => [data, ...prev].slice(0, 10));
        // Show browser notification if permitted
        if (Notification.permission === 'granted') {
          new Notification(`${data.type} - ${data.symbol}`, {
            body: data.message,
            icon: '📊'
          });
        }
      }
    });

    return () => {
      websocket.disconnect();
    };
  }, [selectedSymbol]);

  // Request notification permission
  useEffect(() => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API_URL}/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const loadSymbols = async () => {
    try {
      const response = await axios.get(`${API_URL}/symbols`);
      setSymbols(response.data);
      if (response.data.length > 0) {
        setSelectedSymbol(response.data[0]);
      }
    } catch (error) {
      console.error('Error loading symbols:', error);
    }
  };

  const loadScoreHistory = async (symbol) => {
    try {
      const response = await axios.get(`${API_URL}/scores/${symbol}/history?limit=100`);
      setScoreHistory(response.data);
      if (response.data.length > 0) {
        setCurrentScore(response.data[response.data.length - 1]);
      }
    } catch (error) {
      console.error('Error loading score history:', error);
    }
  };

  const handleSymbolChange = (symbol) => {
    setSelectedSymbol(symbol);
    setScoreHistory([]);
    setAlerts([]);
    loadScoreHistory(symbol);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <Header
          symbols={symbols}
          selectedSymbol={selectedSymbol}
          onSymbolChange={handleSymbolChange}
          connected={connected}
          settings={settings}
        />

        {/* Alerts Banner */}
        {alerts.length > 0 && (
          <div className="bg-white rounded-2xl shadow-xl p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-800">🔔 Recent Alerts</h3>
              <button 
                onClick={() => setAlerts([])}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
            </div>
            <div className="mt-2 space-y-2">
              {alerts.map((alert, idx) => (
                <div 
                  key={idx}
                  className={`p-3 rounded-lg text-sm ${
                    alert.type === 'STRONG_BUY' ? 'bg-green-100 text-green-800' :
                    alert.type === 'STRONG_SELL' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  <strong>{alert.type}:</strong> {alert.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Current Score Display */}
        <ScoreDisplay 
          score={currentScore} 
          settings={settings}
        />

        {/* Interval Breakdown */}
        <IntervalBreakdown 
          intervals={currentScore.intervals || {}}
          weights={settings.timeframeWeights || {}}
        />

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Candlestick Chart */}
          <CandlestickChart 
            symbol={selectedSymbol}
            intervals={settings.intervals || []}
          />

          {/* Indicators Score Chart */}
          <IndicatorsChart 
            scoreHistory={scoreHistory}
            threshold={settings.breakout_rules?.total_score_threshold || 30}
          />
        </div>

        {/* Alert Rules */}
        <AlertRules settings={settings} />
      </div>
    </div>
  );
}

export default App;
