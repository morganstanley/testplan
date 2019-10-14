import React from 'react';
import PropTypes from 'prop-types';
import {ListGroup} from 'reactstrap';

import NavEntry from './NavEntry';
import {CreateNavButtons} from './navUtils.js';
import Column from './Column';
import {STATUS} from "../Common/defaults";
import {getNavEntryType} from "../Common/utils";

/**
 * Render a vertical list of all the currently selected entries children.
 */
const NavList = (props) => {
  const navButtons = CreateNavButtons(props, (entry) => (
    <NavEntry
      name={entry.name}
      status={entry.status}
      type={getNavEntryType(entry)}
      caseCountPassed={entry.case_count.passed}
      caseCountFailed={entry.case_count.failed}
    />
  ));

  return (
    <Column>
      <ListGroup>{navButtons}</ListGroup>
    </Column>
  );
};

NavList.propTypes = {
  /** Nav list entries to be displayed */
  entries: PropTypes.arrayOf(PropTypes.shape({
    uid: PropTypes.string,
    name: PropTypes.string,
    status: PropTypes.oneOf(STATUS),
    case_count: PropTypes.shape({
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
};

export default NavList;
