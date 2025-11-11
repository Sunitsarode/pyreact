import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import websocket from '../services/websocket';
import ScoreDisplay from '../components/ScoreDisplay';
import IntervalBreakdown from '../components/IntervalBreakdown';
import CandlestickChart from '../components/CandlestickChart';
import IndicatorsChart from '../components/IndicatorsChart';
import AlertRules from '../components/AlertRules';
import { API_URL } from '../utils/api';
/*
const getApiURL = () => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:5001/api`;
  }
  return 'http://localhost:5001/api';
};

const API_URL = getApiURL(); */

export default function SymbolPage() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [settings, setSettings] = useState({});
  const [connected, setConnected] = useState(false);
  const [currentScore, setCurrentScore] = useState({
    timestamp: 0,
    weighted_total_score: 0,
    intervals: {}
  });
  const [scoreHistory, setScoreHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [validSymbol, setValidSymbol] = useState(true);

  useEffect(() => {
    validateSymbol();
    loadSettings();
    loadScoreHistory();
  }, [symbol]);

  useEffect(() => {
    websocket.connect();

    websocket.on('connect', () => setConnected(true));
    websocket.on('disconnect', () => setConnected(false));
    
    websocket.on('score_update', (data) => {
      if (data.symbol === symbol) {
        setCurrentScore(data);
        setScoreHistory(prev => [...prev, data].slice(-100));
      }
    });

    websocket.on('alert', (data) => {
      if (data.symbol === symbol) {
        setAlerts(prev => [data, ...prev].slice(0, 10));
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
  }, [symbol]);

  useEffect(() => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const validateSymbol = async () => {
    try {
      const response = await axios.get(`${API_URL}/symbols`);
      if (!response.data.includes(symbol)) {
        setValidSymbol(false);
      }
    } catch (error) {
      console.error('Error validating symbol:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API_URL}/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const loadScoreHistory = async () => {
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

  if (!validSymbol) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 p-6 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-12 text-center max-w-md">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-3xl font-bold text-gray-800 mb-4">Symbol Not Found</h2>
          <p className="text-gray-600 mb-6">
            The symbol <strong>{symbol}</strong> is not configured in the current settings.
          </p>
          <button
            onClick={() => navigate('/')}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header with Back Button */}
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <div className="flex justify-between items-center flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-semibold transition flex items-center gap-2"
              >
                ← Dashboard
              </button>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                  {symbol}
                </h1>
                <p className="text-gray-600 text-sm">Live Trading Analysis</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
              <span className="text-gray-600 font-semibold">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          
          <div className="mt-4 text-sm text-gray-600 flex gap-6 flex-wrap">
            <span>⏱️ Update: Every {settings.updateIntervalMinutes || 5} min</span>
            <span>📈 Intervals: {settings.intervals?.join(', ') || 'N/A'}</span>
            <span>🔔 Alerts: {settings.notifications?.enabled ? 'Enabled' : 'Disabled'}</span>
          </div>
        </div>

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
          symbol={symbol}
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
            symbol={symbol}
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