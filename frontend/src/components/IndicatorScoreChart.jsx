import React from 'react';
import Chart from 'react-apexcharts';

const IndicatorScoreChart = ({ scores, title }) => {
  const series = [
    { name: 'RSI', data: [scores.rsi_score] },
    { name: 'MACD', data: [scores.macd_score] },
    { name: 'ADX', data: [scores.adx_score] },
    { name: 'BB', data: [scores.bb_score] },
    { name: 'SMA', data: [scores.sma_score] },
    { name: 'Supertrend', data: [scores.supertrend_score] },
  ];

  const options = {
    chart: {
      type: 'bar',
      height: 350,
      toolbar: {
        show: false,
      },
    },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: '55%',
        endingShape: 'rounded',
      },
    },
    dataLabels: {
      enabled: true,
    },
    stroke: {
      show: true,
      width: 2,
      colors: ['transparent'],
    },
    xaxis: {
      categories: [title],
      labels: {
        style: {
          colors: '#9ca3af',
        },
      },
    },
    yaxis: {
      min: -100,
      max: 100,
      labels: {
        style: {
          colors: '#9ca3af',
        },
      },
    },
    fill: {
      opacity: 1,
    },
    tooltip: {
      theme: 'dark',
      y: {
        formatter: function (val) {
          return val;
        },
      },
    },
    theme: {
      mode: 'dark',
    },
    legend: {
      labels: {
        colors: '#9ca3af',
      },
    },
  };

  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h3 className="text-lg font-bold mb-2">{title}</h3>
      <Chart options={options} series={series} type="bar" height={350} />
    </div>
  );
};

export default IndicatorScoreChart;
