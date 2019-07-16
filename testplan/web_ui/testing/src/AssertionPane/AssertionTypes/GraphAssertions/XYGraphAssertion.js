import React, {Component} from 'react';
import PropTypes from 'prop-types';
import 'react-vis/dist/style.css';
import './App.css';
import * as GraphUtil from './graphUtils';

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
  WhiskerSeries
} from 'react-vis';


/**
 * Component that are used to render a Graph (Data visualisations that require an XY axis).
 */
class XYGraphAssertion extends Component {
    constructor(props) {
      super(props);

      this.series_colour = {}
      let data = this.props.assertion.graph_data;
      let series_options = this.props.assertion.series_options;

      var plot_options;
      for (var key in data) {
           if(series_options !== null){
               plot_options = series_options[key];
            }
          var plot_colour = GraphUtil.returnColour(plot_options);
          this.series_colour[key] = plot_colour;
      }
    }


    state = {
        lastDrawLocation: null
     };


    components = {
        Line: LineSeries,
        Hexbin: HexbinSeries,
        Contour: ContourSeries,
        Whisker: WhiskerSeries,
        Bar: VerticalBarSeries
    }


  render() {
    let data = this.props.assertion.graph_data;
   // let series_options = this.props.assertion.series_options;
    let graph_options = this.props.assertion.graph_options;
    const {lastDrawLocation} = this.state;
    const graph_type = this.props.assertion.graph_type
    const GraphComponent = this.components[graph_type];

    var legend = [];
    var plots = [];

    for (var key in data) {
        var series_colour = this.series_colour[key]
        plots.push(
                    <GraphComponent
                      data={data[key]}
                      color={series_colour}
                      style = {GraphUtil.returnStyle(graph_type)}
                      radius = {GraphUtil.returnRadius(graph_type)}
                    />
                  );
        if((graph_options !== null) && graph_options.legend){
            legend.push({title: key, color: series_colour})
        }
    }

    return (
      <div>
        <div>
          <XYPlot
            animation
            xDomain={lastDrawLocation && [
                lastDrawLocation.left,
                lastDrawLocation.right
              ]
            }
            yDomain={lastDrawLocation && [
                lastDrawLocation.bottom,
                lastDrawLocation.top
              ]
            }
            width={750}
            height={500}
             xType= {GraphUtil.returnXType(graph_type)}
          >
            <HorizontalGridLines />

            <YAxis title = {GraphUtil.returnXAxisTitle(graph_options)}/>
            <XAxis title = {GraphUtil.returnYAxisTitle(graph_options)}/>

            {plots}

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
          <DiscreteColorLegend orientation = 'horizontal' width={750} items={legend}/>
        </div>
      </div>
    );
  }
}


XYGraphAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};


export default XYGraphAssertion;