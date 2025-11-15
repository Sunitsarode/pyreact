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
  const [selectedInterval, setSelectedInterval] = useState('5m');
  const [visibleIndicators, setVisibleIndicators] = useState({
    avgWeightedScore: true,
    avgScore: true
  });

  const intervals = ['1d', '1h', '15m', '5m', '1m'];
  const intervalNames = {
    '1d': '1 Day',
    '1h': '1 Hour',
    '15m': '15 Min',
    '5m': '5 Min',
    '1m': '1 Min'
  };

  const toggleIndicator = (indicator) => {
    setVisibleIndicators(prev => ({
      ...prev,
      [indicator]: !prev[indicator]
    }));
  };

  // Prepare data for chart
  const timestamps = scoreHistory.map(s => s.timestamp * 1000);
  
  const getAvgWeightedScoreData = () => {
    return scoreHistory.map(s => s.master_score || 0);
  };

  const getAvgScoreData = () => {
    return scoreHistory.map(s => {
      const intervalData = s.intervals?.[selectedInterval];
      return intervalData?.total_score || 0;
    });
  };

  const indicatorConfig = {
    avgWeightedScore: { name: 'Master Score', color: '#FF0000', data: getAvgWeightedScoreData() },
    avgScore: { name: 'Avg Score', color: '#0000FF', data: getAvgScoreData() }
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
      toolbar: {
        show: true
      },
      zoom: {
        enabled: true
      },
      animations: {
        enabled: true,
        dynamicAnimation: {
          speed: 500
        }
      }
    },
    title: {
      text: `Indicator Scores - ${intervalNames[selectedInterval]}`,
      align: 'left',
      style: {
        fontSize: '18px',
        fontWeight: 'bold'
      }
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
          day: 'dd MMM',
          month: "MMM 'yy"
        }
      }
    },
    yaxis: {
      min: -100,
      max: 100,
      tickAmount: 10,
      labels: {
        formatter: (value) => value.toFixed(0)
      }
    },
    tooltip: {
      shared: true,
      intersect: false,
      x: {
        format: 'dd MMM HH:mm'
      },
      y: {
        formatter: (value) => value?.toFixed(2) || '0'
      }
    },
    legend: {
      show: true,
      position: 'top',
      horizontalAlign: 'center'
    },
    grid: {
      borderColor: '#e5e7eb',
      strokeDashArray: 4
    },
    annotations: {
      yaxis: [
        {
          y: threshold,
          borderColor: '#10B981',
          strokeDashArray: 4,
          label: {
            borderColor: '#10B981',
            style: {
              color: '#fff',
              background: '#10B981'
            },
            text: `+${threshold}`
          }
        },
        {
          y: 0,
          borderColor: '#3B82F6',
          strokeDashArray: 2,
          label: {
            borderColor: '#3B82F6',
            style: {
              color: '#fff',
              background: '#3B82F6'
            },
            text: '0'
          }
        },
        {
          y: -threshold,
          borderColor: '#EF4444',
          strokeDashArray: 4,
          label: {
            borderColor: '#EF4444',
            style: {
              color: '#fff',
              background: '#EF4444'
            },
            text: `-${threshold}`
          }
        }
      ]
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl p-6">
      <div className="flex justify-between items-center mb-4 flex-wrap gap-4">
        <h2 className="text-2xl font-bold text-gray-800">📉 Indicators Score</h2>
        
        {/* Interval Selector */}
        <select
          value={selectedInterval}
          onChange={(e) => setSelectedInterval(e.target.value)}
          className="px-3 py-1 border-2 border-gray-300 rounded-lg text-sm font-semibold text-gray-700 focus:outline-none focus:border-blue-500"
        >
          {intervals.map(interval => (
            <option key={interval} value={interval}>{intervalNames[interval]}</option>
          ))}
        </select>
      </div>

      {/* Indicator Toggle Buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        {Object.entries(indicatorConfig).map(([key, config]) => (
          <button
            key={key}
            onClick={() => toggleIndicator(key)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              visibleIndicators[key]
                ? 'text-white'
                : 'bg-gray-200 text-gray-600'
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
          <div className="text-center">
            <p className="text-xl mb-2">⏳ Waiting for data...</p>
            <p className="text-sm">Updates every 5 minutes</p>
          </div>
        </div>
      )}
    </div>
  );
}
