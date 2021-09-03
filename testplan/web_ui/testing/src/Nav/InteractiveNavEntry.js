import React from 'react';
import PropTypes from 'prop-types';
import { Badge } from 'reactstrap';
import { StyleSheet, css } from "aphrodite";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faPlay,
  faRedo,
  faHourglass,
  faToggleOff,
  faToggleOn,
  faFastBackward,
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
    props.envStatus,
    props.handlePlayClick,
    props.suiteRelated,
    props.action,
  );
  const envStatusIcon = getEnvStatusIcon(
    props.runtime_status, props.envStatus, props.envCtrlCallback
  );
  const resetReportIcon = getResetReportIcon(
    props.runtime_status,
    props.envStatus,
    props.handleResetClick,
    props.type,
  );

  return (
    <div
      className='d-flex justify-content-between align-items-center'
      style={{
        height: "1.5em",
        webkitUserSelect: "text",
        MozUserSelect: "text",
        MsUserSelect: "text",
        UserSelect: "text",
      }}
    >
      <Badge
        className={css(styles.entryIcon, styles[badgeStyle])}
        title={props.type}
        pill
      >
        {CATEGORY_ICONS[props.type]}
      </Badge>
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
        {resetReportIcon}
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
const getStatusIcon = (
  entryStatus, envStatus, handlePlayClick, suiteRelated, action
) => {
  if (suiteRelated) {
    return null;
  }

  switch (entryStatus) {
    case 'ready':
      return (
        <FontAwesomeIcon
          className={
            envStatusChanging(envStatus) || action === 'prohibit'
              ? css(styles.inactiveEntryButton)
              : css(styles.entryButton)
          }
          icon={faPlay}
          title='Run tests'
          onClick={
            envStatusChanging(envStatus) || action === 'prohibit'
              ? ignoreClickEvent
              : handlePlayClick
          }
        />
      );

    case 'waiting':
      return (
        <FontAwesomeIcon
          className={css(styles.inactiveEntryButton)}
          icon={faHourglass}
          title='Waiting...'
          spin
          onClick={ignoreClickEvent}
        />
      );

    case 'running':
      return (
        <FontAwesomeIcon
          className={css(styles.inactiveEntryButton)}
          icon={faRedo}
          title='Running...'
          spin
          onClick={ignoreClickEvent}
        />
      );

    case 'resetting':
      return (
        <FontAwesomeIcon
          className={css(styles.inactiveEntryButton)}
          icon={faRedo}
          title='Resetting...'
          spin
          onClick={ignoreClickEvent}
        />
      );

    case 'finished':
      return (
        <FontAwesomeIcon
          className={
            envStatusChanging(envStatus) || action === 'prohibit'
              ? css(styles.inactiveEntryButton)
              : css(styles.entryButton)
          }
          icon={faRedo}
          title='Run tests'
          onClick={
            envStatusChanging(envStatus) || action === 'prohibit'
              ? ignoreClickEvent
              : handlePlayClick
          }
        />
      );

    case 'not_run':
      return (
        <FontAwesomeIcon
          className={
            envStatusChanging(envStatus) || action === 'prohibit'
              ? css(styles.inactiveEntryButton)
              : css(styles.entryButton)
          }
          icon={faRedo}
          title='Run tests'
          onClick={
            envStatusChanging(envStatus) || action === 'prohibit'
              ? ignoreClickEvent
              : handlePlayClick
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
const getEnvStatusIcon = (entryStatus, envStatus, envCtrlCallback) => {
  switch (envStatus) {
    case 'STOPPED':
      return (
        <FontAwesomeIcon
          className={
            testInProgress(entryStatus)
              ? css(styles.inactiveEntryButton)
              : css(styles.entryButton)
          }
          icon={faToggleOff}
          title='Start environment'
          onClick={
            testInProgress(entryStatus)
              ? ignoreClickEvent
              : (e) => envCtrlCallback(e, "start")
          }
        />
      );

    case 'STOPPING':
      return (
        <FontAwesomeIcon
          className={css(styles.inactiveEntryButton)}
          icon={faToggleOn}
          title='Environment stopping...'
          onClick={ignoreClickEvent}
        />
      );

    case 'STARTED':
      return (
        <FontAwesomeIcon
          className={
            testInProgress(entryStatus)
              ? css(styles.inactiveEntryButton)
              : css(styles.entryButton)
          }
          icon={faToggleOn}
          title='Stop environment'
          onClick={
            testInProgress(entryStatus)
              ? ignoreClickEvent
              : (e) => envCtrlCallback(e, "stop")
          }
        />
      );

    case 'STARTING':
      return (
        <FontAwesomeIcon
          className={css(styles.inactiveEntryButton)}
          icon={faToggleOff}
          title='Environment starting...'
          onClick={ignoreClickEvent}
        />
      );

    default:
      return null;
  }
};

/*
 * Returns the report reset component for entries that represent test
 * instance. Returns null for suite entries and case entries.
 */
const getResetReportIcon = (
  entryStatus, envStatus, handleResetClick, entryType) => {
  if (
    entryType === 'multitest' || entryType === "unittest" ||
    entryType === "gtest" || entryType === "cppunit" ||
    entryType === "boost-test" || entryType === "hobbestest" ||
    entryType === "pytest" || entryType === "pyunit" ||
    entryType === "qunit" || entryType === "junit"
  ) {
    return (
      <FontAwesomeIcon
        className={
          envStatusChanging(envStatus) || testInProgress(entryStatus)
            ? css(styles.inactiveEntryButton)
            : css(styles.entryButton)
        }
        icon={faFastBackward}
        title='Reset report'
        onClick={
          envStatusChanging(envStatus) || testInProgress(entryStatus)
            ? ignoreClickEvent
            : handleResetClick
        }
      />
    );
  } else {
    return null;
  }
};

/**
 * Is environment in the process of starting or stopping.
 */
const envStatusChanging = (envStatus) => {
  return envStatus === 'STARTING' || envStatus === 'STOPPING';
};

/**
 * Is test already working and the client needs to wait for the result.
 */
const testInProgress = (entryStatus) => {
  return (
    entryStatus === 'running' || entryStatus === 'resetting' ||
    entryStatus === 'waiting'
  );
};

/**
 * Button on interactive Nav entry is disabled and no response to clicking.
 */
const ignoreClickEvent = (e) => {
  e.preventDefault();
  e.stopPropagation();
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
    marginLeft: '3px',
    flex: "auto",
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
    transition: 'all 0.3s ease-out 0s !important',
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
