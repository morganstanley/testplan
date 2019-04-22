import {any, sorted, domToString} from './../../../Common/utils';
import {DICT_GRID_STYLE} from './../../../Common/defaults';

/** @module dictAssertionUtils */

/**
 * Helper function used to sort the data of DictMatch and FixMatch assertions.
 * The output of these assertions is a flattened JSON where the rows are in the
 * following format:
 *
 *    [level, key, status, expected, value]
 *
 * The sorting happens recursively by slicing at rows with the current depth
 * level.
 *
 * @param {Array} origFlattenedJSON
 * @param {number} depth - depth level of the nested structure
 * @param {boolean} reverse - if true, the sorted list is reversed
 * @param {boolean} orderByStatus - if true, the list will be ordered by status,
 * alphabetical by keys otherwise
 * @returns {Array}
 * @private
 */
function sortFlattenedJSON(
  origFlattenedJSON, 
  depth = 0, 
  reverse = false, 
  orderByStatus = true
) {
  // deep copy the original list
  origFlattenedJSON = origFlattenedJSON.slice();

  let sortedFlattenedJSONList = [];
  let startingIndexes = [];
  let startingAndEndingIndexes = [];

  // return early if there is only 1 item
  if (origFlattenedJSON.length === 1) return origFlattenedJSON;

  // when slicing on anything but the 0th level, 
  // the first item of the list is the key of that object (slice),
  // so it is removed and added to the sorted list
  if (depth !== 0) {
    sortedFlattenedJSONList.push(origFlattenedJSON.shift());

    // if only 1 item remains after removing the key, 
    // add it do the sorted list and return it
    if (origFlattenedJSON.length === 1) {
      sortedFlattenedJSONList.push(...origFlattenedJSON);
      return sortedFlattenedJSONList;
    }
  }

  const set = new Set(origFlattenedJSON.map(line => line[0]));
  const allItemsAreSameLevel = set.size === 1;

  // if all remaining items of the list are on the same depth level, 
  // they can be sorted and returned
  if (allItemsAreSameLevel) {
    sortedFlattenedJSONList.push(
      ...sorted(
        origFlattenedJSON, 
        (item) => orderByStatus ? item[2] : item[1],
        reverse
      )
    );

    return sortedFlattenedJSONList;
  } else {
    // create a new object that contains the indexes of the rows
    startingIndexes = origFlattenedJSON.map(
      (line, index) => ({ startingKey: index, data: line })
    );

    // if there is an item that has a depth value less than the current one, 
    // it is because the examined slice is a list
    const isList = any(origFlattenedJSON.map(line => line[0] < depth));

    if (isList) {
      // the lines with less depth value than the current one are list item 
      // separators, so only their indexes matter depth is not increased so at 
      // the next recursion everything can go back to normal
      startingIndexes = startingIndexes.filter(
        line => line.data[0] === depth - 1
      );
      depth += 0;
    } else {
      // if the current slice is not a list, then we omit the indexes of the 
      // lines that have no key
      startingIndexes = startingIndexes.filter(
        line => line.data[0] === depth && line.data[1] !== ''
      );
      depth += 1;
    }

    // calculate the ending indexes by the already calculated starting indexes,
    // these will be used to do the slicing
    startingIndexes.forEach((line, index) => {
      if (index !== startingIndexes.length - 1) {
        startingAndEndingIndexes.push({
          startingKey: line.startingKey,
          endingKey: startingIndexes[index + 1].startingKey,
          data: line.data
        });
      } else {
        startingAndEndingIndexes.push({
          startingKey: startingIndexes[index].startingKey,
          endingKey: origFlattenedJSON.length,
          data: startingIndexes[index].data
        });
      }
    });

    // sort the list
    startingAndEndingIndexes = sorted(
      startingAndEndingIndexes, 
      item => orderByStatus ? item.data[2] : item.data[1], reverse
    );

    // start recursion on the sorted slices of the list
    startingAndEndingIndexes.map(key => sortedFlattenedJSONList.push(
      ...sortFlattenedJSON(
        origFlattenedJSON.slice(key.startingKey, key.endingKey),
        depth,
        reverse,
        orderByStatus
      )
    ));

    return sortedFlattenedJSONList;
  }
}

/**
 * Prepare the column definitions for DictMatch, DictLog, FixMatch, FixLog 
 * assertions. DictMatch and FixMatch should include expect column.
 *
 * @param {string|object|function} cellStyle - A string, object or function that
 * will define the styling of the cells.
 * @param {class} cellRenderer - Custom component used by the grid to render the
 * cells.
 * @param {boolean} hasExpected - If true, the list will include expect column.
 * @returns {{headerName: string, field: string, hide: boolean}}
 * @private
 */
function prepareDictColumnDefs(cellStyle, cellRenderer, hasExpected) {
  const columnDefs = [{
    headerName: 'Descriptor',
    field: 'descriptor',
    hide: true,
  }];

  const keyColumn = {
    headerName: 'Key',
    field: 'key',
    suppressMovable: true,
    pinned: 'left',
    cellStyle: cellStyle,
    cellRendererFramework: cellRenderer,
  };
  columnDefs.push(keyColumn);

  if (hasExpected) {
    const expectedColumn = {
      headerName: 'Expected',
      field: 'expected',
      cellStyle: cellStyle,
      cellRendererFramework: cellRenderer,
    };
    columnDefs.push(expectedColumn);
  }

  const valueColumn = {
    headerName: 'Value',
    field: 'value',
    cellStyle: cellStyle,
    cellRendererFramework: cellRenderer,
  };
  columnDefs.push(valueColumn);

  return columnDefs;
}

/**
 * Prepare the rows for Dict/FixMatch assertions.
 *
 * @param {object} data - Result of the assertion as a flattened dictionary
 * @param {number} lineNo - lineNo property of the assertion used to identify
 * the assertion on the rendered page. This is not what lineNo was intened to be
 * used for. It would be better to use some UUID to indentify each Assertion.
 * @returns {Array}
 * @private
 */
function prepareDictRowData(data, lineNo) {
  return data.map((line, index, originalArray) => {
    let level, key, status, expectedValue, actualValue;
    const isLog = line.length === 3;

    if (isLog) {
      [level, key, actualValue] = line;
    } else {
      [level, key, status, actualValue, expectedValue] = line;
    }

    const isEmptyLine = key.length === 0 && actualValue.length === 0;
    const hasAcutalValue = Array.isArray(actualValue);
    const hasExpectedValue = Array.isArray(expectedValue);

    let lineObject = {
      descriptor: {
        lineNo: lineNo,
        indent: level,
        isListKey:
          originalArray[index + 1] && originalArray[index + 1][1] === '',
        isEmptyLine: isEmptyLine,
        status: status
      }
    };

    if (isEmptyLine) {
      // Empty lines are used to display breaks between list entries more
      // clearly.
      lineObject.key = { value: null, type: null };
    } else {
      lineObject.key = { value: key, type: 'key' };
      if (hasAcutalValue) {
        lineObject.value = { value: actualValue[1], type: actualValue[0] };
      }
      if (hasExpectedValue) {
        lineObject.expected = {
          value: expectedValue[1],
          type: expectedValue[0]
        };
      }
    }

    return lineObject;
  });
}

/**
 * Function to add styling to cells with conditions based on their values.
 *
 * @param {Object} params
 * @returns {object} css style object
 * @private
 */
function dictCellStyle(params) {
  const isValue = params.colDef.field !== 'key';
  const isFailed = params.data.descriptor.status === 'Failed';
  let cellStyle = {};

  if (isFailed) {
    cellStyle.color = 'red';
    cellStyle.fontWeight = 'bold';
  }

  if (isValue) {
    cellStyle.backgroundColor = '#BDC3C750';
  }

  return cellStyle;
}

/**
 * Calculate the height of the grid. If the grid has less than
 * maximumNumberOfRowsVisible, then the grid will display every row of data
 * available. If it has more than that value then maximumNumberOfRowsVisible
 * number of rows will be displayed and the table will be scrollable.
 *
 * @param {number} numberOfRows
 * @param {number} numberOfEmptyRows - Number of rows that contain no data and
 * are only used to seperate list items
 * @param {number} maximumNumberOfRowsVisible - Maximum number of rows to be
 * displayed
 * @returns {number}
 * @private
 */
function calculateDictGridHeight(
  numberOfRows, 
  numberOfEmptyRows, 
  maximumNumberOfRowsVisible = DICT_GRID_STYLE.MAX_VISIBLE_ROW
) {

  return numberOfRows <= maximumNumberOfRowsVisible
    ? numberOfRows * DICT_GRID_STYLE.ROW_HEIGHT + numberOfEmptyRows * 
      DICT_GRID_STYLE.EMPTY_ROW_HEIGHT + DICT_GRID_STYLE.HEADER_HEIGHT + 
      DICT_GRID_STYLE.BOTTOM_PADDING
    : maximumNumberOfRowsVisible * DICT_GRID_STYLE.ROW_HEIGHT + 
      DICT_GRID_STYLE.HEADER_HEIGHT + DICT_GRID_STYLE.BOTTOM_PADDING;
}

/**
 * Return the description of the FIX tag in the cell.
 *
 * @param {JSON} fixTagInfo - JSON object where keys are FIX tags and the values
 * are description
 * @param {string} cellValue - Value of the cell.
 * @param {string} keyValue - Value of the cell under the key column for the row
 * the cell is in.
 * @param {string} colField - The column the current cell is in.
 * @returns {{name: null, descr: null, value: null}}
 */
function getFixInformation(fixTagInfo, cellValue, keyValue, colField) {
  let fixInfo = {name: null, descr: null, value: null};

  // If keyValue is null the current row is empty. Empty rows are used to
  // display breaks between list entries more clearly.
  const validKey = (colField === 'key') && (keyValue !== null);
  const validExpected = colField === 'expected';
  const validValue = colField === 'value';

  if (validKey) {
    fixInfo.descr = fixTagInfo[keyValue] !== undefined
      ? fixTagInfo[keyValue].descr
      : 'Missing information';
    fixInfo.name = fixTagInfo[keyValue] !== undefined
      ? fixTagInfo[keyValue].names[0]
      : null;
  } else if (validExpected || validValue) {
    fixInfo.value = fixTagInfo[keyValue] !== undefined
      ? fixTagInfo[keyValue].values[cellValue]
      : null;
  }

  return fixInfo;
}


/**
 * Convert flattened dict assertion data to HTML table string
 *
 * @param {Array} flattenedDict - flattened dict assertion data
 * @returns {string} - HTML table
 */
function flattenedDictToDOM(flattenedDict) {
  let table = document.createElement('table');

  /**
   * Convert DictLog/FixLog assertion data to HTML Table
   *
   * <table>
   *   <tr>
   *     <th>Key</th><th>Value</th>
   *   </tr>
   *   <tr>
   *     <td>  alpha</td>
   *     <td>blue<small>str</small></td>
   *   </tr>
   *   ...
   * </table>
   *
   *  _________________________
   * | Key        | Value      |
   * |------------|------------|
   * | foo        |            |
   * |   alpha    | blue       |
   * |   beta     | green      |
   * | bar        | true       |
   * |____________|____________|
   *
   */
  function logToDOM(flattenedDict, table) {
    let header = document.createElement('tr');
    ['Key', 'Value'].forEach((el) => {
      let th = document.createElement('th');
      th.innerHTML = el;
      header.appendChild(th);
    });
    table.appendChild(header);

    flattenedDict.forEach((el) => {
      let [level, key, value] = el;
      // If key and value are string and length is 0, the current row is empty.
      // Empty row will be ignored.
      if (key.length === 0 && value.length === 0) {
        return;
      }
      let tr = document.createElement('tr');
      let keyTd = document.createElement('td');
      let valueTd = document.createElement('td');
      keyTd.innerText = '\u00A0\u00A0'.repeat(level) + key;
      if (Array.isArray(value)) {
        valueTd.innerText = value[1];
        let valueType = document.createElement('small');
        valueType.innerText = value[0];
        valueTd.appendChild(valueType);
      } else {
        valueTd.innerText = value;
      }

      tr.appendChild(keyTd);
      tr.appendChild(valueTd);
      table.appendChild(tr);
    });
  }

  /**
   * Convert DictMatch/FixMatch assertion data to HTML Table
   *
   * <table>
   *   <tr>
   *     <th>Key</th><th>Expected</th><th>Value</th>
   *   </tr>
   *   <tr>
   *     <td>  alpha</td>
   *     <td>blue<small>str</small></td>
   *     <td>red<small>str</small></td>
   *   </tr>
   *   ...
   * </table>
   *  _____________________________________
   * | Key       | Expected   | Value      |
   * |-----------|------------|------------|
   * | foo       |            |            |
   * |   alpha   | blue       | red        |
   * |   beta    | green      | green      |
   * | bar       | true       | true       |
   * |___________|____________|____________|
   *
   */
  function matchToDOM(flattenedDict, table) {
    let header = document.createElement('tr');
    ['Key', 'Expected', 'Value'].forEach((el) => {
      let th = document.createElement('th');
      th.innerHTML = el;
      header.appendChild(th);
    });
    table.appendChild(header);

    flattenedDict.forEach((el) => {
      let [level, key, status, actualValue, expectedValue] = el;
      // If key and value are string and length is 0, the current row is empty.
      // Empty row will be ignored.
      if (key.length === 0 && actualValue.length === 0) {
        return;
      }
      let tr = document.createElement('tr');
      let keyTd = document.createElement('td');
      let valueTd = document.createElement('td');
      let expectedTd = document.createElement('td');
      keyTd.innerText = '\u00A0\u00A0'.repeat(level) + key;

      if (Array.isArray(actualValue)) {
        valueTd.innerText = actualValue[1];
        let valueType = document.createElement('small');
        valueType.innerText = actualValue[0];
        valueTd.appendChild(valueType);
      } else {
        valueTd.innerText = actualValue;
      }

      if (Array.isArray(expectedValue)) {
        expectedTd.innerText = expectedValue[1];
        let valueType = document.createElement('small');
        valueType.innerText = expectedValue[0];
        expectedTd.appendChild(valueType);
      } else {
        expectedTd.innerText = expectedValue;
      }

      tr.appendChild(keyTd);
      tr.appendChild(expectedTd);
      tr.appendChild(valueTd);
      if (status === 'Failed') {
        tr.style.color = 'red';
      }
      table.appendChild(tr);
    });
  }

  if (flattenedDict) {
    const isLog = flattenedDict[0].length === 3;
    if (isLog) {
      logToDOM(flattenedDict, table);
    } else {
      matchToDOM(flattenedDict, table);
    }
  }

  return domToString(table);
}


export {
  sortFlattenedJSON,
  prepareDictColumnDefs,
  prepareDictRowData,
  dictCellStyle,
  calculateDictGridHeight,
  getFixInformation,
  flattenedDictToDOM,
};
