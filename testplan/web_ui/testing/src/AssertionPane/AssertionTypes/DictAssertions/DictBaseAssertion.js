import React, { useState, useLayoutEffect } from "react";
import PropTypes from "prop-types";
import { css, StyleSheet } from "aphrodite";
import "ag-grid-community/dist/styles/ag-grid.css";
import "ag-grid-community/dist/styles/ag-theme-balham.css";
import { AgGridReact } from "ag-grid-react";
import "ag-grid-enterprise";
import { LicenseManager } from "ag-grid-enterprise";

const REACT_APP_AG_GRID_LICENSE = process.env.REACT_APP_AG_GRID_LICENSE;
if (REACT_APP_AG_GRID_LICENSE) {
  LicenseManager.setLicenseKey(REACT_APP_AG_GRID_LICENSE);
}

const exportCallback = (cell) => {
  if (cell.value) {
    return cell.value.value;
  }
  return "";
};

/**
 * Base assertion that are used to render dict-like data.
 * It renders the cells with the following content:
 *
 * {Buttons}
 * {Table}
 *
 */
export default function DictBaseAssertion(props) {
  const [gridApi, setGridApi] = useState(null);
  const [, setGridColumnApi] = useState(null);

  const sizeToFit = (api) => {
    if (api) api.sizeColumnsToFit();
  };

  const onGridReady = (params) => {
    setGridApi(params.api);
    setGridColumnApi(params.columnApi);
    sizeToFit(params.api);
  };

  useLayoutEffect(() => {
    sizeToFit(gridApi?.api);
  });

  // table header + margin + column height * columns
  let height =
    35 + 16 + (props.rows.length > 10 ? 280 : props.rows.length * 28);

  return (
    <>
      {props.buttons}
      <div
        className={`ag-theme-balham ${css(styles.grid)}`}
        style={{ height: `${height}px`, width: "99.9%" }}
      >
        <AgGridReact
          onGridReady={onGridReady}
          suppressColumnVirtualisation={true}
          suppressExcelExport={false}
          columnDefs={props.columns}
          rowData={props.rows}
          defaultColDef={{
            sortable: false,
            filter: true,
            resizable: true,
            enableRowGroup: true,
            enablePivot: true,
          }}
          groupMultiAutoColumn={true}
          enableRangeSelection={true}
          getRowHeight={(params) =>
            params.data.descriptor.isEmptyLine ? 5 : 28
          }
          processCellForClipboard={exportCallback}
          getContextMenuItems={(params) => {
            return [
              "copy",
              "copyWithHeaders",
              {
                name: "CSV Export",
                action: () => {
                  params.api.exportDataAsCsv({
                    processCellCallback: exportCallback,
                  });
                },
              },
            ];
          }}
        />
      </div>
    </>
  );
}

DictBaseAssertion.propTypes = {
  /** The group of button will be display on the top of table */
  buttons: PropTypes.object,
  /** The head data of table */
  columns: PropTypes.array.isRequired,
  /** The row data of table */
  rows: PropTypes.array.isRequired,
};

const styles = StyleSheet.create({
  grid: {
    overflow: "hidden",
    resize: "vertical",
    paddingBottom: "1rem",
    minHeight: "163px",
  },
});
