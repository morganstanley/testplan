import React from "react";
import PropTypes from "prop-types";
import { Badge } from "reactstrap";
import { css } from "aphrodite";

import {
  CATEGORY_ICONS,
  ENTRY_TYPES,
  STATUS,
  STATUS_CATEGORY,
} from "../Common/defaults";
import { navStyles } from "../Common/Styles";
import { generateNavTimeInfo } from "./navUtils";

/**
 * Display NavEntry information:
 *   * name.
 *   * case count (passed/failed).
 *   * type (displayed in badge).
 */
const NavEntry = (props) => {
  const badgeStyle = `${STATUS_CATEGORY[props.status]}Badge`;
  const navTimeInfo =  
    props.displayTime ? generateNavTimeInfo(
      props.setupTime,
      props.teardownTime,
      props.executionTime,
    ) : null;

  return (
    <div
      className="d-flex justify-content-between align-items-center"
      style={{
        height: "1.5em",
        userSelect: "none",
      }}
    >
      <Badge
        className={
          css(navStyles.entryIcon, navStyles[badgeStyle], navStyles.badge)
        }
        title={props.type}
        pill
      >
        {CATEGORY_ICONS[props.type]}
      </Badge>
      <div
        className={
          css(navStyles.entryName, navStyles[STATUS_CATEGORY[props.status]])
        }
        title={`${props.description || props.name} - ${props.status}`}
      >
        {props.name}
      </div>
      <div className={css(navStyles.entryIcons)}>
        <span className={
          css(
            navStyles.entryIcon,
            navStyles[STATUS_CATEGORY[props.status]],
            navStyles.navTime,
          )
        }>
          {navTimeInfo}
        </span>
        <span className={
          css(navStyles.entryIcon)
        } title="passed/failed testcases">
          <span className={css(navStyles.passed)}>{props.caseCountPassed}</span>
          /
          <span className={css(navStyles.failed)}>{props.caseCountFailed}</span>
        </span>
      </div>
    </div>
  );
};

NavEntry.propTypes = {
  /** Entry name */
  name: PropTypes.string,
  /** Entry description */
  description: PropTypes.string,
  /** Entry status */
  status: PropTypes.oneOf(STATUS),
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


export default NavEntry;
