export default function Header({ symbols, selectedSymbol, onSymbolChange, connected, settings }) {
  return (
    <div className="bg-white rounded-2xl shadow-xl p-6">
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
          📊 Live Analyser
        </h1>
        
        <div className="flex items-center gap-4 flex-wrap">
          {/* Symbol Selector */}
          <select 
            value={selectedSymbol}
            onChange={(e) => onSymbolChange(e.target.value)}
            className="px-4 py-2 border-2 border-purple-300 rounded-lg font-semibold text-gray-700 focus:outline-none focus:border-purple-500 cursor-pointer"
          >
            {symbols.map(symbol => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>
          
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
            <span className="text-gray-600 font-semibold">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>
      
      {/* Update Info */}
      <div className="mt-4 text-sm text-gray-600 flex gap-6 flex-wrap">
        <span>⏱️ Update: Every {settings.updateIntervalMinutes || 5} min</span>
        <span>📈 Intervals: {settings.intervals?.join(', ') || 'N/A'}</span>
        <span>🔔 Alerts: {settings.notifications?.enabled ? 'Enabled' : 'Disabled'}</span>
      </div>
    </div>
  );
}
