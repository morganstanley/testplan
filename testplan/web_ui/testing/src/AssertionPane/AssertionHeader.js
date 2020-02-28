import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {css, StyleSheet} from 'aphrodite';
import {CardHeader, Tooltip} from 'reactstrap';
import {library} from '@fortawesome/fontawesome-svg-core';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {
  faClock,
  faLayerGroup,
} from '@fortawesome/free-solid-svg-icons';

library.add(
  faClock,
  faLayerGroup
);

/**
 * Header component of an assertion.
 */
class AssertionHeader extends Component {
  constructor(props) {
    super(props);

    this.state = {isTooltipOpen: false};
    this.toggleTooltip = this.toggleTooltip.bind(this);
  }

  /**
   * Toggle the visibility of the header's tooltip.
   */
  toggleTooltip() {
    this.setState({
      isTooltipOpen: !this.state.isTooltipOpen
    });
  }

  render() {
    let tooltip = null;
    let starterIcon = null;
    const tooltipId = 'tooltip_' + this.props.index;
    const cardHeaderStyle = this.props.assertion.passed === undefined
      ? styles.cardHeaderColorLog
      : this.props.assertion.passed
        ? styles.cardHeaderColorPassed
        : styles.cardHeaderColorFailed;

    if (this.props.assertion.utc_time === undefined) {
      starterIcon =
        <FontAwesomeIcon
          size='sm'
          key='faLayerGroup'
          icon='layer-group'
          className={css(styles.icon)}
        />;
    } else {
      let tooltipDate = new Date(this.props.assertion.utc_time);

      starterIcon =
        <FontAwesomeIcon
          size='sm'
          key='faClock'
          icon='clock'
          className={css(styles.icon)}
          id={tooltipId}
        />;

      tooltip =
        <Tooltip
          placement='bottom'
          isOpen={this.state.isTooltipOpen}
          target={tooltipId}
          toggle={this.toggleTooltip}
        >
          {tooltipDate.toUTCString()}
        </Tooltip>;
    }

    return (
      <CardHeader
        className={css(styles.cardHeader, cardHeaderStyle)}
        onClick={this.props.onClick}
      >
        {starterIcon}
        {tooltip}
        <span>
          <strong>{this.props.assertion.description}</strong>
          ({this.props.assertion.type})
        </span>
        {/*
          TODO will be implemented when complete permalink feature
          linkIcon
        */}
      </CardHeader>
    );
  }
}

AssertionHeader.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
  /** Index of the assertion */
  index: PropTypes.number,
  /** Function when clicking header */
  onClick: PropTypes.func,
};

const styles = StyleSheet.create({
  cardHeader: {
    padding: '.25rem .75rem',
    fontSize: 'small',
    backgroundColor: 'rgba(0,0,0,0)', // Move to defaults?
    cursor: 'pointer',
    borderBottom: '1px solid',
  },

  cardHeaderColorLog: {
    borderBottomColor: '#000000', // Move to defaults?
    color: '#000000', // Move to defaults?
  },

  cardHeaderColorPassed: {
    borderBottomColor: '#28a745', // Move to defaults
    color: '#28a745', // Move to defaults
  },

  cardHeaderColorFailed: {
    borderBottomColor: '#dc3545', // Move to defaults
    color: '#dc3545', // Move to defaults
  },

  collapseDiv: {
    paddingLeft: '1.25rem',
  },

  icon: {
    margin: '0rem .25rem 0rem 0rem',
  }
});

export default AssertionHeader;
