import React, {Component} from 'react';
import PropTypes from 'prop-types';
import { StyleSheet, css } from 'aphrodite';
import { library } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faPrint,
  faInfoCircle,
  faQuestionCircle,
  faFilter,
  faTags,
  faCircle,
  faMale,
  faTable,
  faChartBar
} from '@fortawesome/free-solid-svg-icons';

import FilterBox from "../Toolbar/FilterBox";
import {GREEN, RED, LIGHT_GREY, DARK_GREY, STATUS} from "../Common/defaults";

library.add(
  faPrint,
  faInfoCircle,
  faQuestionCircle,
  faFilter,
  faTags,
  faCircle,
  faMale,
  faTable,
  faChartBar
);

/**
 * Toolbar component, contains the toolbar buttons & Filter box.
 */
class Toolbar extends Component {
  render() {
    const toolbarStyle = this.props.status === 'passed' ?
      css(styles.toolbar, styles.toolbarPassed) :
      this.props.status === 'failed' ?
        css(styles.toolbar, styles.toolbarFailed) :
        css(styles.toolbar, styles.toolbarNeutral);

    const navButtons = this.props.buttons.map((button) =>
      <FontAwesomeIcon
        className="nav-side-button"
        key={button.type}
        icon={button.type}
        fixedWidth
      />
    );

    return (
      <div className={toolbarStyle}>
        <FilterBox handleNavFilter={this.props.handleNavFilter}/>
        <div>{navButtons}</div>
      </div>
    );
  }
}

Toolbar.propTypes = {
  /** Testplan report's status */
  status: PropTypes.oneOf(STATUS),
  /** Buttons to be displayed on the Toolbar */
  buttons: PropTypes.arrayOf(PropTypes.object),
  /** Function to handle expressions entered into the Filter box */
  handleNavFilter: PropTypes.func,
};

const styles = StyleSheet.create({
  toolbar: {
    height: '2.5em',
    width: '100%',
    position: 'fixed',
    display: 'inline-block',
    zIndex: 400,
    top: '0em',
    bottom: '0em',
    left: '0em',
    fontWeight: 'bold',
    textAlign: 'center',
    border: 'none',
  },

  toolbarButton: {
    textDecoration: 'none',
    position: 'relative',
    display: 'inline-block',
    padding: '0.3em 0em 0.3em 0em',
    ':hover:': {
        color: DARK_GREY
      }
    },
  toolbarNeutral: {
    backgroundColor: LIGHT_GREY,
    color: 'black'
  },
  toolbarPassed: {
    backgroundColor: GREEN,
    color: 'white'
  },
  toolbarFailed: {
    backgroundColor: RED,
    color: 'white'
  }
});

export default Toolbar;
