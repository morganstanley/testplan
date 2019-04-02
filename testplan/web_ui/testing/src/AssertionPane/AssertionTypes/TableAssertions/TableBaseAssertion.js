import React, {Component, Fragment} from 'react';
import PropTypes from 'prop-types';
import {css, StyleSheet} from 'aphrodite';
import {AgGridReact} from 'ag-grid-react';
import 'ag-grid-community/dist/styles/ag-grid.css';
import 'ag-grid-community/dist/styles/ag-theme-balham.css';
import {calculateTableGridHeight} from './tableAssertionUtils';

/**
 * Base assertion that are used to render table-like data.
 */
class TableBaseAssertion extends Component {
  constructor(props) {
    super(props);
    this.onGridReady = this.onGridReady.bind(this);
  }
  /**
   * Resize the columns of the grid if the component updated.
   * @public
   */
  componentDidUpdate() {
    this.sizeToFit();
  }

  /**
   * Handler for the grid's onGridReady event. The grid's api is loaded and the 
   * columns are resized.
   * @param params
   * @public
   */
  onGridReady(params) {
    this.gridApi = params.api;
    this.gridColumnApi = params.columnApi;
    this.sizeToFit();
  }

  /**
   * Resize every column to take up all the available space but do not exceed 
   * the width of the grid.
   * @public
   */
  sizeToFit() {
    if (this.gridApi !== undefined) this.gridApi.sizeColumnsToFit();
  }

  render() {
    const height = calculateTableGridHeight(this.props.rowData.length);

    return (
      <Fragment>
        <div className={css(styles.preText)}>
          {this.props.preText}
        </div>
        <div className={
          `ag-theme-balham ${css(styles.isResizable)} ${css(styles.gridFont)}`
          } 
          style={{height: `${height}px`}}>
          <AgGridReact
            suppressColumnVirtualisation={true}
            animateRows={true}
            enableSorting={true}
            enableFilter={true}
            enableColResize={true}
            onGridReady={this.onGridReady}
            columnDefs={this.props.columnDefs}
            rowData={this.props.rowData}
          />
        </div>
      </Fragment>
    );
  }
}

TableBaseAssertion.propTypes = {
  preText: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object,
  ]),
  columnDefs: PropTypes.array,
  rowData: PropTypes.array
};

const styles = StyleSheet.create({
  gridFont: {
    fontSize: '13px',
    fontFamily: 'monospace',
  },

  contentSpan: {
    lineHeight: '110%',
  },

  isResizable: {
    overflow: 'hidden',
    resize: 'vertical',
    paddingBottom: '1rem',
    minHeight: '100px',
  },

  preText: {
    paddingBottom: '.5rem',
  },
});


export default TableBaseAssertion;