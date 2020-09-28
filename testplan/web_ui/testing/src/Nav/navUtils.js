/**
 * Navigation utility functions.
 */
import React from 'react';
import {ListGroup, ListGroupItem} from 'reactstrap';
import {StyleSheet, css} from 'aphrodite';

import TagList from './TagList';
import Column from './Column';
import {LIGHT_GREY, DARK_GREY} from "../Common/defaults";
import CommonStyles from "../Common/Styles.js";

/**
 * Create the list entry buttons or a single button stating nothing can be
 * displayed.
 *
 * @returns {Array|ListGroupItem}
 */
const CreateNavButtons = (
  props,
  createEntryComponent,
  selectedUid
  ) => {
  const depth = props.breadcrumbLength;

  // Apply all filters to the entries.
  const filteredEntries = applyAllFilters(props);

  // Create buttons for each of the filtered entries.
  const navButtons = filteredEntries.map((entry, entryIndex) => {
    const tags = (
      (props.displayTags && entry.tags)
      ? <TagList entryName={entry.name} tags={entry.tags}/>
      : null
    );

    const tabIndex = entryIndex + 1;
    const cssName = [
      styles.navButton, styles.navButtonInteract, CommonStyles.unselectable
    ];
    if (selectedUid && selectedUid === entry.uid) {
      cssName.push(styles.navButtonInteractFocus);
    }

    return (
      <ListGroupItem
        tabIndex={tabIndex.toString()}
        key={entry.uid}
        className={css(...cssName)}
        onClick={((e) => props.handleNavClick(e, entry, depth))}>
        {tags}
        {createEntryComponent(entry)}
      </ListGroupItem>
    );
  });

  const navButtonsEmpty = <ListGroupItem className={css(styles.navButton)}>
    No entries to display...
  </ListGroupItem>;

  return navButtons.length > 0 ? navButtons : navButtonsEmpty;
};

/**
 * Apply all filters to a list of entries
 *
 *  * Apply the "named" filter (currently just filters out passed or failed
 *    entries).
 *  * Filter out empty testcases if required.
 */
const applyAllFilters = (props) => {
  if (props.displayEmpty) {
    return applyNamedFilter(props.entries, props.filter);
  } else {
    return applyNamedFilter(props.entries, props.filter).filter((entry) => {
      if (entry.category === 'testcase') {
        return (entry.entries !== null && entry.entries.length > 0);
      } else {
        return (entry.counter.total > 0);
      }
    });
  }
};

/**
 * Apply the named filter to a list of entries. The filter string may be:
 *
 *  * 'pass' to filter out failed entries
 *  * 'fail' to filter out passed entries
 */
const applyNamedFilter = (entries, filter) => {
  switch (filter) {
    case 'pass':
      return entries.filter(
        (entry) => (entry.counter.passed|0) > 0
      );

    case 'fail':
      return entries.filter(
        (entry) => (entry.counter.failed|0) + (entry.counter.error|0) > 0
      );

    default:
      return entries;
  }
};

export const styles = StyleSheet.create({
  navButton: {
    position: 'relative',
    display: 'block',
    border: 'none',
    backgroundColor: LIGHT_GREY,
    cursor: 'pointer',
  },
  navButtonInteract: {
    ':hover': {
      backgroundColor: DARK_GREY,
    },
  },
  navButtonInteractFocus: {
    backgroundColor: DARK_GREY,
    outline: 'none',
  },
  buttonList: {
    'overflow-y': 'auto',
    'height': '100%',
  },
});

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
  } else if (selectedEntry.category === 'testcase') {
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
  } else if (selectedEntry.category === 'testcase') {
    return selected.slice(0, selected.length - 1);
  } else {
    return selected;
  }
};

const GetNavColumn = (props, navButtons) => (
  <Column
    width={props.width}
    handleColumnResizing={props.handleColumnResizing}
  >
    <ListGroup className={css(styles.buttonList)}>{navButtons}</ListGroup>
  </Column>
);

export {
  CreateNavButtons,
  GetSelectedUid,
  GetNavEntries,
  GetNavBreadcrumbs,
  GetNavColumn,
};
