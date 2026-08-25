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
import { timeToTimestamp } from "../../../Common/utils";
import * as GraphUtil from "./graphUtils";

ChartJS.register(
  BarElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  TimeSeriesScale
);

/**
 * Component used to render a Timeline chart. Every series in
 * graph_data is drawn as its own coloured floating-bar dataset, keeping the
 * bars for different series aligned to the shared row labels.
 */
export default function TimelineChartAssertion({ assertion }) {
  const timezoneOffset = new Date().getTimezoneOffset();
  const data = assertion.graph_data;
  const graph_options = assertion.graph_options;
  const seriesColour = GraphUtil.returnColour(assertion.series_options, data);

  const labels = Object.values(data)
    .flat()
    .map((row) => row.name);

  let minTime;
  let maxTime;
  let offset = 0;
  const datasets = Object.entries(data).map(([series, rows]) => {
    const values = new Array(labels.length).fill(null);

    rows.forEach((row, i) => {
      const start = timeToTimestamp(row.start);
      const end = timeToTimestamp(row.end);
      values[offset + i] = [start, end];

      minTime = minTime === undefined ? start : Math.min(minTime, start);
      maxTime = maxTime === undefined ? end : Math.max(maxTime, end);
    });
    offset += rows.length;

    return {
      label: series,
      data: values,
      backgroundColor: seriesColour[series],
      borderColor: seriesColour[series],
      borderWidth: 2,
      borderRadius: Number.MAX_VALUE,
      borderSkipped: false,
      barThickness: 6,
      minBarLength: 2,
    };
  });

  const xAxisTitle = GraphUtil.returnXAxisTitle(graph_options);
  const yAxisTitle = GraphUtil.returnYAxisTitle(graph_options);

  const height = 10 + labels.length * 5;

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
              stacked: true,
              beginAtZero: false,
              min: minTime,
              max: maxTime,
              title: {
                display: Boolean(xAxisTitle),
                text: xAxisTitle,
              },
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
              stacked: true,
              title: {
                display: Boolean(yAxisTitle),
                text: yAxisTitle,
              },
              ticks: {
                autoSkip: false,
              },
            },
          },
          plugins: {
            legend: {
              display: Boolean(graph_options?.legend),
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

TimelineChartAssertion.propTypes = {
  assertion: PropTypes.object,
};
