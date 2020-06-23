import React, {Fragment} from 'react';
import PropTypes from 'prop-types';
import {css, StyleSheet} from 'aphrodite';
import SaveAlt from '@material-ui/icons/SaveAlt';
import Search from '@material-ui/icons/Search';
import Close from '@material-ui/icons/Close';
import MaterialTable from 'material-table';
// import CopyButton from './../CopyButton';
// import {calculateTableGridHeight, gridToDOM} from './tableAssertionUtils';


/**
 * Base assertion that are used to render table-like data.
 */
export default function TableBaseAssertion(props) {
  return (
    <Fragment>
      <div className={css(styles.preText)}>
          {props.preText}
        </div>
      <MaterialTable
        title={""}
        className={css(styles.table)}
        columns={props.columns}
        data={props.rows}
        options={{
          exportButton: true,
          search: true,
          searchFieldAlignment: 'left',
          toolbar: true,
          paging: false,
          fixedColumns: {
            left: 1,
            right: 0
          },
          headerStyle: {
            fontSize: 'small',
            backgroundColor: '#f5f7f7',
            padding: '6px 11px 6px 11px',
          },
          rowStyle: {
            '&:hover': {
              backgroundColor: '#EEE',
            }
          }
        }}
        icons={{
          Export: () => <SaveAlt />,
          Search: () => <Search />,
          ResetSearch: () => <Close />,
        }}
      />
    </Fragment>
  );
}


TableBaseAssertion.propTypes = {
  preText: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object,
  ]),
  columns: PropTypes.array,
  rows: PropTypes.array
};


const styles = StyleSheet.create({
  preText: {
    paddingBottom: '.5rem',
  },
  table: {
    border: '1px solid',
    borderColor: '#d9dcde',
    borderCollapse: 'collapse',
  },
});
