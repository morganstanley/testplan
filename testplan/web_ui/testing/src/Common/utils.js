/**
 * Common utility functions.
 */
import {NAV_ENTRY_DISPLAY_DATA} from "./defaults";
import _ from 'lodash';

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
 * Reverses a Map.
 * @template T, U
 * @param {Map<T, U>} aMap - The map to reverse
 * @returns {Map<U, T>}
 */
export const reverseMap = aMap => new Map(
  Array.from(aMap).map(([newVal, newKey]) => [ newKey, newVal ])
);

export const isNonemptyArray = x => Array.isArray(x) && x.length;

export const unindent = (strArr, ...tagsArr) => strArr.slice(1).reduce(
  (acc, str, i) => {
    return `${acc}${`${tagsArr[i]}${str}`.replace(/^\s+/mg, '')}`;
  },
  strArr[0]
).trimLeft();

export const flattened = (strArr, ...tagsArr) => {
  return _.spread(unindent)([ strArr, ...tagsArr ])
    .replace(/[ \t]*\n/g, ' ')
    .trimRight();
};

/**
 * The difference between this and lodash.toPlainObject is that this also
 * plain-objectifies the object's prototype.too. The _...*In*_ suffix follows
 * the lodash naming scheme where the non-_...*In*_ function acts only on own
 * properties and the _...*In*_ acts on own and inherited properties.
 *
 * Only values meeting the redux definition of "plain" types will be returned,
 * e.g. the result shallowly omits functions and `symbol`'s.
 *
 * @example

 > const err = new Error('oops');
 > const errObjRepr = { name: 'Error', message: 'oops', stack: 'Uncaught Error: oops...' };
 > require('lodash').isEqual(toPlainObjectIn(err), errObjRepr);  // i.e. deep equals
 true

 * @param {object} obj
 * @param {boolean} [enumerableOnly=false] - whether or not to skip
 *     non-enumerable properties like Lodash does.
 * @returns {Object.<string, string | undefined | null | number | boolean | any[] | object>}
 */
export const toPlainObjectIn = (obj, enumerableOnly = false) => {
  const objectify = o => {
    return Object.fromEntries(Object.entries(o)
      .filter(([_, v]) => _.isPlainObject(v.value))
      .filter(([_, v]) => !enumerableOnly || v.enumerable)
      .map(([k, v]) => [k, v.value])
    );
  };
  const ownDescriptors = Object.getOwnPropertyDescriptors(obj);
  const ownProps = objectify(ownDescriptors);
  const proto = Object.getPrototypeOf(obj);
  const protoDescriptors = Object.getOwnPropertyDescriptors(proto);
  const inheritedProps = objectify(protoDescriptors);
  return { ...inheritedProps, ...ownProps };
};

export const joinURLComponent = (base, component) => {
  return `${base.replace(/\/+$/, '').trim()}/${component}`;
};
