import React, {Component, Fragment} from 'react';
import PropTypes from 'prop-types';
import {Col, Row} from 'reactstrap';
import AssertionGroup from './AssertionGroup';
/**
 * Component that are used to render a large test case when Summary = true
 */

class SummaryBaseAssertion extends Component  {
  constructor(props) {
    super(props);
    }

    getAssertionResults(assertion_entries){
        let assertion_jsx = [];
        for(let assertion_index in assertion_entries){
            //Assertions are grouped by type
            let single_assertion_group = assertion_entries[assertion_index];

            assertion_jsx.push(
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
     return assertion_jsx
    }

  render(){
    let render = [];
    let data = this.props.assertion;
    let summaries = data.entries;
    //Loop through summary categories
    for (let summary_category_index in summaries){
        let category_description = summaries[summary_category_index].description
        let assertions_types_list = summaries[summary_category_index].entries
        let summary_jsx =  []

        //Loop through assertion types (Assertions grouped by assertion types)
        for(let assertion_type_index in assertions_types_list){
            let single_assertion_type = assertions_types_list[assertion_type_index]

            //Display the Assertion type e.g AssertionType: Equal
            summary_jsx.push(
                               <Row>
                                 <Col sm={{ offset: 1 }}>
                                     {single_assertion_type.description}
                                 </Col>
                               </Row>
                              )
            //Display the ALL Assertion content for that type
            summary_jsx.push(this.getAssertionResults(single_assertion_type.entries))

        }

        render.push(
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
             {render}
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