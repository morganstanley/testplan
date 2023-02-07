/* Interactive navigation component. */
import React from 'react';
import PropTypes from 'prop-types';
import base64url from 'base64url';

import NavBreadcrumbs from "./NavBreadcrumbs";
import InteractiveNavList from "./InteractiveNavList";
import InteractiveTreeViewNav from './InteractiveTreeView';
import {
  GetSelectedUid,
  GetInteractiveNavEntries,
  GetNavBreadcrumbs
} from "./navUtils";

/**
 * Interactive Nav component.
 *
 * Performs similar function as the batch report Nav component, but for
 * interactive mode. Key differences:
 *
 *   * Adds extra buttons for running testcases interactively and controlling
 *     environments.
 *
 * This component and its sub-components are a WORK IN PROGRESS and is likely
 * to change. In particular, there may initially be some code duplication
 * with the main Nav component, which will need to be eliminated.
 */
const InteractiveNav = (props) => {
  const breadCrumbEntries = GetNavBreadcrumbs(props.selected);

  return (
    <>
      <NavBreadcrumbs
        entries={breadCrumbEntries}        
        url={props.url}
        uidEncoder = {base64url}
      />
      {renderNavigation(props)}
    </>
  );
};

InteractiveNav.propTypes = {
  /** Testplan report */
  report: PropTypes.object,
  /** Flag to display tree view or default view */
  treeView: PropTypes.bool,
};

const renderNavigation = (props) => {
  //const navEntries = GetInteractiveNavEntries(props.selected);
  const breadCrumbEntries = GetNavBreadcrumbs(props.selected);

  if (props.treeView) {
    const navEntries = props.report ? props.report.entries : [];
    return <InteractiveTreeViewNav
      width={props.navListWidth}
      entries={navEntries}
      breadcrumbLength={breadCrumbEntries.length}
      handleColumnResizing={props.handleColumnResizing}
      filter={null}
      displayEmpty={true}
      displayTags={false}
      displayTime={false}
      selected={props.selected}
      selectedUid={GetSelectedUid(props.selected)}
      handleClick={props.handleClick}
      envCtrlCallback={props.envCtrlCallback}
      url={props.url}
    />;
  }

  const navEntries = GetInteractiveNavEntries(props.selected);
  
  return <InteractiveNavList
    width={props.navListWidth}
    entries={navEntries}
    breadcrumbLength={breadCrumbEntries.length}
    handleColumnResizing={props.handleColumnResizing}
    filter={null}
    displayEmpty={true}
    displayTags={false}
    displayTime={false}
    selectedUid={GetSelectedUid(props.selected)}
    handleClick={props.handleClick}
    envCtrlCallback={props.envCtrlCallback}
    url={props.url}
  />
};

export default InteractiveNav;
