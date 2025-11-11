import { formatPrice } from '../utils/formatters';

export default function ScoreDisplay({ score, settings, symbol }) {
  const threshold = settings.breakout_rules?.total_score_threshold || 30;
  const totalScore = score.weighted_total_score || 0;
  
  const getScoreColor = (score) => {
    if (score > threshold) return 'text-green-500';
    if (score < -threshold) return 'text-red-500';
    return 'text-blue-500';
  };
  
  const getScoreStatus = (score) => {
    if (score > threshold) return '🚀 STRONG BULLISH';
    if (score < -threshold) return '⚠️ STRONG BEARISH';
    return '↔️ NEUTRAL';
  };
  
  const getProgressWidth = (score) => {
    return ((score + 100) / 200) * 100;
  };
  
  const getProgressColor = (score) => {
    if (score > threshold) return 'bg-green-500';
    if (score < -threshold) return 'bg-red-500';
    return 'bg-blue-500';
  };

  const currentPrice = score.current_price || 0;
  const formattedPrice = formatPrice(currentPrice, symbol);

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8">
      <div className="text-center">
        <p className="text-gray-600 text-lg mb-3">Multi-Timeframe Weighted Score</p>
        <div className={`text-7xl font-bold mb-4 ${getScoreColor(totalScore)}`}>
          {totalScore.toFixed(2)}
        </div>
        <p className="text-2xl font-bold mb-6">{getScoreStatus(totalScore)}</p>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-8 mb-4">
          <div 
            className={`h-8 rounded-full transition-all duration-500 flex items-center justify-center text-white font-bold ${getProgressColor(totalScore)}`}
            style={{ width: `${getProgressWidth(totalScore)}%` }}
          >
            {totalScore.toFixed(1)}
          </div>
        </div>
        
        {/* Price & Thresholds */}
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span>-100 (Bearish)</span>
          <div className="text-center">
            <p className="text-lg font-bold text-gray-900">
              {formattedPrice}
            </p>
            <p className="text-xs">Current Price</p>
          </div>
          <span>+100 (Bullish)</span>
        </div>

        {/* Timestamp */}
        {score.timestamp > 0 && (
          <p className="mt-4 text-xs text-gray-500">
            Last Updated: {new Date(score.timestamp * 1000).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );
}
