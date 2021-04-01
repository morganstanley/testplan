import React from 'react';
import PropTypes from 'prop-types';

import NavEntry from './NavEntry';
import {CreateNavButtons, GetNavColumn} from './navUtils.js';
import {STATUS} from "../Common/defaults";

/**
 * Render a vertical list of all the currently selected entries children.
 */
const NavList = (props) => {
  const navButtons = CreateNavButtons(
    props,
    (entry) => {
      const executionTime = (entry.timer && entry.timer.run) ? (
        (new Date(entry.timer.run.end)).getTime() -
        (new Date(entry.timer.run.start)).getTime()) / 1000 : null;

      return (
        <NavEntry
          name={entry.name}
          description={entry.description}
          status={entry.status}
          type={entry.category}
          caseCountPassed={entry.counter.passed}
          caseCountFailed={entry.counter.failed + (entry.counter.error || 0)}
          executionTime={executionTime}
          displayTime={props.displayTime}
        />
      );
    },
  );

  return GetNavColumn(props, navButtons);
};

NavList.propTypes = {
  /** Nav list entries to be displayed */
  entries: PropTypes.arrayOf(PropTypes.shape({
    uid: PropTypes.string,
    name: PropTypes.string,
    description: PropTypes.string,
    status: PropTypes.oneOf(STATUS),
    counter: PropTypes.shape({
      passed: PropTypes.number,
      failed: PropTypes.number,
    }),
  })),
  /** Number of entries in the breadcrumb menu */
  breadcrumbLength: PropTypes.number,
  /** Function to handle Nav list resizing */
  handleColumnResizing: PropTypes.func,
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display empty testcase on navbar */
  displayEmpty: PropTypes.bool,
  /** Flag to display tags on navbar */
  displayTags: PropTypes.bool,
  /** Flag to display execution time on navbar */
  displayTime: PropTypes.bool,
  /** Entry uid to be focused */
  selectedUid: PropTypes.string,

  url: PropTypes.string
};

export default NavList;
