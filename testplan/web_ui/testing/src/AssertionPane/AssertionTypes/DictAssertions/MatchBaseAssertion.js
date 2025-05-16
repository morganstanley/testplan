import React, { useState } from "react";
import PropTypes from "prop-types";
import DictBaseAssertion from "./DictBaseAssertion";
import DictButtonGroup from "./DictButtonGroup";
import DictCellRenderer from "./DictCellRenderer";
import FixCellRenderer from "./FixCellRenderer";
import {
  prepareDictColumnDefs,
  prepareDictRowData,
  sortFlattenedJSON,
  dictCellStyle,
  preprocessDictRows,
} from "./dictAssertionUtils";
import { SORT_TYPES, FILTER_OPTIONS } from "../../../Common/defaults";

const CELL_RENDERER = Object.freeze({
  fix: FixCellRenderer,
  dict: DictCellRenderer,
});

/**
 * Base assertion used to render dict and fix match assertions.
 */
export default function MatchBaseAssertion(props) {
  const flattenedDict = sortFlattenedJSON(
    preprocessDictRows(props.assertion.comparison, true),
    0,
    false,
    true
  );
  const columns = prepareDictColumnDefs(
    dictCellStyle,
    CELL_RENDERER[props.matchType],
    true
  );

  const [rowData, setRowData] = useState(flattenedDict);

  const buttonGroup = (
    <DictButtonGroup
      sortTypeList={[
        SORT_TYPES.ALPHABETICAL,
        SORT_TYPES.REVERSE_ALPHABETICAL,
        SORT_TYPES.BY_STATUS,
      ]}
      filterOptionList={[
        FILTER_OPTIONS.FAILURES_ONLY,
        FILTER_OPTIONS.EXCLUDE_IGNORABLE,
      ]}
      flattenedDict={flattenedDict}
      setRowData={setRowData}
      defaultSortType={SORT_TYPES.BY_STATUS}
      defaultFilterOptions={[]}
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

MatchBaseAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object.isRequired,
  /** Match type */
  matchType: PropTypes.oneOf(["fix", "dict"]).isRequired,
};
