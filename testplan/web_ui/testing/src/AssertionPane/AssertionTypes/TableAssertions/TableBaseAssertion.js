import React, { useState, useLayoutEffect } from "react";
import PropTypes from "prop-types";
import { css, StyleSheet } from "aphrodite";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-balham.css";
import { AgGridReact } from "ag-grid-react";
import "ag-grid-enterprise";
import { LicenseManager } from "ag-grid-enterprise";
import { processCellForClipboard } from "./tableAssertionUtils";

const REACT_APP_AG_GRID_LICENSE = process.env.REACT_APP_AG_GRID_LICENSE;
if (REACT_APP_AG_GRID_LICENSE) {
  LicenseManager.setLicenseKey(REACT_APP_AG_GRID_LICENSE);
}

/**
 * Base assertion that are used to render table-like data.
 */
export default function TableBaseAssertion(props) {
  const [, setGridApi] = useState(null);
  const [gridColumnApi, setGridColumnApi] = useState(null);

  const autoSizeColumns = () => {
    if (gridColumnApi) {
      let allColumnIds = gridColumnApi.getAllColumns().map((c) => c.colId);
      gridColumnApi.autoSizeColumns(allColumnIds);
    }
  };

  const onGridReady = (params) => {
    setGridApi(params.api);
    setGridColumnApi(params.columnApi);
  };

  useLayoutEffect(() => {
    autoSizeColumns();
  });

  // table header + margin + column height * columns
  let height =
    35 + 16 + (props.rows.length > 10 ? 280 : props.rows.length * 28);

  return (
    <>
      <div className={css(styles.preText)}>{props.preText}</div>
      <div
        className={`ag-theme-balham ${css(styles.grid)}`}
        style={{ height: `${height}px`, width: "99.9%" }}
      >
        <AgGridReact
          onGridReady={onGridReady}
          suppressColumnVirtualisation={true}
          columnDefs={props.columns}
          rowData={props.rows}
          onFirstDataRendered={autoSizeColumns}
          defaultColDef={{
            sortable: true,
            filter: true,
            resizable: true,
            enableRowGroup: true,
            enablePivot: true,
          }}
          groupMultiAutoColumn={true}
          enableRangeSelection={true}
          processCellForClipboard={processCellForClipboard}
        />
      </div>
    </>
  );
}

TableBaseAssertion.propTypes = {
  preText: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  columns: PropTypes.array,
  rows: PropTypes.array,
};

const styles = StyleSheet.create({
  preText: {
    paddingBottom: ".5rem",
  },
  grid: {
    overflow: "hidden",
    resize: "vertical",
    paddingBottom: "1rem",
    minHeight: "163px",
  },
});
