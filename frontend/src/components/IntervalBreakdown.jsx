export default function IntervalBreakdown({ intervals, weights }) {
  const getScoreColor = (score) => {
    if (score > 30) return 'text-green-500';
    if (score < -30) return 'text-red-500';
    return 'text-blue-500';
  };
  
  const getBarColor = (score) => {
    if (score > 30) return 'bg-green-500';
    if (score < -30) return 'bg-red-500';
    return 'bg-blue-500';
  };
  
  const getBarWidth = (score) => {
    return ((score + 100) / 200) * 100;
  };

  const intervalOrder = ['1d', '1h', '15m', '5m', '1m'];
  const intervalNames = {
    '1d': '1 Day',
    '1h': '1 Hour',
    '15m': '15 Minutes',
    '5m': '5 Minutes',
    '1m': '1 Minute'
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl p-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">📊 Interval Breakdown</h2>
      
      {Object.keys(intervals).length > 0 ? (
        <div className="space-y-4">
          {intervalOrder.map(interval => {
            const data = intervals[interval];
            if (!data) return null;

            return (
              <div key={interval} className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    <span className="font-bold text-lg">{intervalNames[interval]}</span>
                    <span className="text-sm text-gray-500 ml-2">
                      Weight: {((weights[interval] || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <span className={`text-2xl font-bold ${getScoreColor(data.score)}`}>
                    {data.score?.toFixed(1) || 0}
                  </span>
                </div>
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-4 mb-3">
                  <div 
                    className={`h-4 rounded-full transition-all duration-300 ${getBarColor(data.score)}`}
                    style={{ width: `${getBarWidth(data.score)}%` }}
                  ></div>
                </div>

                {/* Support & Resistance */}
                <div className="flex justify-between text-xs text-gray-600 mb-2">
                  <div>
                    <span className="text-green-600 font-semibold">Support: </span>
                    ${data.support?.toFixed(2) || 0}
                  </div>
                  <div>
                    <span className="text-red-600 font-semibold">Resistance: </span>
                    ${data.resistance?.toFixed(2) || 0}
                  </div>
                </div>
                
                {/* Individual Indicator Scores */}
                {data.rsi_score !== undefined && (
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2 text-xs">
                    <div className="text-center">
                      <p className="text-gray-500">RSI</p>
                      <p className={`font-bold ${getScoreColor(data.rsi_score)}`}>
                        {data.rsi_score?.toFixed(0)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-500">MACD</p>
                      <p className={`font-bold ${getScoreColor(data.macd_score)}`}>
                        {data.macd_score?.toFixed(0)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-500">ADX</p>
                      <p className={`font-bold ${getScoreColor(data.adx_score)}`}>
                        {data.adx_score?.toFixed(0)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-500">BB</p>
                      <p className={`font-bold ${getScoreColor(data.bb_score)}`}>
                        {data.bb_score?.toFixed(0)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-500">SMA</p>
                      <p className={`font-bold ${getScoreColor(data.sma_score)}`}>
                        {data.sma_score?.toFixed(0)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-500">ST</p>
                      <p className={`font-bold ${getScoreColor(data.supertrend_score)}`}>
                        {data.supertrend_score?.toFixed(0)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center text-gray-400 py-8">
          <p className="text-xl">⏳ Waiting for interval data...</p>
        </div>
      )}
    </div>
  );
}
