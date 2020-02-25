/**
 * Toolbar buttons used for the interactive report.
 */
import React from 'react';
import {NavItem} from 'reactstrap';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {faBackward} from '@fortawesome/free-solid-svg-icons';
import {css} from 'aphrodite';

import styles from './navStyles';

/**
 * Render a button to trigger the report state to be reset.
 *
 * If the reset action is currently in progress, display a spinning icon
 * instead.
 */
const ResetButton = (props) => {
  if (props.resetting) {
    return (
      <NavItem key="reset-button" >
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key='toolbar-reset'
            className={css(styles.toolbarButton, styles.toolbarInactive)}
            icon={faBackward}
            title='Resetting...'
          />
        </div>
      </NavItem>
    );
  } else {
    return (
      <NavItem key="reset-button" >
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key='toolbar-reset'
            className={css(styles.toolbarButton)}
            icon={faBackward}
            title='Reset state'
            onClick={props.resetStateCbk}
          />
        </div>
      </NavItem>
    );
  }
};

export {ResetButton};
