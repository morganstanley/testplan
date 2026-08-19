import React from "react";
import PropTypes from "prop-types";
import {
  Chart as ChartJS,
  BarElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  TimeSeriesScale,
} from "chart.js";
import { format as dateFormat, addMinutes as dateAddMinutes } from "date-fns";
import { Bar } from "react-chartjs-2";
import "chartjs-adapter-date-fns";
import { timeToTimestamp } from "../../Common/utils";
import { GREEN, LIGHT_GREEN } from "../../Common/defaults";

ChartJS.register(
  BarElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  TimeSeriesScale
);

export default function TimelineAssertion(props) {
  const timezoneOffset = new Date().getTimezoneOffset();
  const rows = Object.values(props.assertion.timeline_data).flat();

  const labels = [];
  const datasets = [
    {
      data: [],
      backgroundColor: LIGHT_GREEN,
      borderColor: GREEN,
      borderWidth: 2,
      borderRadius: Number.MAX_VALUE,
      borderSkipped: false,
      barThickness: 6,
      minBarLength: 2,
    },
  ];

  let minTime;
  let maxTime;

  rows.forEach((row) => {
    labels.push(row.name);

    const start = timeToTimestamp(row.start);
    const end = timeToTimestamp(row.end);
    datasets[0].data.push([start, end]);

    minTime = minTime === undefined ? start : Math.min(minTime, start);
    maxTime = maxTime === undefined ? end : Math.max(maxTime, end);
  });

  const height = 10 + rows.length * 5;

  return (
    <div style={{ width: "100%" }}>
      <Bar
        height={height}
        options={{
          indexAxis: "y",
          responsive: true,
          animation: {
            duration: 0,
          },
          scales: {
            x: {
              type: "time",
              beginAtZero: false,
              min: minTime,
              max: maxTime,
              ticks: {
                autoSkip: true,
                maxTicksLimit: 10,
                callback: (value) => {
                  return `${dateFormat(
                    dateAddMinutes(value, timezoneOffset),
                    "HH:mm:ss.SSS"
                  )}Z`;
                },
              },
            },
            y: {
              ticks: {
                autoSkip: false,
              },
            },
          },
          plugins: {
            legend: {
              display: false,
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  return [
                    `From: ${dateFormat(
                      dateAddMinutes(context.raw[0], timezoneOffset),
                      "HH:mm:ss.SSS"
                    )}Z`,
                    `To: ${dateFormat(
                      dateAddMinutes(context.raw[1], timezoneOffset),
                      "HH:mm:ss.SSS"
                    )}Z`,
                    `Duration: ${(
                      (context.raw[1] - context.raw[0]) /
                      1000
                    ).toFixed(2)}s`,
                  ];
                },
              },
            },
          },
        }}
        data={{
          labels: labels,
          datasets: datasets,
        }}
      />
    </div>
  );
}

TimelineAssertion.propTypes = {
  assertion: PropTypes.object,
};
