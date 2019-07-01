import React, {Component} from 'react';
import PropTypes from 'prop-types';
import '../../../../node_modules/react-vis/dist/style.css';
import './App.css';
import * as GraphUtil from './graphUtils';

import {
  XAxis,
  YAxis,
  HorizontalGridLines,
  XYPlot,
  LineSeries,
VerticalBarSeries,
  Highlight,
  HexbinSeries,
  ContourSeries,
  WhiskerSeries
} from 'react-vis';

/**
 * Component that are used to render a Graph (Data visualisations that require an XY axis).
 */
class BasicGraphAssertion extends Component {

        state = {
            lastDrawLocation: null,
            series: [
              {
                data: this.props.assertion.data,
                title: 'Test'
              }
            ]
         };

    components = {
    Line: LineSeries,
    Hexbin: HexbinSeries,
    Contour: ContourSeries,
    Whisker: WhiskerSeries,
    Bar: VerticalBarSeries
    }

  render() {
    let data = this.props.assertion.data;
    const {series, lastDrawLocation} = this.state;
    const graph_type = this.props.assertion.graph_type
    const GraphType = this.components[graph_type];
    var x_range = [GraphUtil.getMinX(data, graph_type), GraphUtil.getMaxX(data, graph_type)];
    var y_range = [GraphUtil.getMinY(data, graph_type), GraphUtil.getMaxY(data, graph_type)];
    return (
      <div>
        <div>
          <XYPlot
            animation
            xDomain={ x_range &&
              lastDrawLocation && [
                lastDrawLocation.left,
                lastDrawLocation.right
              ]
            }
            yDomain={ y_range &&
              lastDrawLocation && [
                lastDrawLocation.bottom,
                lastDrawLocation.top
              ]
            }
            width={750}
            height={500}
             xType= {GraphUtil.returnXType(graph_type)}
          >
            <HorizontalGridLines />

            <YAxis />
            <XAxis />

            {series.map(entry => (
              <GraphType
              key={entry.title}
              data={entry.data}
              colorRange={['blue', 'purple', 'red']}
              style = {GraphUtil.returnStyle(graph_type)}
              radius = {GraphUtil.returnRadius(graph_type)}
              />
            ))}
            <Highlight
              onBrushEnd={area => this.setState({lastDrawLocation: area})}
              onDrag={area => {
                this.setState({
                  lastDrawLocation: {
                    bottom: lastDrawLocation.bottom + (area.top - area.bottom),
                    left: lastDrawLocation.left - (area.right - area.left),
                    right: lastDrawLocation.right - (area.right - area.left),
                    top: lastDrawLocation.top + (area.top - area.bottom)
                  }
                });
              }}
            />

          </XYPlot>
        </div>

        <button
          className="showcase-button"
          onClick={() => this.setState({lastDrawLocation: null})}
        >
          Reset Zoom
        </button>
      </div>
    );
  }
}

BasicGraphAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};


export default BasicGraphAssertion;