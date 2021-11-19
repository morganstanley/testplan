import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Card, CardBody, Collapse } from 'reactstrap';
import { css, StyleSheet } from 'aphrodite';

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
import { BASIC_ASSERTION_TYPES } from '../Common/defaults';
import XYGraphAssertion
  from './AssertionTypes/GraphAssertions/XYGraphAssertion';
import DiscreteChartAssertion
  from './AssertionTypes/GraphAssertions/DiscreteChartAssertion';
import SummaryBaseAssertion from './AssertionSummary';
import AttachmentAssertion from './AssertionTypes/AttachmentAssertions';
import PlotlyAssertion from './AssertionTypes/PlotlyAssertion';
import AttachedDirAssertion from './AssertionTypes/AttachedDirAssertion';
import { EXPAND_STATUS } from "../Common/defaults";

/**
 * Component to render one assertion.
 */
class Assertion extends Component {

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
      (nextProps.expand !== this.props.expand) ||
      // Inside the group assertions may need to be updated
      (nextProps.assertion.type === 'Group') ||
      !timeInfoIsEqual(
        nextProps.assertion.timeInfoArray, this.props.timeInfoArray);
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
      MatPlot: AttachmentAssertion,
      Markdown: MarkdownAssertion,
      CodeLog: CodeLogAssertion,
      Plotly: PlotlyAssertion,
      Directory: AttachedDirAssertion,
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
            assertionGroupUid={this.props.uid}
            entries={this.props.assertion.entries}
            filter={this.props.filter}
            reportUid={this.props.reportUid}
            displayPath={this.props.displayPath}
          />
        );
        break;
      case 'Summary':
        assertionType = (
          <SummaryBaseAssertion
            assertion={this.props.assertion}
            assertionGroupUid={this.props.uid}
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
          uid={this.props.uid}
          toggleExpand={this.props.toggleExpand}
          index={this.props.index}
          displayPath={this.props.displayPath}
        />
        <Collapse
          isOpen={this.props.expand === EXPAND_STATUS.EXPAND}
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
            {this.props.expand === EXPAND_STATUS.EXPAND
                ? assertionType : null
            }
          </CardBody>
        </Collapse>
      </Card>
    );
  }
}

Assertion.propTypes = {
  /** Assertion to be rendered */
  assertion: PropTypes.object,
  /** Expand status of the assertion */
  expand: PropTypes.string,
  /** Expand status update function of the assertion */
  toggleExpand: PropTypes.func,
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
