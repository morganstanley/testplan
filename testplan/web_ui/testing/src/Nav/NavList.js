import React from 'react';
import PropTypes from 'prop-types';
import {ListGroup} from 'reactstrap';
import {StyleSheet, css} from 'aphrodite';

import NavEntry from './NavEntry';
import {CreateNavButtons} from './navUtils.js';
import Column from './Column';
import {STATUS, COLUMN_WIDTH} from "../Common/defaults";

/**
 * Render a vertical list of all the currently selected entries children.
 */
const NavList = (props) => {
  const navButtons = CreateNavButtons(
    props,
    (entry) => (
      <NavEntry
        name={entry.name}
        status={entry.status}
        type={entry.category}
        caseCountPassed={entry.case_count.passed}
        caseCountFailed={entry.case_count.failed}
      />
    ),
    props.selectedUid
  );

  return (
    <Column width={COLUMN_WIDTH} >
      <ListGroup className={css(styles.buttonList)}>{navButtons}</ListGroup>
    </Column>
  );
};

const styles = StyleSheet.create({
  buttonList: {
    'overflow-y': 'auto',
    'height': '100%',
  }
});


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
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display tags on navbar */
  displayEmpty: PropTypes.bool,
  /** Flag to display empty testcase on navbar */
  displayTags: PropTypes.bool,
  /** Entry uid to be focused */
  selectedUid: PropTypes.string,
};

export default NavList;
