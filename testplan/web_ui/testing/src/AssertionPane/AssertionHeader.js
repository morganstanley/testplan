import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {css, StyleSheet} from 'aphrodite';
import {CardHeader, Tooltip} from 'reactstrap';
import {library} from '@fortawesome/fontawesome-svg-core';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {faLayerGroup} from '@fortawesome/free-solid-svg-icons';

library.add(faLayerGroup);

/**
 * Header component of an assertion.
 */
class AssertionHeader extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isUTCTooltipOpen: false,
      isDurationTooltipOpen: false,
    };
    this.toggleUTCTooltip = this.toggleUTCTooltip.bind(this);
    this.toggleDurationTooltip = this.toggleDurationTooltip.bind(this);
  }

  /**
   * Toggle the visibility of tooltip of assertion start time.
   */
  toggleUTCTooltip() {
    this.setState(prevState => ({
      isUTCTooltipOpen: !prevState.isUTCTooltipOpen
    }));
  }

  /**
   * Toggle the visibility of tooltip of duration between assertions.
   */
  toggleDurationTooltip() {
    this.setState(prevState => ({
      isDurationTooltipOpen: !prevState.isDurationTooltipOpen
    }));
  }

  render() {
    const cardHeaderStyle = this.props.assertion.passed === undefined
      ? styles.cardHeaderColorLog
      : this.props.assertion.passed
        ? styles.cardHeaderColorPassed
        : styles.cardHeaderColorFailed;

    const timeInfoArray = this.props.assertion.timeInfoArray || [];
    let component = (this.props.assertion.utc_time === undefined) ? (
      <span className={css(styles.cardHeaderAlignRight)}>
        <FontAwesomeIcon  // Should be a nested assertion group
          size='sm'
          key='faLayerGroup'
          icon='layer-group'
          className={css(styles.icon)}
        />
      </span>
    ) : ((timeInfoArray.length === 0) ? (
        <span className={css(styles.cardHeaderAlignRight)}></span>
      ) : (
        <>
          <span
            className={css(styles.cardHeaderAlignRight)}
            id={`tooltip_duration_${timeInfoArray[0]}`}
          >
            {timeInfoArray[2]}
          </span>
          <span className={css(styles.cardHeaderAlignRight)}>
            &nbsp;&nbsp;
          </span>
          <span
            className={css(styles.cardHeaderAlignRight)}
            id={`tooltip_utc_${timeInfoArray[0]}`}
          >
            {timeInfoArray[1]}
          </span>
          <Tooltip
            placement='bottom'
            isOpen={this.state.isUTCTooltipOpen}
            target={`tooltip_utc_${timeInfoArray[0]}`}
            toggle={this.toggleUTCTooltip}
          >
            {"Assertion start time"}
          </Tooltip>
          <Tooltip
            placement='bottom'
            isOpen={this.state.isDurationTooltipOpen}
            target={`tooltip_duration_${timeInfoArray[0]}`}
            toggle={this.toggleDurationTooltip}
          >
            {"Assertion duration"}
          </Tooltip>
        </>
      )
    );

    return (
      <CardHeader
        className={css(styles.cardHeader, cardHeaderStyle)}
        onClick={this.props.onClick}
      >
        <span>
          <strong>
            {this.props.assertion.description ? (
             this.props.assertion.description + " ") : ""}
          </strong>
        </span>
        <span>
          ({this.props.assertion.type})
        </span>
        {component}
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

  cardHeaderAlignRight: {
    float: 'right',
  },

  collapseDiv: {
    paddingLeft: '1.25rem',
  },

  icon: {
    margin: '0rem .25rem 0rem 0rem',
  }
});

export default AssertionHeader;
