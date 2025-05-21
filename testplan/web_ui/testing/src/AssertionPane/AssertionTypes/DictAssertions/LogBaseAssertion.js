import React, { useState } from "react";
import PropTypes from "prop-types";
import DictBaseAssertion from "./DictBaseAssertion";
import DictButtonGroup from "./DictButtonGroup";
import DictCellRenderer from "./DictCellRenderer";
import FixCellRenderer from "./FixCellRenderer";
import {
  prepareDictColumnDefs,
  prepareDictRowData,
  dictCellStyle,
  preprocessDictRows,
} from "./dictAssertionUtils";
import { SORT_TYPES } from "./../../../Common/defaults";

const CELL_RENDERER = Object.freeze({
  fix: FixCellRenderer,
  dict: DictCellRenderer,
});

/**
 * Base assertion used to render dict and fix log assertions.
 */
export default function LogBaseAssertion(props) {
  const flattenedDict = preprocessDictRows(
    props.assertion.flattened_dict,
    false
  );
  const columns = prepareDictColumnDefs(
    dictCellStyle,
    CELL_RENDERER[props.logType]
  );

  const [rowData, setRowData] = useState(flattenedDict);

  const buttonGroup = (
    <DictButtonGroup
      sortTypeList={[
        SORT_TYPES.ALPHABETICAL,
        SORT_TYPES.REVERSE_ALPHABETICAL,
        SORT_TYPES.NONE,
      ]}
      flattenedDict={flattenedDict}
      setRowData={setRowData}
      defaultSortType={SORT_TYPES.NONE}
    />
  );

  return (
    <DictBaseAssertion
      buttons={buttonGroup}
      columns={columns}
      rows={prepareDictRowData(rowData)}
    />
  );
}

LogBaseAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object.isRequired,
  /** Type of the assertion */
  logType: PropTypes.oneOf(["dict", "fix"]).isRequired,
};
