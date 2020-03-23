/**
 * Toolbar buttons used for the common report.
 */
import React from 'react';
import PropTypes from 'prop-types';
import {NavItem} from 'reactstrap';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {faClock} from '@fortawesome/free-solid-svg-icons';
import {css} from 'aphrodite';

import styles from './navStyles';

/**
 * Render a button to toggle the display of execution time on nav entries.
 */
const TimeButton = (props) => {
  return (
    <NavItem>
      <div className={css(styles.buttonsBar)}>
        <FontAwesomeIcon
          key='toolbar-time'
          className={css(styles.toolbarButton)}
          icon={faClock}
          title='Toggle execution time'
          onClick={props.toggleTimeDisplayCbk}
        />
      </div>
    </NavItem>
  );
};

TimeButton.propTypes = {
  /** Function to handle toggle of displaying execution time in the navbar */
  toggleTimeDisplayCbk: PropTypes.func,
};

export {TimeButton};
