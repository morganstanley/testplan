import React from 'react';
import PropTypes from 'prop-types';
import {Badge} from 'reactstrap';
import {StyleSheet, css} from "aphrodite";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {
  faPlay,
  faRedo,
  faToggleOff,
  faToggleOn
} from '@fortawesome/free-solid-svg-icons';

import {
  RED,
  GREEN,
  ORANGE,
  BLACK,
  LIGHT_GREY,
  MEDIUM_GREY,
  CATEGORY_ICONS,
  ENTRY_TYPES,
  STATUS,
  STATUS_CATEGORY,
  RUNTIME_STATUS,
  NAV_ENTRY_ACTIONS,
} from "../Common/defaults";

/**
 * Display interactive NavEntry information:
 *   * name.
 *   * case count (passed/failed).
 *   * type (displayed in badge).
 *   * Interactive status icon
 *   * Environment status icon (if required)
 */
const InteractiveNavEntry = (props) => {
  const badgeStyle = `${STATUS_CATEGORY[props.status]}Badge`;
  const statusIcon = getStatusIcon(
    props.runtime_status,
    props.handlePlayClick,
    props.suiteRelated,
    props.action,
  );
  const envStatusIcon = getEnvStatusIcon(
    props.envStatus, props.envCtrlCallback
  );

  return (
    <div
      className='d-flex justify-content-between align-items-center'
      style={{height: "1.5em"}}
    >
      <div
        className={
          css(styles.entryName, styles[STATUS_CATEGORY[props.status]])
        }
        title={props.description || props.name}
      >
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
        {envStatusIcon}
        {statusIcon}
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
 *
 * * Special suite-related "testcase" entries, such as setup and teardown
 *   reports, cannot be directly run and are instead run automatically as
 *   required. So we do not render buttons to control them.
 */
const getStatusIcon = (entryStatus, handlePlayClick, suiteRelated, action) => {
  if (suiteRelated) {
    return null;
  }

  switch (entryStatus) {
    case 'ready':
      return (
        <FontAwesomeIcon
          className={
            action === 'prohibit' ? css(styles.inactiveEntryButton)
            : css(styles.entryButton)
          }
          icon={faPlay}
          title='Run tests'
          onClick={
            action === 'prohibit' ? (e) => {
              e.preventDefault(); e.stopPropagation();
            } : handlePlayClick
          }
        />
      );

    case 'running':
      return (
        <FontAwesomeIcon
          className={css(styles.inactiveEntryButton)}
          icon={faRedo}
          title='Running...'
          spin
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
        />
      );

    case 'finished':
      return (
        <FontAwesomeIcon
          className={
            action === 'prohibit' ? css(styles.inactiveEntryButton)
            : css(styles.entryButton)
          }
          icon={faRedo}
          title='Run tests'
          onClick={
            action === 'prohibit' ? (e) => {
              e.preventDefault(); e.stopPropagation();
            } : handlePlayClick
          }
        />
      );

    default:
      throw new Error("Unexpected status: " + entryStatus);
  }
};

/**
 * Returns the environment control component for entries that own an
 * environment. Returns null for entries that do not have an environment.
 */
const getEnvStatusIcon = (envStatus, envCtrlCallback) => {
  switch (envStatus) {
      case 'STOPPED':
        return (
          <FontAwesomeIcon
            className={css(styles.entryButton)}
            icon={faToggleOff}
            title='Start environment'
            onClick={(e) => envCtrlCallback(e, "start")}
          />
        );

      case 'STARTING':
        return (
          <FontAwesomeIcon
            className={css(styles.inactiveEntryButton)}
            icon={faToggleOff}
            title='Environment starting...'
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
          />
        );

      case 'STARTED':
        return (
          <FontAwesomeIcon
            className={css(styles.entryButton)}
            icon={faToggleOn}
            title='Stop environment'
            onClick={(e) => envCtrlCallback(e, "stop")}
          />
        );

      case 'STOPPING':
        return (
          <FontAwesomeIcon
            className={css(styles.inactiveEntryButton)}
            icon={faToggleOn}
            title='Environment stopping...'
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
          />
        );

      default:
          return null;
  }
};

InteractiveNavEntry.propTypes = {
  /** Entry name */
  name: PropTypes.string,
  /** Entry description */
  description: PropTypes.string,
  /** Entry status */
  status: PropTypes.oneOf(STATUS),
  runtime_status: PropTypes.oneOf(RUNTIME_STATUS),
  /** Entry action */
  action: PropTypes.oneOf(NAV_ENTRY_ACTIONS),
  /** Entry type */
  type: PropTypes.oneOf(ENTRY_TYPES),
  /** Number of passing testcases entry has */
  caseCountPassed: PropTypes.number,
  /** Number of failing testcases entry has */
  caseCountFailed: PropTypes.number,
};

const styles = StyleSheet.create({
  entryName: {
    overflow: "hidden",
    "text-overflow": "ellipsis",
    "white-space": "nowrap",
    fontSize: "small",
    fontWeight: 500,
  },
  entryIcons: {
    paddingLeft: '1em',
    display: 'flex',
    "flex-wrap": "nowrap",
    "align-items": "center",
  },
  entryIcon: {
    fontSize: 'x-small',
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
  inactiveEntryButton: {
    textDecoration: 'none',
    position: 'relative',
    display: 'inline-block',
    height: '2.4em',
    width: '2.4em',
    cursor: 'pointer',
    color: MEDIUM_GREY,
    padding: '0.7em 0em 0.7em 0em',
    transition: 'all 0.3s ease-out 0s',
  },
  badge: {
    opacity: 0.5,
  },
  passedBadge: {
    backgroundColor: GREEN,
  },
  failedBadge: {
    backgroundColor: RED,
  },
  errorBadge: {
    backgroundColor: RED,
  },
  unstableBadge: {
    backgroundColor: ORANGE,
  },
  unknownBadge: {
    backgroundColor: BLACK,
  },
  passed: {
    color: GREEN,
  },
  failed: {
    color: RED,
  },
  error: {
    color: RED,
  },
  unstable: {
    color: ORANGE,
  },
  unknown: {
    color: BLACK,
  },
});

export default InteractiveNavEntry;
