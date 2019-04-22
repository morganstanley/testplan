/**
 * Common utility functions.
 */
import {NAV_ENTRY_DISPLAY_DATA} from "./defaults";

/**
 * Get the nav entry type.
 *
 * @param {Object} entry - nav entry.
 * @returns {string|undefined}
 */
function getNavEntryType(entry) {
  if (entry.hasOwnProperty('type')) {
    if (entry.type === 'TestGroupReport') {
      return entry.category;
    } else if (entry.type === 'TestCaseReport') {
      return 'testcase';
    } else {
      return undefined;
    }
  } else {
    return 'testplan';
  }
}

/**
 * Get the data to be used when displaying the nav entry.
 *
 * @param {object} entry - nav entry.
 * @returns {Object}
 */
function getNavEntryDisplayData(entry) {
  let metadata = {};
  for (const attribute of NAV_ENTRY_DISPLAY_DATA) {
    if (entry.hasOwnProperty(attribute)) {
      metadata[attribute] = entry[attribute];
    }
  }
  return metadata;
}

/**
 * Returns true of any element of an iterable is true. If not, returns false.
 *
 * @param iterable
 * @returns {boolean}
 */
function any(iterable) {
  for (let index = 0; index < iterable.length; ++index) {
    if (iterable[index]) return true;
  }

  return false;
}

/**
 * Returns a sorted array of the given iterable.
 *
 * @param iterable
 * @param {function} key - function that serves as a key for the sort comparison
 * @param {boolean} reverse - if true, the sorted list is reversed
 * @returns {Array}
 */
function sorted(iterable, key=(item) => (item), reverse=false) {
  return iterable.sort((firstMember, secondMember) => {
    let reverser = reverse ? 1 : -1;

    return ((key(firstMember) < key(secondMember))
      ? reverser
      : ((key(firstMember) > key(secondMember))
        ? (reverser * -1)
        : 0));
  });
}

/**
 * Creates a string that can be used for dynamic id attributes
 * Example: "id-so7567s1pcpojemi"
 * @returns {string}
 */
function uniqueId() {
  return 'id-' + Math.random().toString(36).substr(2, 16);
}

/** 
 * Generate a hash code by string
 * @param {string} str - string that generate hash code
 * @returns {number}
 */
function hashCode(str) {
  var hash = 0, i, chr, len;
  if (str.length === 0) return hash;
  for (i = 0, len = str.length; i < len; i++) {
    chr = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
}

/**
 * Get the string representation of a HTML DOM node
 * @param {object} dom - HTML DOM node
 * @returns {string}
 */
function domToString(dom) {
  let tmp = document.createElement("div");
  tmp.appendChild(dom);
  return tmp.innerHTML;
}

export {
  getNavEntryType,
  getNavEntryDisplayData,
  any,
  sorted,
  uniqueId,
  hashCode,
  domToString,
};