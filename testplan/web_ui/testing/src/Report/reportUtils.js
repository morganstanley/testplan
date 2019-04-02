/**
 * Report utility functions.
 */
import {getNavEntryType} from "../Common/utils";

/**
 * Merge two tag objects into a single tag object.
 *
 * @param {Object} tagsA - first tag object, contains simple & named tags.
 * @param {Object} tagsB - second tag object, contains simple & named tags.
 * @returns {Object} - merged tag object.
 * @private
 */
function _mergeTags(tagsA, tagsB) {
  // Don't edit one of the objects in place, copy to new object.
  let mergedTags = {};
  for (const tagName in tagsA) {
    if (tagsA.hasOwnProperty(tagName)) {
      mergedTags[tagName] = tagsA[tagName];
    }
  }

  // Merge object B into object A.
  for (const tagName in tagsB) {
    if (tagsB.hasOwnProperty(tagName)) {
      const tags = tagsB[tagName];
      if (tagsA.hasOwnProperty(tagName)) {
        let tagsArray = tags.concat(tagsA[tagName]);
        let tagsSet = new Set(tagsArray);
        mergedTags[tagName] = [...tagsSet];
      } else {
        mergedTags[tagName] = tags;
      }
    }
  }
  return mergedTags;
}

/**
 * Propagate indices through report to be utilised by filter box. A single entry
 * will contain:
 *   * tags - its & its ancestors tags.
 *   * tags_index - its, its ancestors & its descendents tags.
 *   * name_type_index - its, its ancestors & its descendents names & types.
 *   * case_count - number of passing & failing descendent testcases.
 *
 * @param {Array} entries - Array of Testplan report entries.
 * @param {Object|undefined} parentIndices - An entry's parent's tags_index &
 * name_type_index.
 * @returns {Object} - The indices for all of the entries in the "entries"
 * Array.
 * @private
 */
function _propagateIndices(entries, parentIndices) {
  if (parentIndices === undefined) {
    parentIndices = {
      tags_index: {},
      name_type_index: new Set(),
    };
  }
  let indices = {
    tags_index: {},
    name_type_index: new Set(),
    case_count: {
      passed: 0,
      failed: 0,
    },
  };

  for (let entry of entries) {
    let entryType = getNavEntryType(entry);
    // Initialize indices.
    let tagsIndex = {};
    const entryNameType = entry.name + '|' + entryType;
    let nameTypeIndex = new Set([
      entryNameType,
      ...parentIndices.name_type_index
    ]);
    let caseCount = {passed: 0, failed: 0};

    let tags = parentIndices.tags_index;
    if (entry.hasOwnProperty('tags')) {
      entry.tags = _mergeTags(entry.tags, parentIndices.tags_index);
      tags = entry.tags;
    }

    if (entryType !== 'testcase') {
      // Propagate indices to children.
      let descendantsIndices = _propagateIndices(
        entry.entries,
        {tags_index: tags, name_type_index: nameTypeIndex}
      );
      tagsIndex = _mergeTags(tagsIndex, descendantsIndices.tags_index);
      nameTypeIndex = new Set([
        ...nameTypeIndex,
        ...descendantsIndices.name_type_index
      ]);
      caseCount.passed += descendantsIndices.case_count.passed;
      caseCount.failed += descendantsIndices.case_count.failed;
    } else {
      // Count testcase's status.
      caseCount.passed += entry.status === 'passed';
      caseCount.failed += entry.status === 'failed';
    }

    // Set entry's indices.
    tagsIndex = _mergeTags(tagsIndex, tags);
    entry.tags_index = tagsIndex;
    entry.name_type_index = nameTypeIndex;
    entry.case_count = caseCount;

    // Update Array of entries indices.
    indices.tags_index = _mergeTags(indices.tags_index, tagsIndex);
    indices.name_type_index = new Set([
      ...indices.name_type_index,
      ...nameTypeIndex
    ]);
    indices.case_count.passed += caseCount.passed;
    indices.case_count.failed += caseCount.failed;
  }
  return indices;
}

/**
 * Propagate indices through report to be utilised by filter box. A single entry
 * will contain:
 *   * tags - its & its ancestors tags.
 *   * tags_index - its, its ancestors & its descendents tags.
 *   * name_type_index - its, its ancestors & its descendents names & types.
 *   * case_count - number of passing & failing descendent testcases.
 *
 * @param {Array} entries - A single Testplan report in an Array.
 * @returns {Array} - The Testplan report with indices, in an Array.
 */
function propagateIndices(entries) {
  _propagateIndices(entries, undefined);
  return entries;
}

export {
  propagateIndices,
};