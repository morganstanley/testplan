import React, { Component } from "react";
import PropTypes from "prop-types";
import { Col, Row } from "reactstrap";
import AssertionGroup from "./AssertionGroup";
/**
 * Component used to render a large test case when summarize = true
 */

class SummaryBaseAssertion extends Component {
  render() {
    let data = this.props.assertion;
    let summaries = data.entries;

    // Go through categories e.g Category: DEFAULT
    return summaries.map((category) => {
      let category_description = category.description;

      // Go through assertion types e.g Assertion type: Equal
      let assertions_types = category.entries.map((assertions_types) => {
        let description = (
          <Row>
            <Col sm={{ offset: 1 }} style={{ fontSize: "small" }}>
              <strong>{assertions_types.description}</strong>
            </Col>
          </Row>
        );

        // State how many assertions are being displayed e.g 5 of 500
        // Create an AssertionGroup for each grouped type of assertion
        // e.g all result.Equal() in Category: DEFAULT
        let entries = assertions_types.entries.map((single_assertion_group) => (
          <div key={single_assertion_group.description}>
            <Row>
              <Col sm={{ offset: 1 }}>{single_assertion_group.description}</Col>
            </Row>
            <Row>
              <Col sm={{ offset: 2 }}>
                <AssertionGroup
                  assertionGroupUid={this.props.assertionGroupUid}
                  entries={single_assertion_group.entries}
                  filter={this.props.filter}
                  displayPath={this.props.displayPath}
                />
              </Col>
            </Row>
          </div>
        ));

        return (
          <div key={assertions_types.description}>
            {description}
            {entries}
          </div>
        );
      });

      return (
        <div key={category.description}>
          <Row>
            <Col lg="14" style={{ fontSize: "small" }}>
              <strong>{category_description}</strong>
            </Col>
          </Row>
          <Row>
            <Col lg="12">{assertions_types}</Col>
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
  /** Assertion group unique id */
  assertionGroupUid: PropTypes.string,
  /** Assertion filter */
  filter: PropTypes.string,
};

export default SummaryBaseAssertion;
