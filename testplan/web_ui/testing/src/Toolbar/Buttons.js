/**
 * Toolbar buttons used for the common report.
 */
import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {css} from 'aphrodite';
import {NavItem} from 'reactstrap';

import {library} from '@fortawesome/fontawesome-svg-core';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {faClock} from '@fortawesome/free-solid-svg-icons';

import styles from './navStyles';
import {getToggledButtonStyle} from './Toolbar';

library.add(faClock);

/**
 * Render a button to toggle the display of execution time on nav entries.
 */
class TimeButton extends Component {
  constructor(props) {
    super(props);
    this.state = {
      displayTime: props.displayTime,
    };

    this.toggleTimeDisplay = this.toggleTimeDisplay.bind(this);
  }

  toggleTimeDisplay() {
    this.props.updateTimeDisplayCbk(!this.state.displayTime);
    this.setState(prevState => ({
      displayTime: !prevState.displayTime
    }));
  }

  render() {
    const toolbarButtonStyle = this.state.displayTime ? (
      getToggledButtonStyle(this.props.status)): css(styles.toolbarButton);
    const iconTooltip = this.state.displayTime ? (
      "Hide time information") : "Display time information";

    return (
      <NavItem>
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key='toolbar-time'
            className={toolbarButtonStyle}
            icon={faClock}
            title={iconTooltip}
            onClick={this.toggleTimeDisplay}
          />
        </div>
      </NavItem>
    );
  }
}

TimeButton.propTypes = {
  /** Function to handle toggle of displaying execution time in the navbar */
  updateTimeDisplayCbk: PropTypes.func,
};

export {
  TimeButton,
};
