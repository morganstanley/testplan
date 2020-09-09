import React, {useState} from 'react';
import PropTypes from 'prop-types';
import DictBaseAssertion from './DictBaseAssertion';
import FixCellRenderer from './FixCellRenderer';
import DictButtonGroup from './DictButtonGroup';
import {
  prepareDictColumn,
  prepareDictRowData,
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
export default function FixLogAssertion(props) {
  const flattenedDict = props.assertion.flattened_dict;
  const columns = prepareDictColumn(FixCellRenderer);

  const [rowData, setRowData] = useState(flattenedDict);

  const buttonGroup = (
    <DictButtonGroup
      sortTypeList={[
        SORT_TYPES.ALPHABETICAL, 
        SORT_TYPES.REVERSE_ALPHABETICAL
      ]}
      flattenedDict={flattenedDict}
      setRowData={setRowData}
    />
  );

  
  return (
    <DictBaseAssertion
      buttonGroup={buttonGroup}
      columns={columns}
      rows={prepareDictRowData(rowData, props.assertion.line_no)}
    />
  );
}


FixLogAssertion.propTypes = {
  /** Assertion being rendered */
	assertion: PropTypes.object.isRequired,
};
