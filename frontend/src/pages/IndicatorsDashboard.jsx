import React, { useState, useEffect } from 'react';
import axios from 'axios';
import IndicatorScoreChart from '../components/IndicatorScoreChart';

const API_BASE_URL = 'http://localhost:5000/api';

const IndicatorsDashboard = () => {
  const [symbols, setSymbols] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [indicatorData, setIndicatorData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/symbols`);
        setSymbols(response.data);
        if (response.data.length > 0) {
          setSelectedSymbol(response.data[0]);
        }
      } catch (err) {
        setError('Failed to fetch symbols.');
        console.error(err);
      }
    };
    fetchSymbols();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      const fetchIndicatorData = async () => {
        setLoading(true);
        setError('');
        try {
          const response = await axios.get(`${API_BASE_URL}/scores/${selectedSymbol}/all_intervals`);
          setIndicatorData(response.data);
        } catch (err) {
          setError(`Failed to fetch indicator data for ${selectedSymbol}.`);
          console.error(err);
        } finally {
          setLoading(false);
        }
      };
      fetchIndicatorData();
    }
  }, [selectedSymbol]);

  const timeframes = ['1min', '5min', '15min', '1hr', '1d'];

  return (
    <div className="p-4 bg-gray-900 text-white min-h-screen">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-bold">Indicators Dashboard</h1>
        <div className="flex items-center">
          <label htmlFor="symbol-select" className="mr-2">Symbol:</label>
          <select
            id="symbol-select"
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-md p-2"
          >
            {symbols.map((symbol) => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && <p>Loading data...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {indicatorData && !loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {timeframes.map((tf) => {
            const sanitizedTf = tf.replace('m', 'min').replace('h', 'hr').replace('d', 'day');
            const scoreData = indicatorData[tf] || indicatorData[sanitizedTf];

            return scoreData ? (
              <IndicatorScoreChart
                key={tf}
                scores={scoreData}
                title={`Scores for ${tf}`}
              />
            ) : (
              <div key={tf} className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-bold mb-2">{`Scores for ${tf}`}</h3>
                <p>No data available for this timeframe.</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default IndicatorsDashboard;
