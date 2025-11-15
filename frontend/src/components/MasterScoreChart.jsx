import React, { useState, useEffect } from 'react';
import ReactApexChart from 'react-apexcharts';

export default function MasterScoreChart({ scoreHistory }) {
  const [selectedInterval, setSelectedInterval] = useState('5m'); // Default to 5m

  const availableIntervals = ['1m', '5m', '1h']; // User requested intervals

  // Prepare data for chart
  const timestamps = scoreHistory.map(s => s.timestamp * 1000);

  const getIntervalMasterScores = (interval) => {
    return scoreHistory.map(s => s.intervals?.[interval]?.master_score || null);
  };

  const getIntervalSMAs = (interval, smaType) => {
    // interval_smas is a dictionary where keys are intervals and values are objects with sma9 and sma21
    // We need to map this to the scoreHistory timestamps
    const smas = [];
    for (let i = 0; i < scoreHistory.length; i++) {
      const scoreEntry = scoreHistory[i];
      if (scoreEntry.interval_smas && scoreEntry.interval_smas[interval]) {
        smas.push(scoreEntry.interval_smas[interval][smaType]);
      } else {
        smas.push(null);
      }
    }
    return smas;
  };

  const masterScores = getIntervalMasterScores(selectedInterval);
  const masterScoreSMA9 = getIntervalSMAs(selectedInterval, 'master_score_sma9');
  const masterScoreSMA21 = getIntervalSMAs(selectedInterval, 'master_score_sma21');

  const series = [
    {
      name: `Master Score (${selectedInterval.toUpperCase()})`,
      data: masterScores.map((val, idx) => ({ x: timestamps[idx], y: val })),
      color: '#FF0000'
    },
    {
      name: `SMA 9 (${selectedInterval.toUpperCase()})`,
      data: masterScoreSMA9.map((val, idx) => ({ x: timestamps[idx], y: val })),
      color: '#0000FF'
    },
    {
      name: `SMA 21 (${selectedInterval.toUpperCase()})`,
      data: masterScoreSMA21.map((val, idx) => ({ x: timestamps[idx], y: val })),
      color: '#00FF00'
    }
  ].filter(s => s.data.some(d => d.y !== null)); // Filter out series with no data

  const chartOptions = {
    chart: {
      type: 'line',
      height: 350,
      toolbar: {
        show: true
      },
      zoom: {
        enabled: true
      },
      animations: {
        enabled: true,
        dynamicAnimation: {
          speed: 500
        }
      }
    },
    title: {
      text: `Master Score Trend - ${selectedInterval.toUpperCase()}`,
      align: 'left',
      style: {
        fontSize: '18px',
        fontWeight: 'bold'
      }
    },
    stroke: {
      width: [2, 1, 1], // Master Score thicker, SMAs thinner
      curve: 'smooth'
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeFormatter: {
          hour: 'HH:mm',
          day: 'dd MMM',
          month: "MMM 'yy"
        }
      }
    },
    yaxis: {
      min: 0,
      max: 100,
      tickAmount: 10,
      labels: {
        formatter: (value) => value.toFixed(0)
      }
    },
    tooltip: {
      shared: true,
      intersect: false,
      x: {
        format: 'dd MMM HH:mm'
      },
      y: {
        formatter: (value) => value?.toFixed(2) || '0'
      }
    },
    legend: {
      show: true,
      position: 'top',
      horizontalAlign: 'center'
    },
    grid: {
      borderColor: '#e5e7eb',
      strokeDashArray: 4
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl p-6">
      <div className="flex justify-between items-center mb-4 flex-wrap gap-4">
        <h2 className="text-2xl font-bold text-gray-800">📈 Master Score Trend</h2>
        
        {/* Interval Selector */}
        <select
          value={selectedInterval}
          onChange={(e) => setSelectedInterval(e.target.value)}
          className="px-3 py-1 border-2 border-gray-300 rounded-lg text-sm font-semibold text-gray-700 focus:outline-none focus:border-blue-500"
        >
          {availableIntervals.map(interval => (
            <option key={interval} value={interval}>{interval.toUpperCase()}</option>
          ))}
        </select>
      </div>

      {scoreHistory.length > 0 ? (
        <ReactApexChart
          options={chartOptions}
          series={series}
          type="line"
          height={350}
        />
      ) : (
        <div className="h-96 flex items-center justify-center text-gray-400">
          <div className="text-center">
            <p className="text-xl mb-2">⏳ Waiting for data...</p>
            <p className="text-sm">Master Score data not yet available.</p>
          </div>
        </div>
      )}
    </div>
  );
}