/* Interactive navigation component. */
import React from 'react';
import PropTypes from 'prop-types';

import NavBreadcrumbs from "./NavBreadcrumbs";
import InteractiveNavList from "./InteractiveNavList";
import {GetSelectedUid, GetNavEntries, GetNavBreadcrumbs} from "./navUtils";

/**
 * Interactive Nav component.
 *
 * Performs similar function as the batch report Nav component, but for
 * interactive mode. Key differences:
 *
 *   * Does not auto-select testcases. Only the root Testplan report is
 *     first selected.
 *   * Adds extra buttons for running testcases interactively and controlling
 *     environments.
 *
 * This component and its sub-components are a WORK IN PROGRESS and is likely
 * to change. In particular, there may initially be some code duplication
 * with the main Nav component, which will need to be eliminated.
 */
const InteractiveNav = (props) => {
  const navEntries = GetNavEntries(props.selected);
  const breadCrumbEntries = GetNavBreadcrumbs(props.selected);

  return (
    <>
      <NavBreadcrumbs
        entries={breadCrumbEntries}
        handleNavClick={props.handleNavClick}
      />
      <InteractiveNavList
        width={props.navListWidth}
        entries={navEntries}
        breadcrumbLength={breadCrumbEntries.length}
        handleNavClick={props.handleNavClick}
        handleColumnResizing={props.handleColumnResizing}
        autoSelect={() => undefined}
        filter={null}
        displayEmpty={true}
        displayTags={false}
        displayTime={false}
        selectedUid={GetSelectedUid(props.selected)}
        handlePlayClick={props.handlePlayClick}
        envCtrlCallback={props.envCtrlCallback}
      />
    </>
  );
};

InteractiveNav.propTypes = {
  /** Testplan report */
  report: PropTypes.object,
};

export default InteractiveNav;
