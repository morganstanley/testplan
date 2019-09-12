import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {Col, Row} from 'reactstrap';
import AssertionGroup from './AssertionGroup';
/**
 * Component used to render a large test case when summarize = true
 */

class SummaryBaseAssertion extends Component  {
  render(){
    let data = this.props.assertion;
    let summaries = data.entries;

    // Go through categories e.g Category: DEFAULT
    return summaries.map(category =>{
           let category_description = category.description;

           // Go through assertion types e.g Assertion type: Equal
           let assertions_types =
           category.entries.map(assertions_types =>{
              let description =
              (
                <Row>
                 <Col sm={{ offset: 1 }}
                    style={{ fontSize: 18 }}>
                   <strong>{assertions_types.description}</strong>
                 </Col>
                </Row>
              );

              // State how many assertions are being displayed e.g 5 of 500
              // Create an AssertionGroup for each grouped type of assertion
              // e.g all result.Equal() in Category: DEFAULT
              let entries =
              assertions_types.entries.map(single_assertion_group =>
                <div key={single_assertion_group.description}>
                  <Row>
                    <Col sm={{ offset: 1 }}>
                      {single_assertion_group.description}
                    </Col>
                  </Row>
                  <Row>
                   <Col sm={{ offset: 2 }}>
                     <AssertionGroup
                        entries={single_assertion_group.entries}
                        globalIsOpen={this.props.globalIsOpen}
                        resetGlobalIsOpen={this.props.resetGlobalIsOpen}
                        filter={this.props.filter}
                      />
                   </Col>
                  </Row>
                </div>
               );

              return  (
                       <div key={assertions_types.description}>
                        {description}
                        {entries}
                      </div>
              );
          });

           return (
                   <div key={category.description}>
                    <Row>
                      <Col lg='14' style={{ fontSize: 20 }}>
                        <strong>{category_description}</strong>
                      </Col>
                    </Row>
                     <Row>
                      <Col lg='12'>
                       {assertions_types}
                      </Col>
                    </Row>
                  </div>
            );
    });
  }
}

SummaryBaseAssertion.propTypes = {
  assertion: PropTypes.object,
  /** Array of assertions to be rendered */
  entries: PropTypes.arrayOf(PropTypes.object),
  /** State of the expand all/collapse all functionality */
  globalIsOpen: PropTypes.bool,
  /** Function to reset the expand all/collapse all state if an individual
   * assertion's visibility is changed */
  resetGlobalIsOpen: PropTypes.func,
  /** Assertion filter */
  filter: PropTypes.string,
};


export default SummaryBaseAssertion;