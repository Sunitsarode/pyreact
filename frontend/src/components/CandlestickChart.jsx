import { useState, useEffect, useRef } from 'react';
import ReactApexChart from 'react-apexcharts';
import axios from 'axios';
import { API_URL } from '../utils/api';

export default function CandlestickChart({ symbol, intervals }) {
  const [selectedInterval, setSelectedInterval] = useState('1h');
  const [candles, setCandles] = useState([]);
  const [scoreHistory, setScoreHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const chartRef = useRef(null);
  const [zoomRange, setZoomRange] = useState(null);
  
  // Toggle state for indicator visibility
  const [visibleIndicators, setVisibleIndicators] = useState({
    weighted: true,
    rsi: false,
    macd: false,
    adx: false,
    bb: false,
    sma: false,
    supertrend: false
  });

  useEffect(() => {
    if (intervals.length > 0 && !intervals.includes(selectedInterval)) {
      setSelectedInterval(intervals[0]);
    }
  }, [intervals]);

  useEffect(() => {
    setZoomRange(null);
    loadData();
    
    const interval = setInterval(loadData, 300000);
    return () => clearInterval(interval);
  }, [symbol, selectedInterval]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      const candlesResponse = await axios.get(`${API_URL}/candles/${symbol}/${selectedInterval}?limit=100`);
      const candleData = candlesResponse.data.map(c => ({
        x: new Date(c.timestamp * 1000).getTime(),
        y: [c.open, c.high, c.low, c.close]
      }));
      setCandles(candleData);

      const scoresResponse = await axios.get(`${API_URL}/scores/${symbol}/history?limit=100`);
      setScoreHistory(scoresResponse.data);
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
    }
  };

  const toggleIndicator = (indicator) => {
    setVisibleIndicators(prev => ({
      ...prev,
      [indicator]: !prev[indicator]
    }));
  };

  // Prepare all indicator score series
  const getIndicatorSeries = () => {
    const timestamps = scoreHistory.map(s => new Date(s.timestamp * 1000).getTime());
    
    const indicatorConfig = {
      weighted: {
        name: 'Weighted Score',
        color: '#FF0000',
        data: scoreHistory.map(s => s.weighted_total_score || 0)
      },
      rsi: {
        name: 'RSI Score',
        color: '#9333EA',
        data: scoreHistory.map(s => s.intervals?.[selectedInterval]?.rsi_score || 0)
      },
      macd: {
        name: 'MACD Score',
        color: '#3B82F6',
        data: scoreHistory.map(s => s.intervals?.[selectedInterval]?.macd_score || 0)
      },
      adx: {
        name: 'ADX Score',
        color: '#F97316',
        data: scoreHistory.map(s => s.intervals?.[selectedInterval]?.adx_score || 0)
      },
      bb: {
        name: 'BB Score',
        color: '#10B981',
        data: scoreHistory.map(s => s.intervals?.[selectedInterval]?.bb_score || 0)
      },
      sma: {
        name: 'SMA Score',
        color: '#06B6D4',
        data: scoreHistory.map(s => s.intervals?.[selectedInterval]?.sma_score || 0)
      },
      supertrend: {
        name: 'Supertrend Score',
        color: '#EF4444',
        data: scoreHistory.map(s => s.intervals?.[selectedInterval]?.supertrend_score || 0)
      }
    };

    return Object.entries(indicatorConfig)
      .filter(([key]) => visibleIndicators[key])
      .map(([key, config]) => ({
        name: config.name,
        data: config.data.map((val, idx) => ({
          x: timestamps[idx],
          y: val
        })),
        color: config.color
      }));
  };

  // S/R lines
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
  const indicatorSeries = getIndicatorSeries();

  // Main candlestick chart options
  const chartOptions = {
    chart: {
      type: 'candlestick',
      height: 500,
      id: 'candles',
      group: 'synced-charts',
      toolbar: {
        show: true,
        autoSelected: 'pan'
      },
      zoom: {
        enabled: true,
        type: 'xy',
        autoScaleYaxis: true
      },
      animations: {
        enabled: false
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
      timezone: 'Asia/Kolkata',
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
      }
    },
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
      horizontalAlign: 'left'
    },
    stroke: {
      width: [1, ...srLines.map(l => l.strokeWidth)]
    },
    tooltip: {
      shared: true,
      custom: function({ seriesIndex, dataPointIndex, w }) {
        const candleData = w.globals.initialSeries[0].data[dataPointIndex];
        if (!candleData) return '';
        
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

  // Score indicator chart options (lower panel)
  const scoreChartOptions = {
    chart: {
      type: 'line',
      height: 300,
      id: 'scores',
      group: 'synced-charts',
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
        type: 'xy',
        autoScaleYaxis: true
      }
    },
    colors: indicatorSeries.map(s => s.color),
    stroke: {
      width: 2,
      curve: 'smooth'
    },
    xaxis: {
      type: 'datetime',
      timezone: 'Asia/Kolkata',
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
        text: 'Indicator Scores'
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
    legend: {
      show: true,
      position: 'top',
      horizontalAlign: 'center'
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

  const candleSeries = [
    {
      name: 'Price',
      type: 'candlestick',
      data: candles
    },
    ...srLines
  ];

  return (
    <div className="bg-white rounded-2xl shadow-xl p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">📈 Trading View</h2>
        
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

      <div className="mb-3 text-xs text-gray-500 bg-blue-50 p-2 rounded-lg">
        💡 <strong>Synced Charts:</strong> Both charts zoom/pan together • Use toolbar controls
      </div>

      {loading ? (
        <div className="h-96 flex items-center justify-center">
          <div className="text-gray-400">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p>Loading charts...</p>
          </div>
        </div>
      ) : candles.length > 0 ? (
        <div>
          {/* Candlestick Chart */}
          <ReactApexChart
            options={chartOptions}
            series={candleSeries}
            type="candlestick"
            height={500}
          />
          
          {/* Indicator Toggle Buttons */}
          <div className="flex flex-wrap gap-2 my-4">
            {Object.entries({
              weighted: { name: 'Weighted Score', color: '#FF0000' },
              rsi: { name: 'RSI Score', color: '#9333EA' },
              macd: { name: 'MACD Score', color: '#3B82F6' },
              adx: { name: 'ADX Score', color: '#F97316' },
              bb: { name: 'BB Score', color: '#10B981' },
              sma: { name: 'SMA Score', color: '#06B6D4' },
              supertrend: { name: 'Supertrend Score', color: '#EF4444' }
            }).map(([key, config]) => (
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

          {/* Score Indicator Chart (Lower Panel) */}
          {indicatorSeries.length > 0 && (
            <div className="mt-4">
              <ReactApexChart
                options={scoreChartOptions}
                series={indicatorSeries}
                type="line"
                height={300}
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

      {/* S/R Legend */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-xs font-semibold text-gray-600 mb-2">Support/Resistance Lines:</p>
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