import { formatPrice } from '../utils/formatters';

const IndicatorPill = ({ name, value }) => {
  const getPillColor = (val) => {
    if (val > 65) return 'bg-green-500';
    if (val > 55) return 'bg-green-400';
    if (val < 35) return 'bg-red-500';
    if (val < 45) return 'bg-red-400';
    return 'bg-gray-400';
  };

  return (
    <div className={`text-white px-3 py-1 rounded-full text-sm font-semibold ${getPillColor(value)}`}>
      {name}: {value.toFixed(1)}
    </div>
  );
};

export default function ScoreDisplay({ score, settings, symbol }) {
  const masterScore = score.master_score || 0;
  const classification = score.classification || 'NEUTRAL';
  const weightedIndicators = score.weighted_indicators || {};

  const getScoreColor = (classification) => {
    if (classification?.includes('BULLISH')) return 'text-green-500';
    if (classification?.includes('BEARISH')) return 'text-red-500';
    return 'text-blue-500';
  };
  
  const getScoreStatus = (classification) => {
    if (classification === 'STRONG_BULLISH') return '🚀 STRONG BULLISH';
    if (classification === 'BULLISH') return '📈 BULLISH';
    if (classification === 'STRONG_BEARISH') return '⚠️ STRONG BEARISH';
    if (classification === 'BEARISH') return '📉 BEARISH';
    return '↔️ NEUTRAL';
  };
  
  const getProgressWidth = (score) => {
    return ((score) / 100) * 100;
  };
  
  const getProgressColor = (classification) => {
    if (classification?.includes('BULLISH')) return 'bg-green-500';
    if (classification?.includes('BEARISH')) return 'bg-red-500';
    return 'bg-blue-500';
  };

  const currentPrice = score.current_price || 0;
  const formattedPrice = formatPrice(currentPrice, symbol);

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8">
      <div className="text-center">
        <p className="text-gray-600 text-lg mb-3">Master Score</p>
        <div className={`text-7xl font-bold mb-4 ${getScoreColor(classification)}`}>
          {masterScore.toFixed(2)}
        </div>
        <p className="text-2xl font-bold mb-6">{getScoreStatus(classification)}</p>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-8 mb-4">
          <div 
            className={`h-8 rounded-full transition-all duration-500 flex items-center justify-center text-white font-bold ${getProgressColor(classification)}`}
            style={{ width: `${getProgressWidth(masterScore)}%` }}
          >
            {masterScore.toFixed(1)}
          </div>
        </div>
        
        {/* Price & Thresholds */}
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span>0 (Bearish)</span>
          <div className="text-center">
            <p className="text-lg font-bold text-gray-900">
              {formattedPrice}
            </p>
            <p className="text-xs">Current Price</p>
          </div>
          <span>100 (Bullish)</span>
        </div>

        {/* Weighted Indicators */}
        <div className="mt-6">
          <p className="text-gray-600 text-md mb-3">Weighted Indicators</p>
          <div className="flex justify-center gap-2 flex-wrap">
            <IndicatorPill name="RSI" value={weightedIndicators.rsi || 0} />
            <IndicatorPill name="MACD" value={weightedIndicators.macd || 0} />
            <IndicatorPill name="ADX" value={weightedIndicators.adx || 0} />
            <IndicatorPill name="Supertrend" value={weightedIndicators.supertrend || 0} />
          </div>
        </div>

        {/* Timestamp */}
        {score.timestamp > 0 && (
          <p className="mt-6 text-xs text-gray-500">
            Last Updated: {new Date(score.timestamp * 1000).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );
}
