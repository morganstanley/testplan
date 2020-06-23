import React from 'react';
import PropTypes from 'prop-types';
import {css, StyleSheet} from 'aphrodite';
import MaterialTable from 'material-table';


/**
 * Base assertion that are used to render dict-like data.
 * It renders the cells with the following content:
 *
 * {Buttons}
 * {Table}
 *
 */
export default function DictBaseAssertion(props) {
  return (
    <>
      {props.buttons}
      <MaterialTable
        title={""}
        className={css(styles.table)}
        columns={props.columns}
        data={props.rows}
        options={{
          exportButton: false,
          search: false,
          toolbar: false,
          paging: false,
          sorting: false,
          maxBodyHeight: '500px',
          overflowY: 'hidden',
          fixedColumns: {
            left: 1,
            right: 0
          },
          headerStyle: {
            fontSize: 'small',
            backgroundColor: '#f5f7f7',
            padding: '6px 11px 6px 11px',
          }
        }}
      />
    </>
  );
};

DictBaseAssertion.propTypes = {
  /** The group of button will be display on the top of table */
  buttons: PropTypes.object,
  /** The head data of table */
  columns: PropTypes.array.isRequired,
  /** The row data of table */
  rows: PropTypes.array.isRequired,
};


const styles = StyleSheet.create({
  table: {
    border: '1px solid',
    borderColor: '#d9dcde',
    borderCollapse: 'collapse',
  }
});
