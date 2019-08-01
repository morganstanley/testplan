import React, {Component, Fragment} from 'react';
import PropTypes from 'prop-types';
import {Col, Row} from 'reactstrap';
import AssertionGroup from './AssertionGroup';
/**
 * Component used to render a large test case when summarize = true
 */

class SummaryBaseAssertion extends Component  {
    displayAssertionGroup(assertion_entries){
        let group_assertion_jsx = [];
        let entries_len = assertion_entries.length
        for(var assertion_index = 0; assertion_index < entries_len; assertion_index++){

            let single_assertion_group = assertion_entries[assertion_index];

            //Create an AssertionGroup component to render assertions of singular type e.g result.Equal
            group_assertion_jsx.push(
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
                              )

        }
     return group_assertion_jsx
    }

  render(){
    let summary_component = [];
    let data = this.props.assertion;
    let summaries = data.entries;

    //Loop through summary categories e.g Category: DEFAULT
    let summary_len = summaries.length;
    for (var summary_index = 0; summary_index < summary_len; summary_index++){
        let category_description = summaries[summary_index].description
        let assertions_types_list = summaries[summary_index].entries
        let summary_jsx =  []

        let type_len = assertions_types_list.length;
        for(var type_index  = 0; type_index < type_len; type_index++){
            let assertion_type = assertions_types_list[type_index]

            //Display the Assertion type as text e.g AssertionType: Equal
            summary_jsx.push(
                               <Row>
                                 <Col sm={{ offset: 1 }}>
                                     {assertion_type.description}
                                 </Col>
                               </Row>
                              )

            summary_jsx.push(this.displayAssertionGroup(assertion_type.entries))

        }

        summary_component.push(
         <div>
          <Fragment>
                <Row>
                  <Col lg='14'>
                    <strong>{category_description}</strong>
                  </Col>
                </Row>
                 <Row>
                  <Col lg='12'>
                   {summary_jsx}
                  </Col>
                </Row>
              </Fragment>
          </div>
         )
    }

      return (
           <div>
             {summary_component}
           </div>
     )
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