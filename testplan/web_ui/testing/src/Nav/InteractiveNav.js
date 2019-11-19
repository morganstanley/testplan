/* Interactive navigation component. */
import React from 'react';
import PropTypes from 'prop-types';

import NavBreadcrumbs from "./NavBreadcrumbs";
import InteractiveNavList from "./InteractiveNavList";
import {ParseNavSelection, GetSelectedUid} from "./navUtils";

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
  const selection = ParseNavSelection(
    props.report,
    props.selected,
  );
  return (
    <>
      <NavBreadcrumbs
        entries={selection.navBreadcrumbs}
        handleNavClick={props.handleNavClick}
      />
      <InteractiveNavList
        entries={selection.navList}
        breadcrumbLength={selection.navBreadcrumbs.length}
        handleNavClick={props.handleNavClick}
        autoSelect={() => undefined}
        filter={null}
        displayEmpty={true}
        displayTags={false}
        selectedUid={GetSelectedUid(props.selected)}
        handlePlayClick={props.handlePlayClick}
      />
    </>
  );
};

InteractiveNav.propTypes = {
  /** Testplan report */
  report: PropTypes.object,
};

export default InteractiveNav;
