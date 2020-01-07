import React from 'react';
import PropTypes from 'prop-types';
import {Badge} from 'reactstrap';
import {StyleSheet, css} from "aphrodite";

import {
  RED,
  GREEN,
  ORANGE,
  BLACK,
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
const NavEntry = (props) => {
  const badgeStyle = `${props.status}Badge`;
  return (
    <div className='d-flex justify-content-between'>
      <div
        className={css(styles.entryName, styles[props.status])}
        title={props.name}>
        {props.name}
      </div>
      <div className={css(styles.entryIcons)}>
        <i className={css(styles.entryIcon)} title='passed/failed testcases'>
          <span className={css(styles.passed)}>{props.caseCountPassed}</span>
          /
          <span className={css(styles.failed)}>{props.caseCountFailed}</span>
        </i>
        <Badge
          className={css(styles.entryIcon, styles[badgeStyle], styles.badge)}
          title={props.type}
          pill>
          {CATEGORY_ICONS[props.type]}
        </Badge>
      </div>
    </div>
  );
};

NavEntry.propTypes = {
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
    flex: 1,
  },
  entryIcons: {
    paddingLeft: '1em',
  },
  entryIcon: {
    fontSize: '0.6em',
    margin: '0em 0.5em 0em 0.5em',
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

export default NavEntry;
