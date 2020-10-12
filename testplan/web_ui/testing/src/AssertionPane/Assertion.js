import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {Card, CardBody, Collapse} from 'reactstrap';
import {css, StyleSheet} from 'aphrodite';

import BasicAssertion from './AssertionTypes/BasicAssertion';
import MarkdownAssertion from './AssertionTypes/MarkdownAssertion';
import CodeLogAssertion from './AssertionTypes/CodeLogAssertion';
import TableLogAssertion
  from './AssertionTypes/TableAssertions/TableLogAssertion';
import TableMatchAssertion
  from './AssertionTypes/TableAssertions/TableMatchAssertion';
import ColumnContainAssertion
  from './AssertionTypes/TableAssertions/ColumnContainAssertion';
import DictLogAssertion from './AssertionTypes/DictAssertions/DictLogAssertion';
import FixLogAssertion from './AssertionTypes/DictAssertions/FixLogAssertion';
import DictMatchAssertion
  from './AssertionTypes/DictAssertions/DictMatchAssertion';
import FixMatchAssertion
  from './AssertionTypes/DictAssertions/FixMatchAssertion';
import NotImplementedAssertion from './AssertionTypes/NotImplementedAssertion';
import AssertionHeader from './AssertionHeader';
import AssertionGroup from './AssertionGroup';
import {BASIC_ASSERTION_TYPES} from '../Common/defaults';
import XYGraphAssertion
  from './AssertionTypes/GraphAssertions/XYGraphAssertion';
import DiscreteChartAssertion
  from './AssertionTypes/GraphAssertions/DiscreteChartAssertion';
import SummaryBaseAssertion from './AssertionSummary';
import {
  AttachmentAssertion,
  MatplotAssertion
} from './AssertionTypes/AttachmentAssertions.js';

/**
 * Component to render one assertion.
 */
class Assertion extends Component {
  constructor(props) {
    super(props);

    this.toggleAssertion = this.toggleAssertion.bind(this);
    this.state = {
      isOpen: this.props.assertion.passed === false,
    };
  }

  shouldComponentUpdate(nextProps, nextState) {
    const timeInfoIsEqual = (arr1, arr2) => {
      if (arr1 === undefined && arr2 === undefined) {
        return true;
      } else if (arr1 !== undefined && arr2 !== undefined &&
                 arr1.length === arr2.length) {
        return true;
      } else {
        return false;
      }
    };

    // If we used a PureComponent it would do a shallow prop comparison which
    // might suffice and we wouldn't need to include this.
    return (nextProps.assertion !== this.props.assertion) ||
      (nextProps.globalIsOpen !== this.props.globalIsOpen) ||
      (nextState.isOpen !== this.state.isOpen) ||
      // Inside the group assertions may need to be updated
      (nextProps.assertion.type === 'Group') ||
      !timeInfoIsEqual(
        nextProps.assertion.timeInfoArray, this.props.timeInfoArray);
  }

  /**
   * Toggle the visibility of the assertion.
   * @public
   */
  toggleAssertion() {
    this.setState({isOpen: !this.state.isOpen});
    this.props.resetGlobalIsOpen();
  }

  /**
   * Set the state on props change. If expand all/collapse all buttons are
   * clicked, the assertion's state must be overwritten to the global state.
   *
   * @param {object} props - Current props.
   * @param {object} state - Previous state.
   * @returns {object|null} - Return the new state if the global state changed
   * or null otherwise.
   * @public
   */
  static getDerivedStateFromProps(props, state) {
    if (
      props.globalIsOpen !== undefined &&
      props.globalIsOpen !== state.isOpen
    ) {
      return {isOpen: props.globalIsOpen};
    }
    return null;
  }

  /**
   * Get the component object of the assertion.
   * @param {String} props - Assertion type props.
   * @returns {Object|null} - Return the assertion component class if the
   * assertion is implemented.
   * @public
   */
  assertionComponent(assertionType) {
    let graphAssertion;
    if (this.props.assertion.discrete_chart) {
      graphAssertion = DiscreteChartAssertion;
    } else {
      graphAssertion = XYGraphAssertion;
    }

    const assertionMap = {
      TableLog: TableLogAssertion,
      TableMatch: TableMatchAssertion,
      TableDiff: TableMatchAssertion,
      ColumnContain: ColumnContainAssertion,
      DictLog: DictLogAssertion,
      DictMatch: DictMatchAssertion,
      FixLog: FixLogAssertion,
      FixMatch: FixMatchAssertion,
      Graph: graphAssertion,
      Attachment: AttachmentAssertion,
      MatPlot: MatplotAssertion,
      Markdown: MarkdownAssertion,
      CodeLog: CodeLogAssertion,
    };
    if (assertionMap[assertionType]) {
      return assertionMap[assertionType];
    } else if (BASIC_ASSERTION_TYPES.indexOf(assertionType) >= 0) {
      return BasicAssertion;
    }
    return null;
  }

  render() {
    let isAssertionGroup = false;
    let assertionType = this.props.assertion.type;
    switch (assertionType) {
      case 'Group':
        isAssertionGroup = true;
        assertionType = (
          <AssertionGroup
            entries={this.props.assertion.entries}
            globalIsOpen={this.props.globalIsOpen}
            resetGlobalIsOpen={this.props.resetGlobalIsOpen}
            filter={this.props.filter}
          />
        );
        break;
      case 'Summary':
        assertionType = (
          <SummaryBaseAssertion
            assertion={this.props.assertion}
            globalIsOpen={this.props.globalIsOpen}
            resetGlobalIsOpen={this.props.resetGlobalIsOpen}
            filter={this.props.filter}
          />
        );
        break;
      default: {
        const AssertionTypeComponent = this.assertionComponent(assertionType);
        if (AssertionTypeComponent) {
          assertionType = (
            <AssertionTypeComponent
              assertion={this.props.assertion}
              reportUid={this.props.reportUid}
            />
          );
        } else {
          assertionType = <NotImplementedAssertion />;
        }
      }
    }

    return (
      <Card className={css(styles.card)}>
        <AssertionHeader
          assertion={this.props.assertion}
          onClick={this.toggleAssertion}
          index={this.props.index}
        />
        <Collapse
          isOpen={this.state.isOpen}
          className={css(styles.collapseDiv)}
          style={{ paddingRight: isAssertionGroup ? null : '1.25rem' }}
        >
          <CardBody
            className={
              css(
                isAssertionGroup
                  ? styles.groupCardBody
                  : styles.assertionCardBody
              )
            }
          >
            {assertionType}
          </CardBody>
        </Collapse>
      </Card>
    );
  }
}

Assertion.propTypes = {
  /** Assertion to be rendered */
  assertion: PropTypes.object,
  /** State of the expand all/collapse all functionality */
  globalIsOpen: PropTypes.bool,
  /** Function to reset the expand all/collapse all state if an individual
   * assertion's visibility is changed */
  resetGlobalIsOpen: PropTypes.func,
  /** Index of the assertion */
  index: PropTypes.number,
  /** Assertion filter */
  filter: PropTypes.string,
  /** Report Uid */
  reportUid: PropTypes.string,
};

const styles = StyleSheet.create({
  assertionCardBody: {
    padding: '.5rem .75rem',
    fontSize: '13px',
    fontFamily: 'monospace',
  },

  groupCardBody: {
    padding: '0rem',
  },

  card: {
    margin: '.5rem 0rem .5rem .5rem',
    border: '0px',
  },

  collapseDiv: {
    paddingLeft: '1.25rem',
  }
});

export default Assertion;
