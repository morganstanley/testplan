import React from 'react';
import PropTypes from 'prop-types';
import {Badge} from 'reactstrap';
import {StyleSheet, css} from "aphrodite";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {faPlay, faRedo} from '@fortawesome/free-solid-svg-icons';
import {BarLoader} from 'react-spinners';

import {
  RED,
  GREEN,
  LIGHT_GREY,
  CATEGORY_ICONS,
  ENTRY_TYPES,
  STATUS
} from "../Common/defaults";

/**
 * Display NavEntry information:
 *   * name.
 *   * case count (passed/failed).
 *   * type (displayed in badge).
 */
const InteractiveNavEntry = (props) => {
  const badgeStyle = `${props.status}Badge`;
  const interactiveIcon = getInteractiveIcon(
    props.status, props.handlePlayClick);

  return (
    <div className='d-flex justify-content-between'>
      <div className={css(styles.entryName, styles[props.status])}>
        {props.name}
      </div>
      <div className={css(styles.entryIcons)}>
        <i className={css(styles.entryIcon)} title='passed/failed testcases'>
          <span className={css(styles.passed)}>{props.caseCountPassed}</span>
          /
          <span className={css(styles.failed)}>{props.caseCountFailed}</span>
        </i>
        <Badge
          className={css(styles.entryIcon, styles[badgeStyle])}
          title={props.type}
          pill
        >
          {CATEGORY_ICONS[props.type]}
        </Badge>
        {interactiveIcon}
      </div>
    </div>
  );
};

/**
 * Returns the appropriate component to display for an interactive entry.
 *
 * * When the entry is ready to run, render a play button.
 *
 * * When the entry is being run, render a "loading" bar. The bar has no
 *   relation to actual test progress, it's just a visual indicator that
 *   something is being run.
 *
 * * When the entry has been run, render a replay button.
 */
const getInteractiveIcon = (entryStatus, handlePlayClick) => {
  switch (entryStatus) {
    case 'ready':
      return (
        <FontAwesomeIcon
          className={css(styles.entryButton)}
          icon={faPlay}
          title='Run tests'
          onClick={handlePlayClick}
        />
      );

    case 'running':
      return (
        <BarLoader
          color={'#123abc'}
          loading={true}
          size={4}
        />
      );

    case 'passed':
    case 'failed':
      return (
        <FontAwesomeIcon
          className={css(styles.entryButton)}
          icon={faRedo}
          title='Run tests'
          onClick={handlePlayClick}
        />
      );

    default:
      throw new Error("Unexpected status: " + entryStatus);
  }
};

InteractiveNavEntry.propTypes = {
  /** Entry name */
  name: PropTypes.string,
  /** Entry status */
  status: PropTypes.oneOf(STATUS),
  /** Entry type */
  type: PropTypes.oneOf(ENTRY_TYPES),
  /** Number of passing testcases entry has */
  caseCountPassed: PropTypes.number,
  /** Number of failing testcases entry has */
  caseCountFailed: PropTypes.number,
};

const styles = StyleSheet.create({
  entryName: {
    overflow: 'hidden',
    fontSize: '1em',
    fontWeight: 500,
  },
  entryIcons: {
    paddingLeft: '1em',
  },
  entryIcon: {
    fontSize: '0.6em',
    margin: '0em 0.5em 0em 0.5em',
  },
  entryButton: {
    textDecoration: 'none',
    position: 'relative',
    display: 'inline-block',
    height: '2.4em',
    width: '2.4em',
    cursor: 'pointer',
    color: 'black',
    padding: '0.7em 0em 0.7em 0em',
    transition: 'all 0.3s ease-out 0s',
    ':hover': {
        color: LIGHT_GREY
    }
  },
  passedBadge: {
    backgroundColor: GREEN,
    opacity: 0.5,
  },
  failedBadge: {
    backgroundColor: RED,
    opacity: 0.5,
  },
  passed: {
    color: GREEN,
  },
  failed: {
    color: RED,
  },
});

export default InteractiveNavEntry;
