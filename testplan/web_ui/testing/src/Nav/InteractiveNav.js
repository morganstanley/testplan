/* Interactive navigation component. */
import React from 'react';
import PropTypes from 'prop-types';

import NavBreadcrumbs from "./NavBreadcrumbs";
import InteractiveNavList from "./InteractiveNavList";
import {ParseNavSelection, HandleNavClick} from "./navUtils";

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
class InteractiveNav extends React.Component {

  constructor(props) {
    super(props);
    this.state = {selected: props.report};
    this.handleNavClick = HandleNavClick.bind(this);
    this.handlePlayClick = this.handlePlayClick.bind(this);
  }

  /* Handle the play button being clicked on a Nav entry. */
  handlePlayClick(e, entry) {
    e.stopPropagation();
    console.log("Running " + entry.name);
    this.props.runEntry(entry);
  }

  render() {
    const selection = ParseNavSelection(
      this.props.report,
      this.state.selected,
    );
    return (
      <>
        <NavBreadcrumbs
          entries={selection.navBreadcrumbs}
          handleNavClick={this.handleNavClick}
        />
        <InteractiveNavList
          entries={selection.navList}
          breadcrumbLength={selection.navBreadcrumbs.length}
          handleNavClick={this.handleNavClick}
          autoSelect={() => undefined}
          filter={undefined}
          displayEmpty={true}
          displayTags={false}
          handlePlayClick={this.handlePlayClick}
        />
      </>
    );
  }
}

InteractiveNav.propTypes = {
  /** Testplan report */
  report: PropTypes.arrayOf(PropTypes.object),
};

export default InteractiveNav;
