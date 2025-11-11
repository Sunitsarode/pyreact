import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Chart from 'react-apexcharts';
import axios from 'axios';
import SimpleHeader from '../components/SimpleHeader';

const AllIndicatorsScorePage = () => {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [timeframe, setTimeframe] = useState('15m'); // Default timeframe
  const [series, setSeries] = useState([]);
  const [options, setOptions] = useState({});
  const [loading, setLoading] = useState(true);

  const timeframes = ['1m', '5m', '15m', '1h', '1d'];

  useEffect(() => {
    console.log('Symbol from URL:', symbol); // DEBUG LOG
    setLoading(true);
    axios.get(`http://localhost:5001/api/scores/${symbol}/${timeframe}/history?limit=100`)
      .then(response => {
        const data = response.data;
        
        const categories = data.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());
        const rsiScores = data.map(d => d.rsi_score);
        const macdScores = data.map(d => d.macd_score);
        const bbScores = data.map(d => d.bb_score);
        const adxScores = data.map(d => d.adx_score);
        const supertrendScores = data.map(d => d.supertrend_score);
        const smaScores = data.map(d => d.sma_score);

        setSeries([
          { name: 'RSI Score', data: rsiScores },
          { name: 'MACD Score', data: macdScores },
          { name: 'BB Score', data: bbScores },
          { name: 'ADX Score', data: adxScores },
          { name: 'Supertrend Score', data: supertrendScores },
          { name: 'SMA Score', data: smaScores },
        ]);

        setOptions({
          chart: {
            height: 350,
            type: 'line',
            zoom: {
              enabled: true
            },
            toolbar: {
              show: true
            },
            foreColor: '#ccc'
          },
          dataLabels: {
            enabled: false
          },
          stroke: {
            curve: 'smooth',
            width: 2
          },
          title: {
            text: `Indicator Scores for ${symbol} - ${timeframe}`,
            align: 'left',
            style: {
              fontSize: '16px',
              color: '#fff'
            }
          },
          grid: {
            borderColor: '#555',
            row: {
              colors: ['transparent', 'rgba(255, 255, 255, 0.05)'],
              opacity: 0.5
            },
          },
          xaxis: {
            categories: categories,
            labels: {
              style: {
                colors: '#ccc'
              }
            }
          },
          yaxis: {
            min: -100,
            max: 100,
            labels: {
              style: {
                colors: '#ccc'
              }
            }
          },
          tooltip: {
            theme: 'dark'
          },
          legend: {
            labels: {
              colors: '#ccc'
            }
          }
        });
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching indicator scores:', error);
        setLoading(false);
      });
  }, [symbol, timeframe]);

  const handleRepopulate = () => {
    if (window.confirm('There is no database or blank database. Do you want to add previous data to db?')) {
      axios.post('http://localhost:5001/api/repopulate')
        .then(response => {
          alert('Data repopulation started. It may take a few minutes.');
        })
        .catch(error => {
          console.error('Error starting data repopulation:', error);
          alert('Failed to start data repopulation.');
        });
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <SimpleHeader />
      <div className="container mx-auto p-4">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">All Indicators Scores for {symbol}</h1>
          <button onClick={handleRepopulate} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Repopulate Data
          </button>
        </div>
        <div className="flex space-x-2 mb-4">
          <button onClick={() => navigate(`/`)} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded">
            Dashboard
          </button>
          <button onClick={() => navigate(`/${symbol}`)} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded">
            Back to {symbol}
          </button>
        </div>
        <div className="flex space-x-2 mb-4">
          {timeframes.map(tf => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-4 py-2 rounded ${timeframe === tf ? 'bg-blue-500' : 'bg-gray-700'}`}
            >
              {tf}
            </button>
          ))}
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          {loading ? (
            <p>Loading...</p>
          ) : (
            <Chart options={options} series={series} type="line" height={350} />
          )}
        </div>
      </div>
    </div>
  );
};

export default AllIndicatorsScorePage;
