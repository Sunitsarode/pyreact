export default function IntervalBreakdown({ intervals, weights }) {
  const getScoreColor = (score) => {
    if (score > 30) return 'text-green-500';
    if (score < -30) return 'text-red-500';
    return 'text-blue-500';
  };

  const intervalOrder = ['1h', '5m', '1m']; // UPDATED: Only these 3
  const intervalNames = {
    '1h': '1 Hour',
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

            // Use avg_total_score instead of total_score
            const avgScore = data.avg_total_score || 0;

            return (
              <div key={interval} className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    <span className="font-bold text-lg">{intervalNames[interval]}</span>
                    <span className="text-sm text-gray-500 ml-2">
                      Weight: {((weights[interval] || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <span className={`text-2xl font-bold ${getScoreColor(avgScore)}`}>
                    {avgScore.toFixed(1)}
                  </span>
                </div>
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-4 mb-3">
                  <div 
                    className={`h-4 rounded-full transition-all duration-300 ${
                      avgScore > 30 ? 'bg-green-500' : 
                      avgScore < -30 ? 'bg-red-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${((avgScore + 100) / 200) * 100}%` }}
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
                
                {/* Individual Indicator Scores - ONLY 4 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                  <div className="text-center">
                    <p className="text-gray-500">RSI</p>
                    <p className={`font-bold ${getScoreColor(data.rsi_score)}`}>
                      {data.rsi_score?.toFixed(0) || 0}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-500">MACD</p>
                    <p className={`font-bold ${getScoreColor(data.macd_score)}`}>
                      {data.macd_score?.toFixed(0) || 0}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-500">ADX</p>
                    <p className={`font-bold ${getScoreColor(data.adx_score)}`}>
                      {data.adx_score?.toFixed(0) || 0}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-500">Supertrend</p>
                    <p className={`font-bold ${getScoreColor(data.supertrend_score)}`}>
                      {data.supertrend_score?.toFixed(0) || 0}
                    </p>
                  </div>
                </div>
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

