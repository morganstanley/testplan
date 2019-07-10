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
  let options = this.props.assertion.options;
  const graph_type = this.props.assertion.graph_type
  const GraphComponent = this.components[graph_type];
      return (
       <GraphComponent
      colorType= {GraphUtil.returnColour(options)}
      data={data}
      width={400}
      height={300}
      getLabel={d => d.name}
      labelsRadiusMultiplier={1.1}
      labelsStyle={{fontSize: 16}}
      showLabels
       />
     )
  }
}
DiscreteChartAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};


export default DiscreteChartAssertion;