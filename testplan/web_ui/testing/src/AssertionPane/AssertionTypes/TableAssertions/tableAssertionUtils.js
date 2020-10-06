/** @module tableAssertionUtils */

import {domToString} from './../../../Common/utils';

const _TP_BLANK_CELL = '_TP_BLANK_CELL';

/**
 * Function to prepare the column definitions for TableLog assertions.
 *
 * @param {Array} columns
 * @returns {object} 
 *  {
 *    title: string, 
 *    field: string, 
 *    cellStyle: object, 
 *    headerStyle: object, 
 *  }
 * @private
 */

const cellStyle = {
  fontSize: 'small',
  border: '1px solid',
  borderColor: '#d9dcde',
  padding: '6px 11px 6px 11px'
};

const headerStyle = {
  border: '1px solid',
  borderColor: '#d9dcde',
};

export function prepareTableColumn(columns) {
  let columnDefs = [{
    title: 'ID',
    field: 'id',
    cellStyle: {
      width: '72px',
      ...cellStyle
    },
    headerStyle: {
      width: '72px',
      ...headerStyle
    }
  }];

  columns.forEach(column => {
    columnDefs.push({
      title: column,
      field: column,
      cellStyle: cellStyle,
      headerStyle: headerStyle
    });
  });
  return columnDefs;
}

/**
 * Prepare the row data of TableLog assertions.
 *
 * @param {Array} indexes - indexes of the rows
 * @param {Array} table - the table itself as an array of objects where the keys
 *  are the column titles
 * @param {Array} columns - column titles
 * @returns {Array}
 * @private
 */
export function prepareTableLogRowData(indexes, table, columns) {
  let rowData = [];

  indexes.forEach(index => {
    let row = columns.reduce((accumulator, column) => {
      const cellVal = table[index][column];
      accumulator[column] = cellVal === _TP_BLANK_CELL ? '' : cellVal;
      return accumulator;
    }, {});

    row['id'] = index;

    rowData.push(row);
  });

  return rowData;
}

/**
 * Prepare the column definitions for TableMatch assertion.
 *
 * @param {Array} columns
 * @returns {Array}
 * @private
 */
export function prepareTableMatchColumn(columns) {
  let columnDefs = [{
    title: 'ID',
    field: 'id',
    cellStyle: {
      width: '72px',
      ...cellStyle
    },
    headerStyle: {
      width: '72px',
      ...headerStyle
    }
  }, {
    title: 'Expected/Value',
    field: 'ev',
    cellStyle: {
      width: '121px',
      ...cellStyle
    },
    headerStyle: {
      width: '121px',
      ...headerStyle
    }
  }];

  columns.forEach(column => {
    columnDefs.push({
      title: column,
      field: column,
      cellStyle: (value, rowData) => {
        if (rowData.passed[column]) {
          return cellStyle;
        } else {
          return {
            color: 'red',
            fontWidth: 'bold',
            ...cellStyle
          };
        }
      },
      headerStyle: headerStyle
    });
  });

  return columnDefs;
}

/**
 * Prepare the row data of TableMatch assertion.
 *
 * @param {Array} data - the table itself as an array of objects where the keys
 * are the column titles
 * @param {Array} columns - column titles
 * @returns {Array}
 * @private
 */
export function prepareTableRowData(data, columns) {
  let rowData = [];

  data.forEach(line => {
    const [
      index,
      data,
      diff,
      errors,
      extra,
    ] = line;

    let passed = {};

    let expectedRow = columns.reduce((accumulator, column, index) => {
      if (diff[column]) {
        accumulator[column] = diff[column];
        passed[column] = false;
      } else if (errors[column]) {
        accumulator[column] = errors[column];
        passed[column] = false;
      } else if (extra[column]) {
        accumulator[column] = extra[column];
        passed[column] = true;
      } else {
        accumulator[column] = data[index];
        passed[column] = true;
      }

      return accumulator;
    }, {});

    expectedRow['id'] = index;
    expectedRow['ev'] = 'Expected';
    expectedRow['passed'] = passed;

    rowData.push(expectedRow);

    let valueRow = columns.reduce((accumulator, column, index) => {
      accumulator[column] = data[index];

      return accumulator;
    }, {});

    valueRow['id'] = index;
    valueRow['ev'] = 'Value';
    valueRow['passed'] = passed;

    rowData.push(valueRow);
  });

  return rowData;
}

/**
 * Prepare the column definitions for ColumnContain assertion.
 *
 * @param {string} column - name of the column
 * @returns {Array}
 * @private
 */
export function prepareTableColumnContainColumn(column) {
  return [
    {
      title: 'ID',
      field: 'id',
      cellStyle: (value, rowData) => {
        let style = {width: '72px', ...cellStyle};
        if (rowData.passed) {
          return style;
        } else {
          return {
            color: 'red',
            fontWidth: 'bold',
            ...style
          };
        }
      },
      headerStyle: {
        width: '72px',
        ...headerStyle,
      }
    },
    {
      title: column,
      field: 'value',
      cellStyle: (value, rowData) => {
        if (rowData.passed) {
          return cellStyle;
        } else {
          return {
            color: 'red',
            fontWidth: 'bold',
            ...cellStyle
          };
        }
      },
      headerStyle: headerStyle
    },
  ];
}

/**
 * Prepare the row data of ColumnContain assertion.
 *
 * @param {Array} data
 * @param {Array} values
 * @returns {Array}
 * @private
 */
export function prepareTableColumnContainRowData(data, values) {
  return data.map(line => {
    const [
      index,
      value,
      passed,
    ] = line;

    return {
      id: index,
      expected: values,
      value: value,
      passed: passed,
    };
  });
}

/**
 * Prepare the text display before the table for ColumnContain assertions.
 * The text is the values that are checked against the table.
 *
 * @param values
 * @returns {Array}
 * @private
 */
export function prepareTableColumnContainPreText(values) {
  return values.map(value => JSON.stringify(value))
    .reduce((prev, curr) => [prev, ', ', curr]);
}

/**
 * Calculate the height of the grid. If the grid has less than
 * maximumNumberOfRowsVisible, then the grid will display every row of data
 * available. If it has more than that value then maximumNumberOfRowsVisible
 * number of rows will be displayed and the table will be scrollable.
 *
 * @param {number} numberOfRows
 * @param {number} maximumNumberOfRowsVisible - Maximum number of rows to be
 * displayed
 * @returns {number}
 * @private
 */
export function calculateTableGridHeight(
  numberOfRows, 
  maximumNumberOfRowsVisible = 20
) {
  const rowHeight = 28;
  const headerHeight = 32;
  const bottomPaddingOnGrid = 16 + 2;

  return numberOfRows <= maximumNumberOfRowsVisible
    ? numberOfRows * rowHeight + headerHeight + bottomPaddingOnGrid
    : maximumNumberOfRowsVisible * rowHeight + headerHeight + 
        bottomPaddingOnGrid;
}


/**
 * Convert Ag-Grid columntDefs and row Data to HTML table DOM object
 *
 * @param {Array} columnDefs - Ag-Grid header
 * @param {Array} rowData - Ag-Grid data
 * @returns {string} - HTML Table
 */
export function gridToDOM(columnDefs, rowData) {
  let headerKey = [];
  let table = document.createElement('table');

  let header = document.createElement('tr');
  columnDefs.forEach((el) => {
    if (el.hide) {
      return;
    }
    let th = document.createElement('th');
    th.innerText = el.headerName;
    header.appendChild(th);
    headerKey.push(el.field);
  });
  table.appendChild(header);

  rowData.forEach((el) => {
    let tr = document.createElement('tr');
    headerKey.forEach((key) => {
      let td = document.createElement('td');
      td.innerText = el[key];
      tr.appendChild(td);
    });
    table.appendChild(tr);
  });
  return domToString(table);
}
