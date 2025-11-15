import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import websocket from '../services/websocket';
import { API_URL } from '../utils/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const [symbols, setSymbols] = useState([]);
  const [symbolData, setSymbolData] = useState({});
  const [connected, setConnected] = useState(false);
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('📊 Dashboard mounted');
    loadSettings();
    loadSymbols();
    
    // Connect WebSocket
    websocket.connect();
    websocket.on('connect', () => {
      console.log('✅ WebSocket connected in Dashboard');
      setConnected(true);
    });
    websocket.on('disconnect', () => {
      console.log('❌ WebSocket disconnected in Dashboard');
      setConnected(false);
    });
    
    websocket.on('score_update', (data) => {
      console.log('📊 Dashboard received score update for:', data.symbol);
      setSymbolData(prev => ({
        ...prev,
        [data.symbol]: data
      }));
    });

    return () => {
      // Don't disconnect here, other pages might be using it
      console.log('📊 Dashboard unmounting');
    };
  }, []);

  const loadSettings = async () => {
    try {
      console.log('⚙️ Loading settings from:', `${API_URL}/settings`);
      const response = await axios.get(`${API_URL}/settings`);
      console.log('✅ Settings loaded:', response.data);
      setSettings(response.data);
    } catch (error) {
      console.error('❌ Error loading settings:', error);
      console.error('Error details:', error.response?.data || error.message);
      setError('Failed to load settings');
    }
  };

  const loadSymbols = async () => {
    try {
      console.log('📈 Loading symbols from:', `${API_URL}/symbols`);
      const response = await axios.get(`${API_URL}/symbols`);
      console.log('✅ Symbols loaded:', response.data);
      setSymbols(response.data);
      
      // Load latest scores for all symbols
      for (const symbol of response.data) {
        try {
          console.log(`📊 Loading score for ${symbol}`);
          const scoreResponse = await axios.get(`${API_URL}/scores/${symbol}`);
          if (scoreResponse.data && Object.keys(scoreResponse.data).length > 0) {
            console.log(`✅ Score loaded for ${symbol}:`, scoreResponse.data.master_score);
            setSymbolData(prev => ({
              ...prev,
              [symbol]: scoreResponse.data
            }));
          } else {
            console.warn(`⚠️ No score data for ${symbol}`);
          }
        } catch (error) {
          console.error(`❌ Error loading score for ${symbol}:`, error.message);
        }
      }
      setLoading(false);
    } catch (error) {
      console.error('❌ Error loading symbols:', error);
      console.error('Error details:', error.response?.data || error.message);
      setError('Failed to load symbols');
      setLoading(false);
    }
  };

  const getScoreColor = (classification) => {
    if (classification?.includes('BULLISH')) return 'from-green-500 to-green-600';
    if (classification?.includes('BEARISH')) return 'from-red-500 to-red-600';
    return 'from-blue-500 to-blue-600';
  };

  const getScoreTextColor = (score) => {
    const threshold = settings.breakout_rules?.total_score_threshold || 30;
    if (score > threshold) return 'text-green-600';
    if (score < -threshold) return 'text-red-600';
    return 'text-blue-600';
  };

  const getScoreStatus = (classification) => {
    if (classification === 'STRONG_BULLISH') return { icon: '🚀', text: 'STRONG BULL' };
    if (classification === 'BULLISH') return { icon: '📈', text: 'BULLISH' };
    if (classification === 'STRONG_BEARISH') return { icon: '⚠️', text: 'STRONG BEAR' };
    if (classification === 'BEARISH') return { icon: '📉', text: 'BEARISH' };
    return { icon: '↔️', text: 'NEUTRAL' };
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 p-6 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-12 text-center max-w-md">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-3xl font-bold text-gray-800 mb-4">Connection Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <div className="flex justify-between items-center flex-wrap gap-4">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-2">
                📊 Live Analyser Dashboard
              </h1>
              <p className="text-gray-600">Select a symbol to view detailed analysis</p>
            </div>
            
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
              <span className="text-gray-600 font-semibold">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          
          {/* Settings Info */}
          <div className="mt-4 text-sm text-gray-600 flex gap-6 flex-wrap">
            <span>⏱️ Update: Every {settings.updateIntervalMinutes || 5} min</span>
            <span>📈 Intervals: {settings.intervals?.join(', ') || 'N/A'}</span>
            <span>📊 Symbols: {symbols.length}</span>
          </div>
        </div>

        {/* Symbol Cards Grid */}
        {loading ? (
          <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-xl text-gray-600">Loading symbols...</p>
          </div>
        ) : symbols.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {symbols.map(symbol => {
              const data = symbolData[symbol] || {};
              const score = data.master_score || 0;
              const classification = data.classification || 'NEUTRAL';
              const price = data.current_price || 0;
              const status = getScoreStatus(classification);
              
              return (
                <div
                  key={symbol}
                  onClick={() => {
                    console.log(`🔗 Navigating to /${symbol}`);
                    navigate(`/${symbol}`);
                  }}
                  className="bg-white rounded-2xl shadow-xl p-6 cursor-pointer transform transition-all hover:scale-105 hover:shadow-2xl"
                >
                  {/* Symbol Header */}
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-2xl font-bold text-gray-800">{symbol}</h3>
                      <p className="text-sm text-gray-500">
                        {data.timestamp ? new Date(data.timestamp * 1000).toLocaleTimeString() : 'Waiting...'}
                      </p>
                    </div>
                    <div className="text-3xl">{status.icon}</div>
                  </div>

                  {/* Current Price */}
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 mb-1">Current Price</p>
                    <p className="text-3xl font-bold text-gray-900">
                      ${price.toFixed(2)}
                    </p>
                  </div>

                  {/* Score Display */}
                  <div className={`bg-gradient-to-r ${getScoreColor(classification)} rounded-xl p-4 text-white mb-3`}>
                    <p className="text-sm opacity-90 mb-1">Master Score</p>
                    <div className="flex justify-between items-center">
                      <p className="text-4xl font-bold">{score.toFixed(1)}</p>
                      <p className="text-lg font-semibold">{status.text}</p>
                    </div>
                  </div>

                  {/* Mini Progress Bar */}
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                    <div 
                      className={`h-2 rounded-full bg-gradient-to-r ${getScoreColor(classification)}`}
                      style={{ width: `${((score + 100) / 200) * 100}%` }}
                    ></div>
                  </div>

                  {/* Quick Stats */}
                  {data.intervals && Object.keys(data.intervals).length > 0 && (
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.keys(data.intervals).slice(0, 2).map(interval => (
                        <div key={interval} className="bg-gray-50 rounded p-2">
                          <p className="text-gray-500 uppercase">{interval}</p>
                          <p className={`font-bold ${getScoreTextColor(data.intervals[interval].total_score)}`}>
                            {data.intervals[interval].total_score?.toFixed(1) || '0'}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Click Hint */}
                  <div className="mt-4 text-center text-sm text-gray-500">
                    Click to view detailed analysis →
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <p className="text-xl text-gray-600">No symbols configured</p>
            <p className="text-sm text-gray-500 mt-2">Check your settings.json file</p>
          </div>
        )}

      </div>
    </div>
  );
}