import React from 'react';
import PropTypes from 'prop-types';
import {ListGroup} from 'reactstrap';

import InteractiveNavEntry from './InteractiveNavEntry';
import Column from './Column';
import {CreateNavButtons} from './navUtils.js';
import {STATUS} from "../Common/defaults";
import {getNavEntryType} from "../Common/utils";

/**
 * Render a vertical list of all the currently selected entries children for
 * an interactive report.
 */
const InteractiveNavList = (props) => {
  const navButtons = CreateNavButtons(props, (entry) => (
    <InteractiveNavEntry
      name={entry.name}
      status={entry.status}
      type={getNavEntryType(entry)}
      caseCountPassed={entry.case_count.passed}
      caseCountFailed={entry.case_count.failed}
      handlePlayClick={(e) => props.handlePlayClick(e, entry)}
    />
  ));

  return (
    <Column>
      <ListGroup>{navButtons}</ListGroup>
    </Column>
  );
};

InteractiveNavList.propTypes = {
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
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display tags on navbar */
  displayEmpty: PropTypes.bool,
  /** Flag to display empty testcase on navbar */
  displayTags: PropTypes.bool,
};

export default InteractiveNavList;
