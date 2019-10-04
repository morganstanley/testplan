/**
 * Navigation utility functions.
 */
import React from 'react';
import {ListGroupItem} from 'reactstrap';
import {StyleSheet, css} from 'aphrodite';

import {getNavEntryDisplayData, getNavEntryType} from "../Common/utils";
import TagList from './TagList';
import {LIGHT_GREY, DARK_GREY} from "../Common/defaults";

/**
 * Check if nothing has been selected from the Nav.
 *
 * @param {Array} selected - The selected entries from the Nav.
 * Each Object in the Array has the entry's name & type.
 * @returns {boolean}
 * @private
 */
function nothingSelected(selected) {
  return selected.length === 0;
}

/**
 * Check if last selected entry is a testcase and if current entry
 * is its sibling.
 *
 * @param {Array} selected - The selected entries from the Nav.
 * Each Object in the Array has the entry's name & type.
 * @param {string} parentUid - The UID of the parent entry to the
 * "entries" Array.
 * @returns {boolean}
 * @private
 */
function testcaseSelected(selected, parentUid) {
  const lastSelected = selected[selected.length - 1];
  const secondLastSelected = selected[selected.length - 2];
  return (lastSelected.type === 'testcase' &&
          parentUid === secondLastSelected.uid);
}

/**
 * Check if current entry is a child of the last selected entry
 * and that the last selected entry isn't a testcase.
 *
 * @param {Array} selected - The selected entries from the Nav.
 * Each Object in the Array has the entry's name & type.
 * @param {string} parentUid - The UID of the parent entry to the
 * "entries" Array.
 * @returns {boolean}
 * @private
 */
function parentEntryLastSelected(selected, parentUid) {
  const lastSelected = selected[selected.length - 1];
  return (lastSelected.type !== 'testcase' &&
          parentUid === lastSelected.uid);
}

/**
 * Populate nav breadcrumbs & list Arrays depending on which entries were
 * selected from Nav.
 *
 * @param {Array} entries - Array of Testplan report entries.
 * @param {Array} selected - The selected entries from the Nav. Each Object in
 * the Array
 * has the entry's name & type.
 * @param {number} depth - The depth of the "entries" Array in the Testplan
 * report.
 * @param {string} parentUid - The UID of the parent entry to the "entries"
 * Array.
 * @returns {{navBreadcrumbs: Array, navList: Array}}
 * @private
 */
function parseNavSelection(entries, selected, depth, parentUid) {
  let navBreadcrumbs = [];
  let navList = [];
  for (const entry of entries) {
    const entryType = getNavEntryType(entry);

    // Populate:
    //   a. breadcrumbs from current entry and it's children
    //   b. list from current entry's children
    if (entryType !== 'testcase' &&
        depth < selected.length &&
        selected[depth].uid === entry.uid) {
      const breadcrumbEntryMetadata = getNavEntryDisplayData(entry);
      const nextSelection = parseNavSelection(
        entry.entries,
        selected,
        depth + 1,
        entry.uid
      );
      navBreadcrumbs.push(breadcrumbEntryMetadata);
      navBreadcrumbs.push(...nextSelection.navBreadcrumbs);
      navList = nextSelection.navList;
      break;
    }

    // Populate:
    //   a. list from current entry
    if (nothingSelected(selected) ||
        testcaseSelected(selected, parentUid) ||
        parentEntryLastSelected(selected, parentUid)) {
      let listEntryMetadata = getNavEntryDisplayData(entry);
      // Adding assertions to testcase data to be sent to AssertionPane.
      if (entryType === 'testcase') {
        listEntryMetadata.entries = entry.entries;
      }
      navList.push(listEntryMetadata);
    }
  }
  return {
    navBreadcrumbs: navBreadcrumbs,
    navList: navList
  };
}

/**
 * Populate nav breadcrumbs & list Arrays depending on which entries were
 * selected from Nav.
 *
 * @param {Array} entries - A single Testplan report in an Array.
 * @param {Array} selected - The selected entries from the Nav. Each Object in
 * the Array
 * has the entries name & type.
 * @returns {{navBreadcrumbs: Array, navList: Array}}
 */
function ParseNavSelection(entries, selected) {
  return parseNavSelection(entries, selected, 0, null);
}

/**
 * Handle Nav entries being clicked. Add/remove entries from selected Array
 * in state.
 *
 * NOTE: this function is intended to be mixed into a component which
 * binds "this". Currently this method is shared by the Nav and InteractiveNav
 * components.
 *
 * @param {Object} e - click event.
 * @param {Object} entry - Nav entry metadata.
 * @param {number} depth - depth of Nav entry in Testplan report.
 * @public
 */
function HandleNavClick (e, entry, depth) {
  e.stopPropagation();
  const entryType = getNavEntryType(entry);
  const selected = this.state.selected.slice(0, depth);
  selected.push({uid: entry.uid, type: entryType});
  this.setState({selected: selected});
  this.props.saveAssertions(entry);
}

/**
 * Create the list entry buttons or a single button stating nothing can be
 * displayed.
 *
 * @returns {Array|ListGroupItem}
 */
const CreateNavButtons = (props, createEntryComponent) => {
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

    return (
      <ListGroupItem
        tabIndex={tabIndex.toString()}
        key={entry.uid}
        className={css(styles.navButton, styles.navButtonInteract)}
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
      if (entry.type === 'TestCaseReport') {
        return (entry.entries !== null && entry.entries.length > 0);
      } else {
        return (entry.case_count.failed + entry.case_count.passed > 0);
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
        (entry) => entry.case_count.failed > 0
      );

    case 'fail':
      return entries.filter(
        (entry) => entry.case_count.failed === 0
      );

    default:
      return entries;
  }
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

export {
  ParseNavSelection,
  HandleNavClick,
  CreateNavButtons,
};
