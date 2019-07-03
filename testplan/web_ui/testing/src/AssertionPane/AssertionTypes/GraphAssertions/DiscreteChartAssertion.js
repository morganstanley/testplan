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
  let data = this.props.assertion.data;
  const graph_type = this.props.assertion.graph_type
  const GraphComponent = this.components[graph_type];
      return (
       <GraphComponent
      colorType={'literal'}
      colorDomain={[0, 100]}
      colorRange={[0, 10]}
      margin={{top: 100}}
      getLabel={d => d.name}
      data={data}
      labelsRadiusMultiplier={1.1}
      labelsStyle={{fontSize: 16, fill: '#222'}}
      showLabels
      style={{stroke: '#fff', strokeWidth: 2}}
      width={400}
      height={300}
       />
     )
  }
}
DiscreteChartAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};


export default DiscreteChartAssertion;