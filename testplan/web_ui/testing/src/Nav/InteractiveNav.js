/* Interactive navigation component. */
import React from 'react';
import PropTypes from 'prop-types';
import base64url from 'base64url';

import NavBreadcrumbs from "./NavBreadcrumbs";
import InteractiveNavList from "./InteractiveNavList";
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
  const navEntries = GetInteractiveNavEntries(props.selected);
  const breadCrumbEntries = GetNavBreadcrumbs(props.selected);

  return (
    <>
      <NavBreadcrumbs
        entries={breadCrumbEntries}        
        url={props.url}
        uidEncoder = {base64url}
      />
      <InteractiveNavList
        width={props.navListWidth}
        entries={navEntries}
        breadcrumbLength={breadCrumbEntries.length}        
        handleColumnResizing={props.handleColumnResizing}
        filter={null}
        displayEmpty={true}
        displayTags={false}
        displayTime={false}
        selectedUid={GetSelectedUid(props.selected)}
        handlePlayClick={props.handlePlayClick}
        envCtrlCallback={props.envCtrlCallback}
        url={props.url}
      />
    </>
  );
};

InteractiveNav.propTypes = {
  /** Testplan report */
  report: PropTypes.object,
};

export default InteractiveNav;
