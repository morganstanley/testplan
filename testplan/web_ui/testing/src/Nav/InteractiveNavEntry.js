import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { Badge } from "reactstrap";
import { StyleSheet, css } from "aphrodite";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faPlay,
  faRedo,
  faHourglass,
  faToggleOff,
  faToggleOn,
  faFastBackward,
} from "@fortawesome/free-solid-svg-icons";
import { useAtom } from "jotai";
import _ from "lodash";

import {
  RED,
  GREEN,
  ORANGE,
  BLACK,
  CATEGORY_ICONS,
  ENTRY_TYPES,
  STATUS,
  STATUS_CATEGORY,
  RUNTIME_STATUS,
  ENV_STATUSES,
  NAV_ENTRY_ACTIONS,
} from "../Common/defaults";
import { formatMilliseconds } from "./../Common/utils";
import {
  pendingEnvRequestAtom,
} from "../Report/InteractiveReport";

/**
 * Display interactive NavEntry information:
 *   * name.
 *   * case count (passed/failed).
 *   * type (displayed in badge).
 *   * Interactive status icon
 *   * Environment status icon (if required)
 */
const InteractiveNavEntry = (props) => {
  const [pendingEnvRequest, setPendingEnvRequest] = useAtom(
    pendingEnvRequestAtom
  );
  const badgeStyle = `${STATUS_CATEGORY[props.status]}Badge`;
  const statusIcon = getStatusIcon(
    props.runtime_status,
    props.envStatus,
    props.handleClick,
    props.suiteRelated,
    props.action,
    pendingEnvRequest
  );
  const envStatusIcon = getEnvStatusIcon(
    props.runtime_status,
    props.envStatus,
    props.envCtrlCallback,
    pendingEnvRequest,
    setPendingEnvRequest,
  );
  const resetReportIcon = getResetReportIcon(
    props.runtime_status,
    props.envStatus,
    props.handleClick,
    props.type
  );
  const executionTime =
    props.displayTime && _.isNumber(props.executionTime) ? (
      <span className={css(styles.entryIcon)} title="Execution time">
        <span className={css(styles[STATUS_CATEGORY[props.status]])}>
          {formatMilliseconds(props.executionTime)}
        </span>
      </span>
    ) : null;

  return (
    <div
      className="d-flex justify-content-between align-items-center"
      style={{
        height: "1.5em",
        userSelect: "text",
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
        className={css(styles.entryName, styles[STATUS_CATEGORY[props.status]])}
        title={props.description || props.name}
      >
        {props.name}
      </div>
      <div className={css(styles.entryIcons)}>
        {executionTime}
        <span className={css(styles.entryIcon)} title="passed/failed testcases">
          <span className={css(styles.passed)}>{props.caseCountPassed}</span>/
          <span className={css(styles.failed)}>{props.caseCountFailed}</span>
        </span>
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
  entryStatus,
  envStatus,
  handleClick,
  suiteRelated,
  action,
  pendingEnvRequest,
) => {
  if (suiteRelated) {
    return null;
  }

  const disabled = envStatusChanging(envStatus) || action === "prohibit"
    || envStatusChanging(pendingEnvRequest);
  switch (entryStatus) {
    case "ready":
      return (
        <FontAwesomeIcon
          className={
            disabled ? css(styles.inactiveEntryButton) : css(styles.entryButton)
          }
          icon={faPlay}
          title="Run tests"
          onClick={
            disabled ? ignoreClickEvent : (e) => handleClick(e, "running")
          }
        />
      );

    case "waiting":
      return (
        <FontAwesomeIcon
          className={css(styles.inactiveEntryButton)}
          icon={faHourglass}
          title="Waiting..."
          spin
          onClick={ignoreClickEvent}
        />
      );

    case "resetting":
      return (
        <FontAwesomeIcon
          className={css(styles.inactiveEntryButton)}
          icon={faRedo}
          title="Resetting..."
          spin
          onClick={ignoreClickEvent}
        />
      );

    case "running":
      return (
        <FontAwesomeIcon
          className={css(styles.inactiveEntryButton)}
          icon={faRedo}
          title="Running..."
          spin
          onClick={ignoreClickEvent}
        />
      );

    case "finished":
      return (
        <FontAwesomeIcon
          className={
            disabled ? css(styles.inactiveEntryButton) : css(styles.entryButton)
          }
          icon={faRedo}
          title="Run tests"
          onClick={
            disabled ? ignoreClickEvent : (e) => handleClick(e, "running")
          }
        />
      );

    case "not_run":
      return (
        <FontAwesomeIcon
          className={
            disabled ? css(styles.inactiveEntryButton) : css(styles.entryButton)
          }
          icon={faRedo}
          title="Run tests"
          onClick={
            disabled ? ignoreClickEvent : (e) => handleClick(e, "running")
          }
        />
      );

    default:
      throw new Error("Unexpected status: " + entryStatus);
  }
};

/**
 * Returns
 */
function StartingStoppingIcon(starting) {
    const [isPulsating, setIsPulsating] = useState(
        starting ? false : true
    );

    useEffect(() => {
        const interval = setInterval(() => {
            setIsPulsating((prevState) => !prevState);
        }, 500);

        return () => {
            clearInterval(interval);
        };
    }, []);

    return (
        <FontAwesomeIcon
            className={
                css(
                    styles.inactiveEntryButton,
                    styles.environmentToggle,
                    styles.busyEnvironmentToggle,
                )
            }
            icon={starting ? faToggleOn : faToggleOff}
            title={starting ? "Environment starting..." : "Environment stopping..."}
            onClick={ignoreClickEvent}
            transition="opacity 0.175s ease-in-out"
            animation={isPulsating ? "pulsate 0.35s infinite" : "none"}
            opacity={isPulsating ? 0.5 : 1}
        />
    );
};

/**
 * Returns the environment control component for entries that own an
 * environment. Returns null for entries that do not have an environment.
 */
const getEnvStatusIcon = (
    entryStatus,
    envStatus,
    envCtrlCallback,
    pendingEnvRequest,
    setPendingEnvRequest,
  ) => {
  let disabled = testInProgress(entryStatus)
    || envStatusChanging(pendingEnvRequest);
  switch (envStatus) {
    case ENV_STATUSES.stopped:
      return (
        <FontAwesomeIcon
          className={
            disabled ?
            css(styles.inactiveEntryButton, styles.environmentToggle) :
            css(styles.entryButton, styles.environmentToggle)
          }
          icon={faToggleOff}
          title={disabled ? "Pending action" : "Start environment"}
          onClick={
            disabled ? ignoreClickEvent : (e) => {
              setPendingEnvRequest(ENV_STATUSES.starting);
              envCtrlCallback(e, "start");
            }
          }
        />
      );

    case ENV_STATUSES.stopping:
      if (pendingEnvRequest === ENV_STATUSES.stopping) {
        setPendingEnvRequest("");
      };
      return StartingStoppingIcon(false);

    case ENV_STATUSES.started:
      return (
        <FontAwesomeIcon
          className={
            disabled ?
            css(styles.inactiveEntryButton, styles.environmentToggle) :
            css(styles.entryButton, styles.environmentToggle)
          }
          icon={faToggleOn}
          title={disabled ? "Pending action" : "Stop environment"}
          onClick={
            disabled ? ignoreClickEvent : (e) => {
              setPendingEnvRequest(ENV_STATUSES.stopping);
              envCtrlCallback(e, "stop");
            }
          }
        />
      );

    case ENV_STATUSES.starting:
      if (pendingEnvRequest === ENV_STATUSES.starting) {
        setPendingEnvRequest("");
      };
      return StartingStoppingIcon(true);

    default:
      return null;
  }
};

/*
 * Returns the report reset component for entries that represent test
 * instance. Returns null for suite entries and case entries.
 */
const getResetReportIcon = (entryStatus, envStatus, handleClick, entryType) => {
  if (isTestInstance(entryType)) {
    const disabled =
      envStatusChanging(envStatus) || testInProgress(entryStatus);
    return (
      <FontAwesomeIcon
        className={
          disabled ? css(styles.inactiveEntryButton) : css(styles.entryButton)
        }
        icon={faFastBackward}
        title="Reset MultiTest environment and report"
        onClick={
          disabled ? ignoreClickEvent : (e) => handleClick(e, "resetting")
        }
      />
    );
  } else {
    return null;
  }
};

/**
 * Is entry the same level as a Multitest entry.
 */
const isTestInstance = (entryType) => {
  return entryType === "multitest" ||
    entryType === "unittest" ||
    entryType === "gtest" ||
    entryType === "cppunit" ||
    entryType === "boost-test" ||
    entryType === "hobbestest" ||
    entryType === "pytest" ||
    entryType === "pyunit" ||
    entryType === "qunit" ||
    entryType === "junit"
    ? true
    : false;
};

/**
 * Is environment in the process of starting or stopping.
 */
const envStatusChanging = (envStatus) => {
  return envStatus === ENV_STATUSES.starting
    || envStatus === ENV_STATUSES.stopping;
};

/**
 * Is test already working and the client needs to wait for the result.
 */
const testInProgress = (entryStatus) => {
  return (
    entryStatus === "running" ||
    entryStatus === "resetting" ||
    entryStatus === "waiting"
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
  /** Execution time measured in seconds */
  executionTime: PropTypes.number,
  /** If to display execution time */
  displayTime: PropTypes.bool,
};

const styles = StyleSheet.create({
  entryName: {
    overflow: "hidden",
    "text-overflow": "ellipsis",
    "white-space": "nowrap",
    fontSize: "small",
    fontWeight: 500,
    marginLeft: "3px",
    flex: "auto",
  },
  entryIcons: {
    paddingLeft: "1em",
    display: "flex",
    "flex-wrap": "nowrap",
    "align-items": "center",
  },
  entryIcon: {
    fontSize: "small",
    margin: "0em 0.5em 0em 0.5em",
  },
  entryButton: {
    textDecoration: "none",
    position: "relative",
    display: "inline-block",
    height: "2.4em",
    width: "2.4em",
    cursor: "pointer",
    color: "black",
    padding: "0.7em 0em 0.7em 0em",
    transition: "all 0.3s ease-out 0s",
  },
  inactiveEntryButton: {
    textDecoration: "none",
    position: "relative",
    display: "inline-block",
    height: "2.4em",
    width: "2.4em",
    cursor: "pointer",
    color: BLACK,
    padding: "0.7em 0em 0.7em 0em",
    transition: "all 0.3s ease-out 0s !important",
  },
  environmentToggle: {
    padding: "0.65em 0em 0.65em 0em",
  },
  busyEnvironmentToggle: {
    color: "orange",
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
