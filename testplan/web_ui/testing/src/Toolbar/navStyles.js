/**
 * Styles for the toolbar component.
 */
import {StyleSheet} from 'aphrodite';

import {
  GREEN, RED, ORANGE, BLACK, DARK_GREY,
} from "../Common/defaults";


const styles = StyleSheet.create({
  toolbar: {
    padding: '0',
  },

  filterBox: {
    float: 'left',
    height: '100%',
  },
  buttonsBar: {
    float: 'left',
    height: '100%',
    color: 'white',
  },
  filterLabel: {
    width: '100%',
    display: 'inlinde-block',
    cursor: 'pointer',
    padding: '0.2em',
    'margin-left': '2em',
  },
  dropdownItem: {
    padding: '0',
    ':focus': {
      outline: '0',
    },
  },
  toolbarButton: {
    textDecoration: 'none',
    position: 'relative',
    display: 'inline-block',
    height: '2.4em',
    width: '2.4em',
    cursor: 'pointer',
    color: 'white',
    padding: '0.7em 0em 0.7em 0em',
    transition: 'all 0.3s ease-out 0s',
    ':hover': {
        color: DARK_GREY
    }
  },
  toolbarInactive: {
    cursor: 'auto',
  },
  toolbarUnstable: {
    backgroundColor: ORANGE,
    color: 'white'
  },
  toolbarUnknown: {
    backgroundColor: BLACK,
    color: 'white'
  },
  toolbarPassed: {
    backgroundColor: GREEN,
    color: 'white'
  },
  toolbarFailed: {
    backgroundColor: RED,
    color: 'white'
  },
  filterDropdown: {
    'margin-top': '-0.3em'
  },
  infoTable: {
    'table-layout': 'fixed',
    width: '100%'
  },
  infoTableKey: {
    width: '25%',
  },
  infoTableValue: {
    'word-wrap': 'break-word',
    'overflow-wrap': 'break-word',
  }
});

export default styles;
