import React from 'react';
import PropTypes from 'prop-types';
import _ from 'lodash';
import base64url from 'base64url';

import InteractiveNavEntry from './InteractiveNavEntry';
import {CreateNavButtons, GetNavColumn} from './navUtils.js';
import {STATUS, RUNTIME_STATUS} from "../Common/defaults";

/**
 * Render a vertical list of all the currently selected entries children for
 * an interactive report.
 */
const InteractiveNavList = (props) => {
  const navButtons = CreateNavButtons(
    props,
    (entry) => (
      <InteractiveNavEntry
        name={_.isEmpty(entry.part) ? entry.name : entry.uid}
        description={entry.description}
        status={entry.status}
        runtime_status={entry.runtime_status}
        envStatus={entry.env_status}
        type={entry.category}
        caseCountPassed={entry.counter.passed}
        caseCountFailed={entry.counter.failed}
        handlePlayClick={(e) => props.handlePlayClick(e, entry)}
        envCtrlCallback={
          (e, action) => props.envCtrlCallback(e, entry, action)
        }
        suiteRelated={entry.suite_related}
      />
    ),
    base64url
  );

  // Make the column a little wider for the interactive mode, to account for
  // extra space used by the interactive buttons.
  return GetNavColumn(props, navButtons);
};

InteractiveNavList.propTypes = {
  /** Nav list entries to be displayed */
  entries: PropTypes.arrayOf(PropTypes.shape({
    uid: PropTypes.string,
    name: PropTypes.string,
    description: PropTypes.string,
    status: PropTypes.oneOf(STATUS),
    runtime_status: PropTypes.oneOf(RUNTIME_STATUS),
    counter: PropTypes.shape({
      passed: PropTypes.number,
      failed: PropTypes.number,
    }),
  })),
  /** Number of entries in the breadcrumb menu */
  breadcrumbLength: PropTypes.number,
  /** Function to handle Nav entries being clicked (selected) */
  handleNavClick: PropTypes.func,
  /** Function to handle Nav list resizing */
  handleColumnResizing: PropTypes.func,
  /** Function to automatically select Nav entries */
  autoSelect: PropTypes.func,
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display empty testcase on navbar */
  displayEmpty: PropTypes.bool,
  /** Flag to display tags on navbar */
  displayTags: PropTypes.bool,
  /** Flag to display execution time on navbar */
  displayTime: PropTypes.bool,
};

export default InteractiveNavList;
