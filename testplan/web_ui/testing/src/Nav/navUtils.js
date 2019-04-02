/**
 * Navigation utility functions.
 */
import {getNavEntryDisplayData, getNavEntryType} from "../Common/utils";

/**
 * Check if nothing has been selected from the Nav.
 *
 * @param {Array} selected - The selected entries from the Nav.
 * Each Object in the Array has the entry's name & type.
 * @returns {boolean}
 * @private
 */
function _nothingSelected(selected) {
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
function _testcaseSelected(selected, parentUid) {
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
function _parentEntryLastSelected(selected, parentUid) {
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
function _parseNavSelection(entries, selected, depth, parentUid) {
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
      const nextSelection = _parseNavSelection(
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
    if (_nothingSelected(selected) ||
        _testcaseSelected(selected, parentUid) ||
        _parentEntryLastSelected(selected, parentUid)) {
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
function parseNavSelection(entries, selected) {
  return _parseNavSelection(entries, selected, 0, undefined);
}

export {
  parseNavSelection,
};