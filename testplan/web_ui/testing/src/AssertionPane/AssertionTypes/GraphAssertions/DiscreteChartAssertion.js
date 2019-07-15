import React, {Component} from 'react';
import PropTypes from 'prop-types';
import 'react-vis/dist/style.css';
import './App.css';
import * as GraphUtil from './graphUtils';
import {
  RadialChart
} from 'react-vis';

/**
 * Component that are used to render a Chart (Data visualisations that don't require an XY axis).
 */

class DiscreteChartAssertion extends Component  {
  components = {
    Pie: RadialChart
    }


  render(){
    let data = this.props.assertion.graph_data;
    const graph_type = this.props.assertion.graph_type
    const GraphComponent = this.components[graph_type];
    let series_options = this.props.assertion.series_options;
    let graph_options = this.props.assertion.graph_options;

    var plots = [];
    var plot_options;
    var series_colour;

    for (var key in data) {
        if(series_options !== null){
          plot_options = series_options[key];
        }
        series_colour = GraphUtil.returnColour(plot_options)
        plots.push(
                     <GraphComponent
                      colorType= {series_colour}
                      data={data[key]}
                      width={400}
                      height={300}
                      getLabel={d => d.name}
                      labelsRadiusMultiplier={1.1}
                      labelsStyle={{fontSize: 16}}
                      showLabels
                      />
         );
    }
      return (
           <div>
              {plots}
           </div>
     )
  }
}
DiscreteChartAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};


export default DiscreteChartAssertion;