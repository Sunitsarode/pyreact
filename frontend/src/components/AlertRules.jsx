export default function AlertRules({ settings }) {
  const breakoutRules = settings.breakout_rules || {};
  
  return (
    <div className="bg-white rounded-2xl shadow-xl p-6">
      <h3 className="text-xl font-bold mb-4 text-gray-800">🔔 Alert Rules</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4">
          <p className="text-green-700 font-bold mb-2">Strong Buy Alert</p>
          <p className="text-3xl font-bold text-green-600">
            &gt; {breakoutRules.total_score_threshold || 30}
          </p>
          <p className="text-xs text-green-600 mt-2">
            Triggered when weighted score exceeds threshold
          </p>
        </div>
        
        <div className="bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4">
          <p className="text-yellow-700 font-bold mb-2">RSI Alerts</p>
          <div className="space-y-1">
            <p className="text-sm text-yellow-600">
              <span className="font-bold">Overbought:</span> &gt; {breakoutRules.rsi_overbought || 70}
            </p>
            <p className="text-sm text-yellow-600">
              <span className="font-bold">Oversold:</span> &lt; {breakoutRules.rsi_oversold || 30}
            </p>
          </div>
          <p className="text-xs text-yellow-600 mt-2">
            Based on RSI indicator value
          </p>
        </div>
        
        <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
          <p className="text-red-700 font-bold mb-2">Strong Sell Alert</p>
          <p className="text-3xl font-bold text-red-600">
            &lt; -{breakoutRules.total_score_threshold || 30}
          </p>
          <p className="text-xs text-red-600 mt-2">
            Triggered when weighted score falls below threshold
          </p>
        </div>
      </div>

      {/* Notification Status */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-700">
              Notification Method: {settings.notifications?.method || 'None'}
            </p>
            <p className="text-xs text-gray-500">
              Status: {settings.notifications?.enabled ? '✅ Enabled' : '❌ Disabled'}
            </p>
          </div>
          <div className="text-xs text-gray-500">
            Cooldown: 5 minutes between same alert types
          </div>
        </div>
      </div>
    </div>
  );
}
