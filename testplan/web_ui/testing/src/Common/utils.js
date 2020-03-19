/**
 * Common utility functions.
 */
import {NAV_ENTRY_DISPLAY_DATA} from "./defaults";

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
  getNavEntryDisplayData,
  any,
  sorted,
  uniqueId,
  hashCode,
  domToString,
};

/**
 * Callback which takes one argument.
 * @template T
 * @callback Callback1Arg<T>
 * @param {T} arg1
 *//**
 * Callback which takes no arguments.
 * @callback Callback0Arg
 *//**
 * Functional version of `try { ... } catch(err) { ... }`.
 * @param {Callback0Arg} tryFunc0Args -
 *     Will be run as `try { tryFunc0Args(); } ...`
 * @param {Callback1Arg<Error>=} catchFunc1Arg -
 *     Will be run as `.. catch(err) { catchFunc1Arg(err); }`
 * @returns {undefined}
 */
export function tryCatch(tryFunc0Args, catchFunc1Arg = () => undefined) {
  try { return tryFunc0Args(); }
  catch(e) { return catchFunc1Arg(e); }
}

/**
 * @class
 * @extends URLSearchParams
 * @classdesc
 * Subclass of `URLSearchParams` that parses all query params as JSON upon
 * instantiation and adds some convenience methods.
 * @example
 * const pqp = new ParsedQueryParams('?a=1&b=true&c=%7B"x"%3A+true%7D');
 * pqp.get('c') === {"x": true}
 * pqp.get('d', 'HEY') === "HEY"
 * pqp.firstOf(['q', 'b']) === true
 */
export class ParsedQueryParams extends URLSearchParams {
  /** @param {string} queryString */
  constructor(queryString) {
    const parsedValEntries = [];
    for(const [key, val] of new URLSearchParams(queryString)) {
      parsedValEntries.push([
        key, tryCatch(() => JSON.parse(val)) || val
      ]);
    }
    // we do this last since `URLSearchParams.set` eliminates duplicates
    // (which we may want to preserve)
    super(parsedValEntries);
  }
  get = (key, defaultVal = null) => super.get(key) || defaultVal;
  getAll(key, defaultVal = null) {
    const tudo = super.getAll(key);
    return tudo.length ? tudo : defaultVal;
  }
  /**
   * Try all keys, falling back to `defaultVal` if none are present
   * @param {Array<string>} keys - Keys to try in sequence
   * @param {*} [defaultVal=null] - Return value of none of `keys` are present
   * @returns {*}
   */
  firstOf(keys, defaultVal = null) {
    if(!Array.isArray(keys)) return this.get(keys, defaultVal);
    for(const key of keys) {
      if(this.has(key))
        return this.getAll(key).slice(0)[0] || defaultVal;
    }
    return defaultVal;
  }
}
