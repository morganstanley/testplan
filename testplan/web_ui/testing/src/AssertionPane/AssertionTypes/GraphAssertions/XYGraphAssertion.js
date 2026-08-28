import { useRef } from "react";
import PropTypes from "prop-types";
import {
  Chart as ChartJS,
  LineController,
  BarController,
  ScatterController,
  LineElement,
  PointElement,
  BarElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from "chart.js";
import zoomPlugin from "chartjs-plugin-zoom";
import { Line, Bar, Scatter } from "react-chartjs-2";
import * as GraphUtil from "./graphUtils";

ChartJS.register(
  LineController,
  BarController,
  ScatterController,
  LineElement,
  PointElement,
  BarElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  zoomPlugin
);

const components = {
  Line,
  Scatter,
  Bar,
};

const ZOOM_OPTIONS = {
  zoom: {
    drag: { enabled: true },
    mode: "xy",
  },
};

/**
 * Component that are used to render a Graph (Data visualisations that require
 * an XY axis).
 */
function XYGraphAssertion({ assertion }) {
  const chartRef = useRef(null);

  const data = assertion.graph_data;
  const seriesColour = GraphUtil.returnColour(assertion.series_options, data);
  const graph_options = assertion.graph_options;
  const graph_type = assertion.graph_type;
  const GraphComponent = components[graph_type];

  if (!GraphComponent) {
    return (
      <div>
        Graph type "{graph_type}" is removed and is no longer rendered
        in the web report.
      </div>
    );
  }

  const datasets = Object.entries(data).map(([series, values]) => ({
    label: series,
    data: values,
    borderColor: seriesColour[series],
    backgroundColor: seriesColour[series],
    tension: 0,
  }));

  const xAxisTitle = GraphUtil.returnXAxisTitle(graph_options);
  const yAxisTitle = GraphUtil.returnYAxisTitle(graph_options);

  return (
    <div
      style={{ width: 750, height: 500 }}
      onDoubleClick={() => chartRef.current?.resetZoom?.()}
    >
      <GraphComponent
        ref={chartRef}
        data={{ datasets }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              type: graph_type === "Bar" ? "category" : "linear",
              title: {
                display: Boolean(xAxisTitle),
                text: xAxisTitle,
              },
            },
            y: {
              title: {
                display: Boolean(yAxisTitle),
                text: yAxisTitle,
              },
            },
          },
          plugins: {
            legend: {
              display: Boolean(graph_options?.legend),
            },
            zoom: ZOOM_OPTIONS,
          },
        }}
      />
    </div>
  );
}

XYGraphAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};

export default XYGraphAssertion;
