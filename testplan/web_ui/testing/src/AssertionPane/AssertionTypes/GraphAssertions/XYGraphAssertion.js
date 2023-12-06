import { useState } from "react";
import PropTypes from "prop-types";
import "react-vis/dist/style.css";
import * as GraphUtil from "./graphUtils";
import { css, StyleSheet } from "aphrodite";
import {
  XAxis,
  YAxis,
  DiscreteColorLegend,
  HorizontalGridLines,
  XYPlot,
  LineSeries,
  VerticalBarSeries,
  Highlight,
  HexbinSeries,
  ContourSeries,
  WhiskerSeries,
  MarkSeries,
  ChartLabel,
} from "react-vis";

const components = {
  Line: LineSeries,
  Hexbin: HexbinSeries,
  Contour: ContourSeries,
  Whisker: WhiskerSeries,
  Bar: VerticalBarSeries,
  Scatter: MarkSeries,
};

/**
 * Component that are used to render a Graph (Data visualisations that require
 * an XY axis).
 */
function XYGraphAssertion({ assertion }) {
    const [lastDrawLocation, setLastDrawLocation] = useState(null);

    const data = assertion.graph_data;
    const seriesColour = GraphUtil.returnColour(assertion.series_options, data);
    const graph_options = assertion.graph_options;
    const graph_type = assertion.graph_type;
    const GraphComponent = components[graph_type];

    let legend = [];
    let plots = [];

    for (let key in data) {
      let series_colour = seriesColour[key];
      plots.push(
        <GraphComponent
          key={key}
          data={data[key]}
          color={series_colour}
          style={GraphUtil.returnStyle(graph_type)}
        />
      );
      if (graph_options !== null && graph_options.legend) {
        legend.push({ title: key, color: series_colour });
      }
    }

    return (
      <div className={css(styles.centreComponent)}>
        <XYPlot
          animation
          xDomain={
            lastDrawLocation && [lastDrawLocation.left, lastDrawLocation.right]
          }
          yDomain={
            lastDrawLocation && [lastDrawLocation.bottom, lastDrawLocation.top]
          }
          width={750}
          height={500}
          xType={GraphUtil.returnXType(graph_type)}
        >
          <HorizontalGridLines />

          <XAxis />
          <ChartLabel
            text={GraphUtil.returnXAxisTitle(graph_options)}
            className="x-axis-label"
            includeMargin={false}
            xPercent={0.5}
            yPercent={1.107}
            style={{
              transform: "rotate(0)",
              textAnchor: "middle",
            }}
          />

          <YAxis />
          <ChartLabel
            text={GraphUtil.returnYAxisTitle(graph_options)}
            className="y-axis-label"
            includeMargin={false}
            xPercent={-0.0455}
            yPercent={0.5}
            style={{
              transform: "rotate(270)",
              textAnchor: "middle",
            }}
          />

          {plots}

          <Highlight
            onBrushEnd={(area) => setLastDrawLocation(area)}
            onDrag={(area) => {
              setLastDrawLocation({
                bottom: lastDrawLocation.bottom + (area.top - area.bottom),
                left: lastDrawLocation.left - (area.right - area.left),
                right: lastDrawLocation.right - (area.right - area.left),
                top: lastDrawLocation.top + (area.top - area.bottom),
              });
            }}
          />
        </XYPlot>
        <DiscreteColorLegend
          orientation="horizontal"
          width={750}
          items={legend}
        />
      </div>
    );
  }

XYGraphAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};

const styles = StyleSheet.create({
  centreComponent: {
    alignItems: "center",
  },
});

export default XYGraphAssertion;
