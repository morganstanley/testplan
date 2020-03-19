import React from 'react';
import PropTypes from 'prop-types';

import NavEntry from './NavEntry';
import {CreateNavButtons, GetNavColumn} from './navUtils.js';
import {STATUS, COLUMN_WIDTH} from "../Common/defaults";

/**
 * Render a vertical list of all the currently selected entries children.
 */
const NavList = (props) => {
  const navButtons = CreateNavButtons(
    props,
    (entry) => (
      <NavEntry
        name={entry.name}
        status={entry.status}
        type={entry.category}
        caseCountPassed={entry.counter.passed}
        caseCountFailed={entry.counter.failed}
      />
    ),
    props.selectedUid
  );

  return GetNavColumn(COLUMN_WIDTH, navButtons);
};

NavList.propTypes = {
  /** Nav list entries to be displayed */
  entries: PropTypes.arrayOf(PropTypes.shape({
    uid: PropTypes.string,
    name: PropTypes.string,
    status: PropTypes.oneOf(STATUS),
    counter: PropTypes.shape({
      passed: PropTypes.number,
      failed: PropTypes.number,
    }),
  })),
  /** Number of entries in the breadcrumb menu */
  breadcrumbLength: PropTypes.number,
  /** Function to handle Nav entries being clicked (selected) */
  handleNavClick: PropTypes.func,
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display tags on navbar */
  displayEmpty: PropTypes.bool,
  /** Flag to display empty testcase on navbar */
  displayTags: PropTypes.bool,
  /** Entry uid to be focused */
  selectedUid: PropTypes.string,
};

export default NavList;
