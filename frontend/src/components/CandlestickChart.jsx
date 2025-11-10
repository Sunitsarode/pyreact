import { useState, useEffect } from 'react';
import ReactApexChart from 'react-apexcharts';
import axios from 'axios';
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
console.log('🔍 CandlestickChart.jsx API_URL:', API_URL);  // ← Add this line

export default function CandlestickChart({ symbol, intervals }) {
  const [selectedInterval, setSelectedInterval] = useState('1h');
  const [candles, setCandles] = useState([]);
  const [scoreHistory, setScoreHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (intervals.length > 0 && !intervals.includes(selectedInterval)) {
      setSelectedInterval(intervals[0]);
    }
  }, [intervals]);

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [symbol, selectedInterval]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load candles
      const candlesResponse = await axios.get(`${API_URL}/candles/${symbol}/${selectedInterval}?limit=100`);
      const candleData = candlesResponse.data.map(c => ({
        x: new Date(c.timestamp * 1000).getTime(),
        y: [c.open, c.high, c.low, c.close]
      }));
      setCandles(candleData);

      // Load score history for weighted score and S/R lines
      const scoresResponse = await axios.get(`${API_URL}/scores/${symbol}/history?limit=100`);
      setScoreHistory(scoresResponse.data);
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
    }
  };

  // Prepare weighted score data for lower panel
  const weightedScoreData = scoreHistory.map(s => ({
    x: new Date(s.timestamp * 1000).getTime(),
    y: s.weighted_total_score || 0
  }));

  // Prepare S/R lines for each interval (as step lines that change over time)
  const getSupportResistanceLines = () => {
    const intervalColors = {
      '1d': '#8B5CF6',
      '1h': '#3B82F6',
      '15m': '#10B981',
      '5m': '#F59E0B',
      '1m': '#EF4444'
    };

    const srLines = [];

    intervals.forEach(interval => {
      // Support line
      const supportData = scoreHistory.map(s => ({
        x: new Date(s.timestamp * 1000).getTime(),
        y: s.intervals?.[interval]?.support || null
      })).filter(d => d.y !== null);

      if (supportData.length > 0) {
        srLines.push({
          name: `${interval.toUpperCase()} Support`,
          type: 'line',
          data: supportData,
          color: intervalColors[interval],
          dashArray: 4,
          strokeWidth: 2
        });
      }

      // Resistance line
      const resistanceData = scoreHistory.map(s => ({
        x: new Date(s.timestamp * 1000).getTime(),
        y: s.intervals?.[interval]?.resistance || null
      })).filter(d => d.y !== null);

      if (resistanceData.length > 0) {
        srLines.push({
          name: `${interval.toUpperCase()} Resistance`,
          type: 'line',
          data: resistanceData,
          color: intervalColors[interval],
          dashArray: 0,
          strokeWidth: 2
        });
      }
    });

    return srLines;
  };

  const srLines = getSupportResistanceLines();

  const chartOptions = {
    chart: {
      type: 'candlestick',
      height: 500,
      id: 'candles',
      toolbar: {
        show: true,
        autoSelected: 'pan',
        tools: {
          download: true,
          selection: true,
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
          reset: true
        }
      },
      zoom: {
        enabled: true,
        type: 'xy',  // Enable both X and Y axis zoom
        autoScaleYaxis: true  // Auto-scale Y axis when zooming
      }
    },
    title: {
      text: `${symbol} - ${selectedInterval.toUpperCase()}`,
      align: 'left',
      style: {
        fontSize: '18px',
        fontWeight: 'bold'
      }
    },
   
    xaxis: {
      type: 'datetime',
      timezone: 'Asia/Kolkata',  // IST timezone
      labels: {
        datetimeUTC: false,
        datetimeFormatter: {
          year: 'yyyy',
          month: "MMM 'yy",
          day: 'dd MMM',
          hour: 'HH:mm'
        },
         rotate: -45,
    style: {
      fontSize: '11px'
    },
    hideOverlappingLabels: true  
        
      },
     
    },
/*xaxis: {
  type: 'datetime',
  labels: {
    formatter: function(value, timestamp) {
      const date = new Date(value);
      const hours = date.getHours();
      const minutes = date.getMinutes();
      const day = date.getDate();
      const month = date.toLocaleString('en-US', { month: 'short' });
      
      if (['1m', '5m', '15m', '1h'].includes(selectedInterval)) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
      } else {
        return `${day} ${month}`;
      }
    },
    rotate: -45,
    style: {
      fontSize: '11px'
    },
    hideOverlappingLabels: true  // ✅ Add this to reduce clutter
  }
},*/
    yaxis: {
      tooltip: {
        enabled: true
      },
      labels: {
        formatter: (value) => '$' + value.toFixed(2)
      }
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#10B981',
          downward: '#EF4444'
        }
      }
    },
    legend: {
      show: true,
      position: 'top',
      horizontalAlign: 'left',
      floating: false,
      fontSize: '12px',
      markers: {
        width: 12,
        height: 12
      }
    },
    stroke: {
      width: [1, ...srLines.map(l => l.strokeWidth)]
    },
    tooltip: {
      shared: true,
      custom: function({ seriesIndex, dataPointIndex, w }) {
        const candleData = w.globals.initialSeries[0].data[dataPointIndex];
        if (!candleData) return '';
        
        // Format date in IST
        const date = new Date(candleData.x);
        const dateStr = date.toLocaleString('en-IN', { 
          timeZone: 'Asia/Kolkata',
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
        
        const [o, h, l, c] = candleData.y;
        
        let html = `
          <div style="padding: 10px; background: white; border: 1px solid #ccc; border-radius: 4px;">
            <div style="font-weight: bold; margin-bottom: 5px;">${dateStr} IST</div>
            <div style="color: #666;">
              <div>Open: $${o.toFixed(2)}</div>
              <div>High: $${h.toFixed(2)}</div>
              <div>Low: $${l.toFixed(2)}</div>
              <div>Close: $${c.toFixed(2)}</div>
            </div>
        `;

        // Add S/R levels at this timestamp
        const timestamp = candleData.x;
        const score = scoreHistory.find(s => new Date(s.timestamp * 1000).getTime() === timestamp);
        if (score) {
          html += '<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee; font-size: 11px;">';
          intervals.forEach(interval => {
            const intervalData = score.intervals?.[interval];
            if (intervalData?.support && intervalData?.resistance) {
              html += `
                <div style="color: #666;">
                  <strong>${interval.toUpperCase()}:</strong> 
                  S: $${intervalData.support.toFixed(2)} | 
                  R: $${intervalData.resistance.toFixed(2)}
                </div>
              `;
            }
          });
          html += '</div>';
        }
        
        html += '</div>';
        return html;
      }
    }
  };

  // Score chart options (lower panel)
  const scoreChartOptions = {
    chart: {
      type: 'line',
      height: 250,
      id: 'score',
      brush: {
        enabled: false
      },
      toolbar: {
        show: true,
        tools: {
          download: true,
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
          reset: true
        }
      },
      zoom: {
        enabled: true,
        type: 'xy',  // Enable both X and Y axis zoom
        autoScaleYaxis: true  // Auto-scale Y axis when zooming
      }
    },
    colors: ['#9333EA'],
    stroke: {
      width: 2,
      curve: 'smooth'
    },
    fill: {
      type: 'gradient',
      gradient: {
        opacityFrom: 0.5,
        opacityTo: 0.1
      }
    },
    xaxis: {
      type: 'datetime',
      timezone: 'Asia/Kolkata',  // IST timezone
      labels: {
        datetimeUTC: false,
        datetimeFormatter: {
          year: 'yyyy',
          month: "MMM 'yy",
          day: 'dd MMM',
          hour: 'HH:mm'
        }
      }
    },
    yaxis: {
      min: -100,
      max: 100,
      tickAmount: 4,
      labels: {
        formatter: (value) => value.toFixed(0)
      },
      title: {
        text: 'Weighted Score'
      }
    },
    grid: {
      borderColor: '#e5e7eb'
    },
    tooltip: {
      shared: true,
      x: {
        format: 'dd MMM HH:mm'
      }
    },
    annotations: {
      yaxis: [
        {
          y: 30,
          borderColor: '#10B981',
          strokeDashArray: 4,
          label: {
            borderColor: '#10B981',
            style: {
              color: '#fff',
              background: '#10B981',
              fontSize: '10px'
            },
            text: '+30'
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
              background: '#3B82F6',
              fontSize: '10px'
            },
            text: '0'
          }
        },
        {
          y: -30,
          borderColor: '#EF4444',
          strokeDashArray: 4,
          label: {
            borderColor: '#EF4444',
            style: {
              color: '#fff',
              background: '#EF4444',
              fontSize: '10px'
            },
            text: '-30'
          }
        }
      ]
    }
  };

  // Main series with candles + S/R lines
  const candleSeries = [
    {
      name: 'Price',
      type: 'candlestick',
      data: candles
    },
    ...srLines
  ];

  // Score series
  const scoreSeries = [{
    name: 'Weighted Score',
    data: weightedScoreData
  }];

  return (
    <div className="bg-white rounded-2xl shadow-xl p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">📈 Candlestick Chart</h2>
        
        {/* Interval Selector */}
        <select
          value={selectedInterval}
          onChange={(e) => setSelectedInterval(e.target.value)}
          className="px-3 py-1 border-2 border-gray-300 rounded-lg text-sm font-semibold text-gray-700 focus:outline-none focus:border-blue-500"
        >
          {intervals.map(interval => (
            <option key={interval} value={interval}>{interval.toUpperCase()}</option>
          ))}
        </select>
      </div>

      {/* Tips */}
      <div className="mb-3 text-xs text-gray-500 bg-blue-50 p-2 rounded-lg">
        💡 <strong>Zoom:</strong> Use toolbar zoom icon, then drag to select area • Scroll wheel to zoom • Right-click drag to pan • Reset button to restore
      </div>

      {loading ? (
        <div className="h-96 flex items-center justify-center">
          <div className="text-gray-400">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p>Loading chart...</p>
          </div>
        </div>
      ) : candles.length > 0 ? (
        <div>
          {/* Main Candlestick Chart with S/R Lines */}
          <ReactApexChart
            options={chartOptions}
            series={candleSeries}
            type="candlestick"
            height={500}
          />
          
          {/* Weighted Score Panel (below like MACD) */}
          {weightedScoreData.length > 0 && (
            <div className="mt-4">
              <ReactApexChart
                options={scoreChartOptions}
                series={scoreSeries}
                type="area"
                height={250}
              />
            </div>
          )}
        </div>
      ) : (
        <div className="h-96 flex items-center justify-center text-gray-400">
          <div className="text-center">
            <p className="text-xl mb-2">📊 No data available</p>
            <p className="text-sm">Waiting for candles...</p>
          </div>
        </div>
      )}

      {/* Legend for S/R Lines */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-xs font-semibold text-gray-600 mb-2">Support/Resistance Lines (Time-based):</p>
        <div className="flex flex-wrap gap-3 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-purple-500" style={{ borderStyle: 'dashed' }}></div>
            <span className="text-purple-600">1D Support</span>
            <div className="w-3 h-0.5 bg-purple-500"></div>
            <span className="text-purple-600">1D Resistance</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-blue-500" style={{ borderStyle: 'dashed' }}></div>
            <span className="text-blue-600">1H Support</span>
            <div className="w-3 h-0.5 bg-blue-500"></div>
            <span className="text-blue-600">1H Resistance</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-green-500" style={{ borderStyle: 'dashed' }}></div>
            <span className="text-green-600">15M Support</span>
            <div className="w-3 h-0.5 bg-green-500"></div>
            <span className="text-green-600">15M Resistance</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-orange-500" style={{ borderStyle: 'dashed' }}></div>
            <span className="text-orange-600">5M Support</span>
            <div className="w-3 h-0.5 bg-orange-500"></div>
            <span className="text-orange-600">5M Resistance</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-red-500" style={{ borderStyle: 'dashed' }}></div>
            <span className="text-red-600">1M Support</span>
            <div className="w-3 h-0.5 bg-red-500"></div>
            <span className="text-red-600">1M Resistance</span>
          </div>
        </div>
      </div>
    </div>
  );
}