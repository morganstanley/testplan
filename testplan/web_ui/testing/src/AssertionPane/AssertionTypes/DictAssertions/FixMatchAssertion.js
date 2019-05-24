import React, {Component} from 'react';
import PropTypes from 'prop-types';
import DictBaseAssertion from './DictBaseAssertion';
import FixCellRenderer from './FixCellRenderer';
import DictButtonGroup from './DictButtonGroup';
import {
  prepareDictColumnDefs,
  prepareDictRowData,
  sortFlattenedJSON,
  dictCellStyle,
} from './dictAssertionUtils';
import {SORT_TYPES} from './../../../Common/defaults';


/**
 * Component that renders FixMatch assertion.
 *
 * The expected dictionary   | The actual dictionary matched
 * of the test:              | to the expected one:
 *
 * {                         | {
 *   'foo': {                |   'foo': {
 *     'alpha': 'blue',      |     'alpha': 'red',
 *     'beta': 'green',      |     'beta': 'green',
 *   }                       |   }
 *   'bar': true             |   'bar': true
 * }                         | }
 *
 *  ______________________________________
 * | Key        | Expected   | Value      |
 * |------------|------------|------------|
 * | *foo       |            |            |
 * |   *alpha   | blue       | red        |
 * |   *beta    | green      | green      |
 * | *bar       | true       | true       |
 * |____________|____________|____________|
 *
 * The grid consists of three columns: Key, Expected and Value.
 *  - Key: a key of the dictionary. Nested objects are displayed with indented
 *    keys.
 *  - Expected: expected value for the given key.
 *  - Value: Actual value for the given key.
 *
 */
class FixMatchAssertion extends Component {
  constructor(props) {
    super(props);

    this.flattenedDict = this.props.assertion.comparison;
    this.columnDefs = prepareDictColumnDefs(
      dictCellStyle, FixCellRenderer, true
    );
    this.state = {
      rowData: prepareDictRowData(
        sortFlattenedJSON(this.flattenedDict, 0, false, true),
        this.props.assertion.line_no
      ),
    };

    this.setRowData = this.setRowData.bind(this);
  }

  setRowData(sortedData) {
    this.setState({
      rowData: prepareDictRowData(
        sortedData,
        this.props.assertion.line_no)
    });
  }

  render() {
    let buttonGroup = (
      <DictButtonGroup
        sortTypeList={[
          SORT_TYPES.ALPHABETICAL, 
          SORT_TYPES.REVERSE_ALPHABETICAL,
          SORT_TYPES.BY_STATUS,
          SORT_TYPES.ONLY_FAILURES
        ]}
        flattenedDict={this.flattenedDict}
        setRowData={this.setRowData}
        defaultSortType={SORT_TYPES.BY_STATUS}
      />
    );

    return (
			<DictBaseAssertion
        buttonGroup={buttonGroup}
        columnDefs={this.columnDefs}
        rowData={this.state.rowData}
      />
		);
  }
}

FixMatchAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object.isRequired,
};

export default FixMatchAssertion;