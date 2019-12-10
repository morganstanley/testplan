import React from 'react';
import PropTypes from 'prop-types';

import NavBreadcrumbs from "./NavBreadcrumbs";
import NavList from "./NavList";
import {GetSelectedUid, GetNavEntries, GetNavBreadcrumbs} from "./navUtils";

/**
 * Nav component:
 *   * render breadcrumbs menu.
 *   * render list menu.
 *   * handle clicking through menus, tracking what has been selected.
 *   * auto select entries if the list is empty or has 1 entry.
 */
const Nav = (props) => {
  const navEntries = GetNavEntries(props.selected);
  const breadCrumbEntries = GetNavBreadcrumbs(props.selected);

  return (
    <>
      <NavBreadcrumbs
        entries={breadCrumbEntries}
        handleNavClick={props.handleNavClick}
      />
      <NavList
        entries={navEntries}
        breadcrumbLength={breadCrumbEntries.length}
        handleNavClick={props.handleNavClick}
        filter={props.filter}
        displayEmpty={props.displayEmpty}
        displayTags={props.displayTags}
        selectedUid={GetSelectedUid(props.selected)}
      />
    </>
  );
};

Nav.propTypes = {
  /** Testplan report */
  report: PropTypes.object,
  /** Selected navigation entries. */
  selected: PropTypes.arrayOf(PropTypes.object),
  /** Function to handle saving the assertions found by the Nav */
  saveAssertions: PropTypes.func,
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display tags on navbar */
  displayTags: PropTypes.bool,
  /** Flag to display empty testcase on navbar */
  displayEmpty: PropTypes.bool,
  /** Callback when a navigation entry is clicked. */
  handleNavClick: PropTypes.func,
};

export default Nav;
