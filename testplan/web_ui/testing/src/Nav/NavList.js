import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {ListGroup, ListGroupItem} from 'reactstrap';
import {StyleSheet, css} from 'aphrodite';

import NavEntry from './NavEntry';
import Column from './Column';
import {STATUS} from "../Common/defaults";
import {getNavEntryType} from "../Common/utils";
import {LIGHT_GREY, DARK_GREY} from "../Common/defaults";

/**
 * Render a vertical list of all the currently selected entries children.
 */
class NavList extends Component {
  componentDidMount() {
    this.props.autoSelect(this.props.entries, this.props.breadcrumbLength);
  }

  componentDidUpdate() {
    this.props.autoSelect(this.props.entries, this.props.breadcrumbLength);
  }

  /**
   * Create the list entry buttons or a single button stating nothing can be
   * displayed.
   *
   * @returns {Array|ListGroupItem}
   */
  createNavButtons() {
    const depth = this.props.breadcrumbLength;
    let navButtons = [];
    let tabIndex = 1;
    for (const entry of this.props.entries) {
      navButtons.push(
        <ListGroupItem
          tabIndex={tabIndex.toString()}
          key={entry.uid}
          className={css(styles.navButton, styles.navButtonInteract)}
          onClick={((e) => this.props.handleNavClick(e, entry, depth))}>
          <NavEntry
            name={entry.name}
            status={entry.status}
            type={getNavEntryType(entry)}
            caseCountPassed={entry.case_count.passed}
            caseCountFailed={entry.case_count.failed} />
        </ListGroupItem>
      );
      tabIndex += 1;
    }

    const navButtonsEmpty = <ListGroupItem className={css(styles.navButton)}>
      No entries to display...
    </ListGroupItem>;

    return navButtons.length > 0 ? navButtons : navButtonsEmpty;
  }

  render() {
    const navButtons = this.createNavButtons();
    return (
      <Column>
        <ListGroup>{navButtons}</ListGroup>
      </Column>
    );
  }
}

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
  /** Function to automatically select Nav entries */
  autoSelect: PropTypes.func,
};

const styles = StyleSheet.create({
  navButton: {
    position: 'relative',
    display: 'inline-block',
    border: 'none',
    backgroundColor: LIGHT_GREY,
  },
  navButtonInteract: {
    ':hover': {
      backgroundColor: DARK_GREY,
    },
    ':focus': {
      backgroundColor: DARK_GREY,
      outline: 'none',
    }
  },
});

export default NavList;
