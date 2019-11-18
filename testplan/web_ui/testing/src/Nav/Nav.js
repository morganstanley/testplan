import React from 'react';
import PropTypes from 'prop-types';

import NavBreadcrumbs from "./NavBreadcrumbs";
import NavList from "./NavList";
import {ParseNavSelection} from "./navUtils";

/**
 * Nav component:
 *   * render breadcrumbs menu.
 *   * render list menu.
 *   * handle clicking through menus, tracking what has been selected.
 *   * auto select entries if the list is empty or has 1 entry.
 */
const Nav = (props) => {
  const selection = ParseNavSelection(
    props.report,
    props.selected,
  );

  let selectedUid = undefined;
  if (props.selected && props.selected.length>0) {
    selectedUid = props.selected[props.selected.length-1].uid;
  }

  return (
    <>
      <NavBreadcrumbs
        entries={selection.navBreadcrumbs}
        handleNavClick={props.handleNavClick}
      />
      <NavList
        entries={selection.navList}
        breadcrumbLength={selection.navBreadcrumbs.length}
        handleNavClick={props.handleNavClick}
        filter={props.filter}
        displayEmpty={props.displayEmpty}
        displayTags={props.displayTags}
        selectedUid={selectedUid}
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
