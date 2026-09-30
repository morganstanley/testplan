import PropTypes from "prop-types";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { Pie } from "react-chartjs-2";
import * as GraphUtil from "./graphUtils";

ChartJS.register(ArcElement, Tooltip, Legend);

const PIE_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: true },
  },
};

/**
 * Component that are used to render a Chart (Data visualisations that don't
 * require an XY axis). Currently will only render pie charts
 * correctly (not generalised for other charts).
 */
function DiscreteChartAssertion({ assertion }) {
  const components = { Pie };
  const data = assertion.graph_data;
  const graph_type = assertion.graph_type;
  const seriesColour = GraphUtil.returnColour(assertion.series_options, data);
  const GraphComponent = components[graph_type];

  const plots = [];

  for (let key in data) {
    const slices = data[key];
    const colour = seriesColour[key];
    plots.push(
      <div key={key} style={{ width: 400, height: 300 }}>
        <GraphComponent
          data={{
            labels: slices.map((slice) => slice.name),
            datasets: [
              {
                data: slices.map((slice) => slice.angle),
                backgroundColor: slices.map((slice) =>
                  colour === "literal" ? slice.color : colour
                ),
              },
            ],
          }}
          options={PIE_OPTIONS}
        />
      </div>
    );
  }

  return (
    <div>
      {plots}
      <p>(Hover over chart to see labels)</p>
    </div>
  );
}
DiscreteChartAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};

export default DiscreteChartAssertion;
