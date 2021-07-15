import React from 'react';
import PropTypes from 'prop-types';
import NavBreadcrumbs from "./NavBreadcrumbs";
import NavList from "./NavList";
import TreeViewNav from "./TreeView";
import { GetSelectedUid, GetNavEntries } from "./navUtils";

/**
 * Nav component:
 *   * render breadcrumbs menu.
 *   * render list menu.
 *   * handle clicking through menus, tracking what has been selected.
 *   * auto select entries if the list is empty or has 1 entry.
 */
const Nav = (props) => {
  const breadCrumbEntries = props.selected;
  return (
    <>
      <NavBreadcrumbs
        entries={breadCrumbEntries}
        url={props.url}
      />
      {renderNavigation(props)}
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
  /** Flag to display tree view or default view */
  treeView: PropTypes.bool,
  /** Flag to display tags on navbar */
  displayTags: PropTypes.bool,
  /** Flag to display execution time on navbar */
  displayTime: PropTypes.bool,
  /** Flag to display empty testcase on navbar */
  displayEmpty: PropTypes.bool,

  url: PropTypes.string
};


const renderNavigation = (props) => {
  const breadCrumbEntries = props.selected;
  if (props.treeView) {
    const navEntries = props.report ? props.report.entries : [];
    return <TreeViewNav
      width={props.navListWidth}
      entries={navEntries}
      breadcrumbLength={breadCrumbEntries.length}
      handleColumnResizing={props.handleColumnResizing}
      filter={props.filter}
      displayEmpty={props.displayEmpty}
      displayTags={props.displayTags}
      displayTime={props.displayTime}
      selected={props.selected}
      selectedUid={GetSelectedUid(props.selected)}
      url={props.url}
    />;
  }
  const navEntries = GetNavEntries(props.selected);
  return <NavList
    width={props.navListWidth}
    entries={navEntries}
    breadcrumbLength={breadCrumbEntries.length}
    handleColumnResizing={props.handleColumnResizing}
    filter={props.filter}
    displayEmpty={props.displayEmpty}
    displayTags={props.displayTags}
    displayTime={props.displayTime}
    selectedUid={GetSelectedUid(props.selected)}
    url={props.url}
  />;
};

export default Nav;