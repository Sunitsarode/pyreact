import { useState } from 'react';
import ReactApexChart from 'react-apexcharts';
import { API_URL } from '../utils/api';
// At the top of each file
/*const getApiURL = () => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:5001/api`;
  }
  return 'http://localhost:5001/api';
};

const API_URL = getApiURL();*/
console.log('🔍 IndicatorsChart.jsx API_URL:', API_URL);  // ← Add this line

export default function IndicatorsChart({ scoreHistory, threshold }) {
  const [selectedInterval, setSelectedInterval] = useState('5m'); // DEFAULT 5min
  const [visibleIndicators, setVisibleIndicators] = useState({
    avgScore: true,
    rsi: false,
    macd: false,
    adx: false,
    supertrend: false
  });

  const intervals = ['1m', '5m', '1h']; // UPDATED: Only these 3

  const toggleIndicator = (indicator) => {
    setVisibleIndicators(prev => ({
      ...prev,
      [indicator]: !prev[indicator]
    }));
  };

  const timestamps = scoreHistory.map(s => s.timestamp * 1000);
  
  // Get avg_total_score for selected interval
  const getAvgScoreData = () => {
    return scoreHistory.map(s => {
      const intervalData = s.intervals?.[selectedInterval];
      return intervalData?.avg_total_score || 0;
    });
  };

  // Get individual indicator scores
  const getRsiData = () => {
    return scoreHistory.map(s => s.intervals?.[selectedInterval]?.rsi_score || 0);
  };

  const getMacdData = () => {
    return scoreHistory.map(s => s.intervals?.[selectedInterval]?.macd_score || 0);
  };

  const getAdxData = () => {
    return scoreHistory.map(s => s.intervals?.[selectedInterval]?.adx_score || 0);
  };

  const getSupertrendData = () => {
    return scoreHistory.map(s => s.intervals?.[selectedInterval]?.supertrend_score || 0);
  };

  const indicatorConfig = {
    avgScore: { name: 'Avg Total Score', color: '#FF0000', data: getAvgScoreData() },
    rsi: { name: 'RSI Score', color: '#9333EA', data: getRsiData() },
    macd: { name: 'MACD Score', color: '#3B82F6', data: getMacdData() },
    adx: { name: 'ADX Score', color: '#F97316', data: getAdxData() },
    supertrend: { name: 'Supertrend Score', color: '#EF4444', data: getSupertrendData() }
  };

  const series = Object.entries(indicatorConfig)
    .filter(([key]) => visibleIndicators[key])
    .map(([key, config]) => ({
      name: config.name,
      data: config.data.map((val, idx) => ({
        x: timestamps[idx],
        y: val
      })),
      color: config.color
    }));

  const chartOptions = {
    chart: {
      type: 'line',
      height: 450,
      toolbar: { show: true },
      zoom: { enabled: true }
    },
    title: {
      text: `Indicator Scores - ${selectedInterval.toUpperCase()}`,
      align: 'left'
    },
    stroke: {
      width: 2,
      curve: 'smooth'
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeFormatter: {
          hour: 'HH:mm',
          day: 'dd MMM'
        }
      }
    },
    yaxis: {
      min: -100,
      max: 100,
      tickAmount: 10
    },
    annotations: {
      yaxis: [
        {
          y: threshold,
          borderColor: '#10B981',
          label: { text: `+${threshold}` }
        },
        {
          y: 0,
          borderColor: '#3B82F6',
          label: { text: '0' }
        },
        {
          y: -threshold,
          borderColor: '#EF4444',
          label: { text: `-${threshold}` }
        }
      ]
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">📉 Indicators Score</h2>
        
        <select
          value={selectedInterval}
          onChange={(e) => setSelectedInterval(e.target.value)}
          className="px-3 py-1 border-2 border-gray-300 rounded-lg"
        >
          {intervals.map(interval => (
            <option key={interval} value={interval}>{interval.toUpperCase()}</option>
          ))}
        </select>
      </div>

      {/* Toggle Buttons - ONLY 5 indicators */}
      <div className="flex flex-wrap gap-2 mb-4">
        {Object.entries(indicatorConfig).map(([key, config]) => (
          <button
            key={key}
            onClick={() => toggleIndicator(key)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold ${
              visibleIndicators[key] ? 'text-white' : 'bg-gray-200 text-gray-600'
            }`}
            style={{
              backgroundColor: visibleIndicators[key] ? config.color : undefined
            }}
          >
            {config.name}
          </button>
        ))}
      </div>

      {scoreHistory.length > 0 ? (
        <ReactApexChart
          options={chartOptions}
          series={series}
          type="line"
          height={450}
        />
      ) : (
        <div className="h-96 flex items-center justify-center text-gray-400">
          <p>⏳ Waiting for data...</p>
        </div>
      )}
    </div>
  );
}

