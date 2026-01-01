/**
 * Navigation utility functions.
 */
import React from "react";
import { ListGroup, ListGroupItem } from "reactstrap";
import { css } from "aphrodite";
import _ from "lodash";
import { NavLink } from "react-router-dom";
import { generatePath } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import TagList from "./TagList";
import Column from "./Column";
import CommonStyles, { statusStyles } from "../Common/Styles.js";
import { STATUS_CATEGORY } from "../Common/defaults.js";
import { navStyles } from "../Common/Styles";
import {
  generateURLWithParameters,
  formatShortDuration,
} from "../Common/utils";
import { isReportLeaf } from "../Report/reportUtils";

/**
 * Create the list entry buttons or a single button stating nothing can be
 * displayed.
 *
 * @returns {Array|ListGroupItem}
 */
const CreateNavButtons = (props, createEntryComponent, uidEncoder) => {
  // Apply all filters to the entries.
  const filteredEntries = applyAllFilters(
    props.filter,
    props.entries,
    props.displayEmpty,
    props.displaySkipped
  );

  // Create buttons for each of the filtered entries.
  const navButtons = filteredEntries.map((entry, entryIndex) => {
    const tags =
      props.displayTags && entry.tags ? (
        <TagList entryName={entry.name} tags={entry.tags} />
      ) : null;

    const tabIndex = entryIndex + 1;
    const cssClass = [
      navStyles.navButton,
      navStyles.navButtonInteract,
      CommonStyles.unselectable,
    ];
    const cssActiveClass = [...cssClass, navStyles.navButtonInteractFocus];

    let [reportuid, ...selectionuids] = uidEncoder
      ? entry.uids.map(uidEncoder)
      : entry.uids;
    const linkTo = generateURLWithParameters(
      window.location,
      generatePath(props.url, {
        uid: reportuid,
        selection: selectionuids,
      })
    );

    return (
      <ListGroupItem
        tabIndex={tabIndex.toString()}
        key={entry.hash || entry.uid}
        className={css(cssClass)}
        activeClassName={css(cssActiveClass)}
        tag={NavLink}
        to={linkTo}
        action
      >
        {tags}
        {createEntryComponent(entry)}
      </ListGroupItem>
    );
  });

  const navButtonsEmpty = (
    <ListGroupItem className={css(navStyles.navButton)}>
      No entries to display...
    </ListGroupItem>
  );

  return navButtons.length > 0 ? navButtons : navButtonsEmpty;
};

const nonEmptyEntry = (entry) => {
  if (isReportLeaf(entry)) {
    return entry.entries !== null && entry.entries.length > 0;
  } else {
    return entry.counter && entry.counter.total > 0;
  }
};

const nonSkippedEntry = (entry) => {
  return entry.status !== "skipped" || entry.status_override !== "skipped";
};

/**
 * Apply all filters to a list of entries
 *
 *  * Apply the "named" filter (currently just filters out passed or failed
 *    entries).
 *  * Filter out empty testcases if required.
 */
const applyAllFilters = (filter, entries, displayEmpty, displaySkipped) => {
  const filteredEntries = applyNamedFilter(entries, filter);
  let composedFilter = (entry) => true;
  if (!displayEmpty) {
    composedFilter = nonEmptyEntry;
  }
  if (!displaySkipped) {
    const _composedFilter = composedFilter;
    composedFilter = (entry) =>
      _composedFilter(entry) && nonSkippedEntry(entry);
  }
  return filteredEntries.filter(composedFilter);
};

/**
 * Apply the named filter to a list of entries. The filter string may be:
 *
 *  * 'pass' to filter out failed entries
 *  * 'fail' to filter out passed entries
 */
const applyNamedFilter = (entries, filter) => {
  switch (filter) {
    case "pass":
      return entries.filter(
        (entry) => (entry.counter ? entry.counter.passed | 0 : 0) > 0
      );
    case "fail":
      return entries.filter(
        (entry) =>
          entry.status === "error" ||
          entry.status === "failed" ||
          (entry.counter ? entry.counter.failed | 0 : 0) +
            (entry.counter ? entry.counter.error | 0 : 0) >
            0
      );

    default:
      return entries;
  }
};

/**
 * Return the UID of the currently selected entry, or null if there is no
 * entry selected.
 */
const GetSelectedUid = (selected) => {
  if (selected && selected.length > 0) {
    return selected[selected.length - 1].uid;
  } else {
    return null;
  }
};

/**
 * Get the entries to present to a user in the navigation column. In general,
 * we present a list of the child entries of the currently selected report
 * node so that a user may click to drill down to the next level (e.g. from
 * MultiTest into a suite). As a special case, when a testcase is selected
 * we do not drill down any further and instead display all entries in the
 * suite that testcase belongs to.
 *
 * @param {Array[ReportNode]} selected - Current selection hierarchy.
 * @return {Array[ReportNode]} Report nodes to display in the navigation
 *                             column.
 */
const GetNavEntries = (selected) => {
  const selectedEntry = selected[selected.length - 1];

  if (!selectedEntry) {
    return [];
  } else if (isReportLeaf(selectedEntry)) {
    const suite = selected[selected.length - 2];

    // All testcases should belong to a suite, throw an error if we can't
    // find it.
    if (!suite) {
      throw new Error(
        "Could not find parent suite of testcase " + selectedEntry.name
      );
    }
    return suite.entries;
  } else {
    return selectedEntry.entries;
  }
};

/**
 * Get the interavtive entries to present to a user in the navigation column.
 * Will check attributes of these entries and make changes to them if necessary.
 * For example, if several testcase entries belong to a testsuite which sets
 * attribute "strict_order" enabled, then the testcase entry should be disabled
 * unless all previous ones get execution results.
 *
 * @param {Array[ReportNode]} selected - Current selection hierarchy.
 */
const GetInteractiveNavEntries = (selected) => {
  let selectedEntry = selected[selected.length - 1];

  if (!selectedEntry) {
    return [];
  }

  if (
    isReportLeaf(selectedEntry) ||
    selectedEntry.category === "parametrization"
  ) {
    selectedEntry = selected[selected.length - 2]; // move to testsuite entry
  }

  // If testsuite has `strict_order` attribute, UI will set enable/disable
  // status of testcase items to force user to run testcase one by one.
  if (selectedEntry.category === "testsuite" && selectedEntry.strict_order) {
    let testcaseEntries = []; // contains all testcase entries in testsuite
    selectedEntry.entries.forEach((childEntry) => {
      if (childEntry.category === "testcase") {
        testcaseEntries.push(childEntry);
      } else if (childEntry.category === "parametrization") {
        childEntry.entries.forEach((entry) => {
          testcaseEntries.push(entry);
        });
      }
    });

    // To make all testcases run sequentially, in a test suite only the entry
    // next to the recently finished testcase have "play" button enabled.
    let idx = 0;
    while (idx < testcaseEntries.length) {
      if (testcaseEntries[idx].runtime_status !== "finished") {
        break;
      }
      ++idx;
    }
    if (idx > 0) {
      // at least one testcase already finished
      testcaseEntries.slice(0, idx).forEach((entry) => {
        entry.action = "prohibit";
      });
    }
    if (idx < testcaseEntries.length) {
      // at least one testcase is ready to run
      testcaseEntries[idx].action =
        testcaseEntries[idx].runtime_status === "running" ||
        testcaseEntries[idx].runtime_status === "resetting" ||
        testcaseEntries[idx].runtime_status === "waiting"
          ? "prohibit"
          : "play";
      testcaseEntries.slice(idx + 1).forEach((entry) => {
        entry.action = "prohibit";
      });
    }

    // Enable/disable status of "play" button of each parametrization group
    // entry depends on its child entries (the 1st child must be ready to run).
    selectedEntry.entries.forEach((childEntry) => {
      if (childEntry.category === "parametrization") {
        if (
          childEntry.entries.some((entry) => {
            return entry.action === "play";
          })
        ) {
          childEntry.action = "play";
        } else {
          childEntry.action = "prohibit";
        }
      }
    });
  }

  return GetNavEntries(selected);
};

/**
 * Get the entries to display in the navigation breadcrumbs bar. Generally
 * this is just the selection hierarchy. As a special case, when a testcase
 * is selected, we only display up to the suite level in the breadcrumb bar.
 *
 * @param {Array[ReportNode]} selected - Current selection hierarchy.
 * @return {Array[ReportNode]} Report nodes to display in the breadcrumb bar.
 */
const GetNavBreadcrumbs = (selected) => {
  const selectedEntry = selected[selected.length - 1];
  if (!selectedEntry) {
    return [];
  } else if (isReportLeaf(selectedEntry)) {
    return selected.slice(0, selected.length - 1);
  } else {
    return selected;
  }
};

const GetNavColumn = (props, navButtons) => (
  <Column width={props.width} handleColumnResizing={props.handleColumnResizing}>
    <ListGroup className={css(navStyles.buttonList)}>{navButtons}</ListGroup>
  </Column>
);

const GetStatusIcon = (status) => (
  <span className={css(navStyles.statusIcon)}>
    <FontAwesomeIcon
      title={status}
      size="sm"
      icon={statusStyles[STATUS_CATEGORY[status]].icon}
      className={css(navStyles.icon)}
    />
  </span>
);

const generateNavTimeInfo = (
  setupTimeProp,
  teardownTimeProp,
  executionTimeProp
) => {
  let totalTime = null;
  if (_.isNumber(executionTimeProp)) {
    totalTime = executionTimeProp;
    totalTime += _.isNumber(setupTimeProp) ? setupTimeProp : 0;
    totalTime += _.isNumber(teardownTimeProp) ? teardownTimeProp : 0;
  }

  const detailedTimeElement =
    _.isNumber(setupTimeProp) || _.isNumber(teardownTimeProp) ? (
      <span
        key={`nav-time-detailed-${setupTimeProp}-${executionTimeProp}-${teardownTimeProp}`}
        className={css(navStyles.entryIcon)}
        title="Setup / Execution / Teardown duration"
      >
        ({formatShortDuration(setupTimeProp)}/
        {formatShortDuration(executionTimeProp)}/
        {formatShortDuration(teardownTimeProp)})
      </span>
    ) : null;
  const totalTimeElement = _.isNumber(totalTime) ? (
    <span
      key={`nav-time-total-${totalTime}`}
      className={css(navStyles.entryIcon)}
      title="Total runtime"
    >
      {formatShortDuration(totalTime)}
    </span>
  ) : null;

  return [totalTimeElement, detailedTimeElement];
};

export {
  CreateNavButtons,
  generateNavTimeInfo,
  GetStatusIcon,
  GetSelectedUid,
  GetNavEntries,
  GetInteractiveNavEntries,
  GetNavBreadcrumbs,
  GetNavColumn,
  applyAllFilters,
  applyNamedFilter,
};
