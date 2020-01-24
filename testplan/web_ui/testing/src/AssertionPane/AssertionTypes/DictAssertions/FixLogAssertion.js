import React, {Component} from 'react';
import PropTypes from 'prop-types';
import DictBaseAssertion from './DictBaseAssertion';
import FixCellRenderer from './FixCellRenderer';
import DictButtonGroup from './DictButtonGroup';
import {
  prepareDictColumnDefs,
  prepareDictRowData,
  dictCellStyle,
} from './dictAssertionUtils';
import {SORT_TYPES} from './../../../Common/defaults';

/**
 * Component that renders FixLog assertion.
 *
 * The actual dictionary of the test:            
 *
 * {                         
 *   'foo': {               
 *     'alpha': 'blue',     
 *     'beta': 'green',     
 *   }                      
 *   'bar': true            
 * }
 *
 *  _________________________
 * | Key        | Value      |
 * |------------|------------|
 * | *foo       |            |
 * |   *alpha   | blue       |
 * |   *beta    | green      |
 * | *bar       | true       |
 * |____________|____________|
 *
 * The grid consists of two columns: Key and Value.
 *  - Key: a key of the dictionary. Nested objects are displayed with indented
 *    keys.
 *  - Value: Actual value for the given key.
 *
 */
class FixLogAssertion extends Component {
  constructor(props) {
    super(props);

    this.flattenedDict = this.props.assertion.flattened_dict;
    this.columnDefs = prepareDictColumnDefs(dictCellStyle, FixCellRenderer);
    this.state = {
      rowData: 
        prepareDictRowData(this.flattenedDict, this.props.assertion.line_no),
    };
    this.setRowData = this.setRowData.bind(this);
  }

  setRowData(sortedData) {
    this.setState({
      rowData: prepareDictRowData(
        sortedData,
        this.props.assertion.line_no
      )
    });
  }

  render() {
    let buttonGroup = (
      <DictButtonGroup
        sortTypeList={[
          SORT_TYPES.ALPHABETICAL, 
          SORT_TYPES.REVERSE_ALPHABETICAL
        ]}
        flattenedDict={this.flattenedDict}
        setRowData={this.setRowData}
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

FixLogAssertion.propTypes = {
  /** Assertion being rendered */
	assertion: PropTypes.object.isRequired,
};

export default FixLogAssertion;