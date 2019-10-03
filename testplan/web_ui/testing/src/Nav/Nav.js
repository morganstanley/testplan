import React from 'react';
import PropTypes from 'prop-types';

import NavBreadcrumbs from "./NavBreadcrumbs";
import NavList from "./NavList";
import {ParseNavSelection, HandleNavClick} from "./navUtils";
import {getNavEntryType} from "../Common/utils";

/**
 * Nav component:
 *   * render breadcrumbs menu.
 *   * render list menu.
 *   * handle clicking through menus, tracking what has been selected.
 *   * auto select entries if the list is empty or has 1 entry.
 */
class Nav extends React.Component {
  constructor(props) {
    super(props);
    this.handleNavClick = HandleNavClick.bind(this);
    this.autoSelect = this.autoSelect.bind(this);
    this.state = {
      selected: []
    };
  }

  /**
   * Auto select Nav entries depending on whether the passed entries Array is
   * empty (go up a level) or has 1 entry (go down a level).
   *
   * @param {Array} entries - Nav entries (should be NavList entries).
   * @param breadcrumbsLength - Number of the NavBreadcrumbs entries.
   * @public
   */
  autoSelect(entries, breadcrumbsLength) {
    let selected;
    const lastSelectedType = this.state.selected.length > 0 ?
      this.state.selected[this.state.selected.length - 1].type :
      undefined;
    if (entries.length === 0 && this.state.selected.length > 1) {
      selected = this.state.selected.slice(0, breadcrumbsLength);
    } else if (entries.length === 1 && lastSelectedType !== 'testcase') {
      selected = this.state.selected.concat([{
        uid: entries[0].uid,
        type: getNavEntryType(entries[0])
      }]);
    }
    if (selected !== undefined) {
      this.setState({selected: selected});
    }
  }

  render() {
    const selection = ParseNavSelection(this.props.report, this.state.selected);
    return (
      <>
        <NavBreadcrumbs
          entries={selection.navBreadcrumbs}
          handleNavClick={this.handleNavClick}
        />
        <NavList
          entries={selection.navList}
          breadcrumbLength={selection.navBreadcrumbs.length}
          handleNavClick={this.handleNavClick}
          autoSelect={this.autoSelect}
          filter={this.props.filter}
          displayEmpty={this.props.displayEmpty}
          displayTags={this.props.displayTags}
        />
      </>
    );
  }
}

Nav.propTypes = {
  /** Testplan report */
  report: PropTypes.arrayOf(PropTypes.object),
  /** Function to handle saving the assertions found by the Nav */
  saveAssertions: PropTypes.func,
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display tags on navbar */
  displayTags: PropTypes.bool,
  /** Flag to display empty testcase on navbar */
  displayEmpty: PropTypes.bool,
};

export default Nav;
