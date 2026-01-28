/**
 * Report utility functions.
 */
import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import { TZDate } from "@date-fns/tz";
import _ from "lodash";
import axios from "axios";
import AssertionPane from "../AssertionPane/AssertionPane";
import ResourcePanel from "../AssertionPane/ResourcePanel";
import Message from "../Common/Message";
import {
  formatMilliseconds,
  getAttachmentUrl,
  getAssertionsFileName,
} from "./../Common/utils";
import { VIEW_TYPE } from "../Common/defaults";
import { parseToJson } from "../Common/utils";
import { filterEntries } from "./reportFilter";

/**
 * Test if a given report entry is a leaf node, i.e. there is no report entry
 * among its children.
 *
 * While there is no type attribute on TestGroupReport shallow objects,
 * undefined !== "TestCaseReport" will still make it work here.
 *
 * @param {Object} entry - Report entry to be tested.
 * @returns {Boolean} - true if it is such leaf node.
 */
const isReportLeaf = (entry) => entry.type === "TestCaseReport";

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
        let tagsSet = _.uniq(tagsArray);
        mergedTags[tagName] = [...tagsSet];
      } else {
        mergedTags[tagName] = tags;
      }
    }
  }
  return mergedTags;
}

/**
 * Merge counters from multiple report entries.
 *
 * @param {Array} parts - Array of report entries to merge counters from.
 * @returns {Object} - Merged counter object.
 * @private
 */
const _mergeCounters = (parts) => {
  return parts.reduce(
    (acc, part) => ({
      passed: acc.passed + (part.counter.passed),
      failed: acc.failed + (part.counter.failed),
      total: acc.total + (part.counter.total),
      error: acc.error + (part.counter.error || 0),
    }),
    { passed: 0, failed: 0, total: 0, error: 0 }
  );
};

/**
 * Compute combined status from multiple report entries.
 * Priority: error > failed > passed > unknown
 *
 * @param {Array} parts - Array of report entries.
 * @returns {string} - Combined status.
 * @private
 */
const _mergeStatus = (parts) => {
  const statuses = parts.map((p) => p.status);
  if (statuses.includes("error")) return "error";
  if (statuses.includes("failed")) return "failed";
  if (statuses.includes("passed")) return "passed";
  return "unknown";
};

/**
 * Build common merged fields from a group of entries.
 *
 * @param {Array} group - Array of entries to merge.
 * @returns {Object} - Common merged fields.
 * @private
 */
const _mergeCommonFields = (group) => ({
  counter: _mergeCounters(group),
  timer: null,
  status: _mergeStatus(group),
  status_override:
    group.find((e) => e.status_override)?.status_override ?? null,
  tags: group.reduce((acc, e) => _mergeTags(acc, e.tags || {}), {}),
  logs: group.flatMap((e) => e.logs || []),
  _allPartUids: [
    ...new Set(
      group.flatMap((e) => (e._allPartUids ? e._allPartUids : [e.uid]))
    ),
  ],
});

/**
 * Flatten a report entry tree into a pre-order list.
 * Each entry is annotated with _parentPath (array of ancestor definition_names).
 * Synthesized entries are skipped.
 *
 * @param {Object} entry - The entry to flatten.
 * @param {Array} parentPath - Path of ancestor definition_names.
 * @returns {Array} - Flattened array of entries with _parentPath.
 * @private
 */
const _preOrderFlatten = (entry, parentPath = []) => {
  if (entry.category === "synthesized") return [];

  const annotated = { ...entry, _parentPath: parentPath };
  const result = [annotated];

  const currentPath = [...parentPath, entry.definition_name];
  for (const child of entry.entries || []) {
    result.push(..._preOrderFlatten(child, currentPath));
  }

  annotated.entries = [];
  return result;
};

/**
 * Find the parent node in the merged tree using parentPath.
 * Since we process entries in pre-order, parents are always added before children.
 *
 * @param {Object} root - The root of the merged tree.
 * @param {Array} parentPath - Array of ancestor definition_names.
 * @returns {Object} - The parent node where the entry should be added.
 * @private
 */
const _findParent = (root, parentPath) => {
  let current = root;
  for (const defName of parentPath) {
    current = current.entries.find((e) => e.definition_name === defName);
  }
  return current;
};

/**
 * Add an entry to the merged tree, creating parent structure as needed.
 * If a structure entry (suite/parametrization) already exists, merge metadata.
 * If a test case, always append.
 *
 * @param {Object} root - The root of the merged tree.
 * @param {Object} entry - The entry to add (with _parentPath).
 * @private
 */
const _addEntryToMerged = (root, entry) => {
  const parentPath = entry._parentPath || [];
  const parent = _findParent(root, parentPath);
  const { _parentPath, ...cleanEntry } = entry;

  if (isReportLeaf(entry)) {
    parent.entries.push(cleanEntry);
  } else {
    const existing = parent.entries.find(
      (e) => e.definition_name === entry.definition_name
    );
    if (existing) {
      Object.assign(existing, _mergeCommonFields([existing, entry]));
    } else {
      parent.entries.push({ ...cleanEntry, entries: [] });
    }
  }
};

/**
 * Recursively tag all entries with their source multitest UID.
 * This is needed so test cases know which assertion file to look in.
 *
 * @param {Array} entries - Array of entries to tag.
 * @param {string} sourceMultitestUid - The UID of the source multitest.
 * @private
 */
const _tagEntriesWithSource = (entries, sourceMultitestUid) => {
  if (!entries) return;
  for (const entry of entries) {
    entry._sourceMultitestUid = sourceMultitestUid;
    if (entry.entries && entry.entries.length > 0) {
      _tagEntriesWithSource(entry.entries, sourceMultitestUid);
    }
  }
};

/**
 * Merge multiple multitest parts into a single entry.
 * Uses round-robin insertion: process each part until a testcase is inserted,
 * then move to the next part. This preserves correct test case ordering.
 *
 * @param {string} baseName - The base name (definition_name) for the merged entry.
 * @param {Array} parts - Array of part entries to merge.
 * @returns {Object} - Merged multitest entry.
 * @private
 */
const _mergeParts = (baseName, parts) => {
  const sortedParts = _.sortBy(parts, (p) => p.part[0]);
  const first = sortedParts[0];

  for (const part of sortedParts) {
    _tagEntriesWithSource(part.entries, part.uid);
  }

  const flattenedParts = sortedParts.map((part) =>
    part.entries.flatMap((child) => _preOrderFlatten(child))
  );

  // [0, 0, 0...] for each part
  const pointers = sortedParts.map(() => 0);

  const merged = {
    ...first,
    name: baseName,
    part: null,
    entries: [],
    ..._mergeCommonFields(sortedParts),
  };

  const hasMoreEntries = () =>
    pointers.some((cursor, i) => cursor < flattenedParts[i].length);

  while (hasMoreEntries()) {
    for (let partIdx = 0; partIdx < sortedParts.length; partIdx++) {
      const flat = flattenedParts[partIdx];

      while (pointers[partIdx] < flat.length) {
        const entry = flat[pointers[partIdx]];
        pointers[partIdx]++;

        _addEntryToMerged(merged, entry);

        if (isReportLeaf(entry)) {
          break;
        }
      }
    }
  }

  return merged;
};

/**
 * Merge multitest parts that share the same definition_name.
 * Parts are identified by having a non-null `part` field (e.g., [0, 2]).
 * Synthesized entries are discarded during merge.
 *
 * @param {Array} entries - Array of report entries at the same level.
 * @returns {Array} - Entries with parts merged.
 * @private
 */
const mergeMultitestParts = (entries) => {
  if (!entries || entries.length === 0) return entries;

  const partGroups = {};
  const result = [];

  for (const entry of entries) {
    if (Array.isArray(entry.part)) {
      const key = entry.definition_name;
      if (!partGroups[key]) {
        partGroups[key] = { index: result.length, entries: [] };
        result.push(null);
      }
      partGroups[key].entries.push(entry);
    } else {
      result.push(entry);
    }
  }

  for (const [baseName, { index, entries: group }] of
    Object.entries(partGroups)) {
    const merged = _mergeParts(baseName, group);
    result[index] = merged;
  }

  return result;
};

/**
 * Merge assertions and structure into main report.
 *
 * @param {Object} mainReport - Main report with meta data.
 * @param {Object} assertions - An object which contains all assertions.
 * @param {Array} structure - Report structure.
 * @returns {Object} - Merged report.
 * @private
 */
const MergeSplittedReport = (mainReport, assertions, structure) => {
  const _mergeStructure = (_structure, _assertions) => {
    _structure.forEach((element) => {
      if (isReportLeaf(element)) {
        element.entries = _assertions[element.uid] || [];
      } else {
        _mergeStructure(element.entries, _assertions);
      }
    });
  };
  if (assertions) {
    _mergeStructure(structure, assertions);
  }
  mainReport.entries = structure;
  return mainReport;
};

/**
 * Update uids to reflect merged tree structure while preserving originals.
 * Stores current uids as _originalUids, then sets new uids based on parent path.
 * The new uids field is for tree view node structure
 * the _originalUids is for url generation in the node
 *
 * @param {Array} entries - Array of report entries.
 * @param {Array} parentUids - Parent's uid path.
 * @private
 */
const _updateUidsForMergedTree = (entries, parentUids) => {
  if (!entries) return;
  for (const entry of entries) {
    if (entry.uids) {
      entry._originalUids = entry.uids;
    }
    entry.uids = [...parentUids, entry.uid];
    if (entry.entries) {
      _updateUidsForMergedTree(entry.entries, entry.uids);
    }
  }
};

/**
 * Apply multitest parts merging to a report.
 * Creates a deep copy to avoid mutating the original.
 * Updates uids after merging so tree structure is consistent.
 *
 * @param {Object} report - The report to process.
 * @returns {Object} - Report with merged multitest parts.
 */
const applyPartsMerge = (report) => {
  if (!report) return report;
  const cloned = _.cloneDeep(report);
  cloned.entries = mergeMultitestParts(cloned.entries);
  _updateUidsForMergedTree(cloned.entries, [cloned.uid]);
  return cloned;
};

/**
 * Propagate indices through report to be utilised by filter box. A single entry
 * will contain:
 *   * tags - its & its ancestors tags.
 *   * tags_index - its, its ancestors & its descendents tags.
 *   * name_type_index - its, its ancestors & its descendents names & types.
 *   * uids - the entity uids from root to this entity
 *
 * @param {Array} entries - Array of Testplan report entries.
 * @param {Object|undefined} parentIndices - An entry's parent's tags_index &
 * name_type_index.
 * @returns {Object} - The indices for all of the entries in the "entries"
 * Array.
 * @private
 */
const propagateIndicesRecur = (entries, parentIndices) => {
  if (parentIndices === undefined) {
    parentIndices = {
      tags_index: {},
      name_type_index: [],
      uids: [],
    };
  }
  let indices = {
    tags_index: {},
    name_type_index: [],
  };

  for (let entry of entries) {
    let entryType = entry.category;
    // Initialize indices.
    let tagsIndex = {};
    const entryNameType = entry.name + "|" + entryType;
    let nameTypeIndex = _.uniq([
      entryNameType,
      ...parentIndices.name_type_index,
    ]);

    let tags = parentIndices.tags_index;
    if (entry.hasOwnProperty("tags")) {
      entry.tags = _mergeTags(entry.tags, parentIndices.tags_index);
      tags = entry.tags;
    }

    const uids = [...parentIndices.uids, entry.uid];
    if (!isReportLeaf(entry)) {
      // Propagate indices to children.
      let descendantsIndices = propagateIndicesRecur(entry.entries, {
        tags_index: tags,
        name_type_index: nameTypeIndex,
        uids,
      });
      tagsIndex = _mergeTags(tagsIndex, descendantsIndices.tags_index);
      nameTypeIndex = _.uniq([
        ...nameTypeIndex,
        ...descendantsIndices.name_type_index,
      ]);
    }

    // Set entry's indices.
    tagsIndex = _mergeTags(tagsIndex, tags);
    entry.tags_index = tagsIndex;
    entry.name_type_index = nameTypeIndex;
    entry.uids = uids;

    // Update Array of entries indices.
    indices.tags_index = _mergeTags(indices.tags_index, tagsIndex);
    indices.name_type_index = _.uniq([
      ...indices.name_type_index,
      ...nameTypeIndex,
    ]);
  }
  return indices;
};

/**
 * Propagate indices through report to be utilised by filter box. A single entry
 * will contain:
 *   * tags - its & its ancestors tags.
 *   * tags_index - its, its ancestors & its descendents tags.
 *   * name_type_index - its, its ancestors & its descendents names & types.
 *   * uids - the entity uids from root to this entity
 *
 * @param {Array} entries - A single Testplan report in an Array.
 * @returns {Array} - The Testplan report with indices, in an Array.
 */
const PropagateIndices = (report) => {
  propagateIndicesRecur([report], undefined);
  return report;
};

/**
 * Get the current report data, status and fetch message as required.
 */
const GetReportState = (state) => {
  // Handle the Testplan report if it has been fetched.
  if (!state.report) {
    // The Testplan report hasn't been fetched yet.
    return {
      reportStatus: null,
      reportFetchMessage: getReportFetchMessage(state),
    };
  } else {
    // The Testplan report has been fetched.
    return {
      reportStatus: state.report.status,
      reportFetchMessage: null,
    };
  }
};

// TODO: use TanStack Query
let assertionsCache = {};

/**
 * Get the component to display in the centre pane.
 */
const CenterPane = ({
  reportState,
  reportFetchMessage,
  reportUid,
  selectedEntries,
  displayTime,
  UTCTime,
}) => {
  const [assertions, setAssertions] = useState(null);
  const selectedEntry = _.last(selectedEntries);
  useEffect(() => {
    if (selectedEntries.length === 0 || reportFetchMessage) {
      return;
    }

    if (assertions === null) {
      if (
        selectedEntry.entries.length === 0 &&
        selectedEntry.counter.total > 0 &&
        reportUid !== null &&
        selectedEntries.length > 1
      ) {
        // version 3 report structure
        // Use _sourceMultitestUid if available (merged multitest parts)
        const multitestUid =
          selectedEntry._sourceMultitestUid || selectedEntries[1].uid;
        const assertionFileName = getAssertionsFileName(multitestUid);
        if (assertionsCache.hasOwnProperty(assertionFileName)) {
          const _assertions = getAssertions(
            selectedEntries,
            assertionsCache[assertionFileName][selectedEntry.uid],
            displayTime,
            UTCTime
          );
          setAssertions(_assertions);
        } else {
          const fetchUrl = getAttachmentUrl(assertionFileName, reportUid);
          axios
            .get(fetchUrl, { transformResponse: parseToJson })
            .then((response) => {
              const _assertions = getAssertions(
                selectedEntries,
                response.data[selectedEntry.uid],
                displayTime,
                UTCTime
              );

              // TODO: Improve caching strategy. Currently only one assertion file is cached.
              assertionsCache = {
                [assertionFileName]: response.data,
              };
              setAssertions(_assertions);
            })
            .catch((error) => {
              console.error("Error fetching assertions:", error);
              setAssertions([]);
            });
        }
      } else {
        // version 1&2 report structure
        const _assertions = getAssertions(
          selectedEntries,
          _.last(selectedEntries).entries,
          displayTime,
          UTCTime
        );
        setAssertions(_assertions);
      }
    }
  }, [
    selectedEntry,
    reportFetchMessage,
    reportUid,
    selectedEntries,
    displayTime,
    UTCTime,
    assertions,
  ]);

  const logs = selectedEntry?.logs || [];
  const selectedDescription = selectedEntries
    .slice(-1)
    .map((element) => {
      return element.description;
    })
    .filter((element) => {
      return element; // filter empty description
    });

  if (reportState.error) {
    return <Message message={`Error: ${reportState.error.message}`} />;
  }

  if (reportFetchMessage !== null) {
    return <Message message={reportFetchMessage} />;
  }

  if (reportState.currentPanelView === VIEW_TYPE.RESOURCE) {
    return <ResourcePanel key="resourcePanel" report={reportState.report} />;
  }

  if (assertions === null && reportUid !== null) {
    return <Message message="Loading assertions" />;
  }

  if (
    (assertions !== null && assertions.length > 0) ||
    logs.length > 0 ||
    selectedDescription.length > 0
  ) {
    return (
      <AssertionPane
        key={selectedEntry ? selectedEntry.hash || selectedEntry.uid : null}
        assertions={assertions || []}
        logs={logs}
        descriptionEntries={selectedDescription}
        left={reportState.navWidth}
        testcaseUid={selectedEntry.uid}
        filter={reportState.filter}
        displayPath={reportState.displayPath}
        reportUid={reportUid}
      />
    );
  }
  if (selectedEntry && selectedEntry.entries.length > 0) {
    return <Message message="Please select an entry." />;
  } else {
    return <Message message="No entries to be displayed." />;
  }
};

/** TODO */
const getAssertions = (selectedEntries, assertions, displayTime, UTCTime) => {
  // get timezone from nearest (test-level) report (defaults to utc)
  const IANAtz = selectedEntries.find((e) => e.timezone)?.timezone || "UTC";

  // get all assertions from groups and list them sequentially in an array
  const getAssertionsRecursively = (links, entries) => {
    for (let i = 0; i < entries.length; ++i) {
      if (entries[i].type === "Group") {
        getAssertionsRecursively(links, entries[i].entries);
      } else {
        links.push(entries[i]);
      }
    }
  };

  const createTimeInfoString = (entry, UTCTime) => {
    // new entry structure
    if (entry.timestamp) {
      let d = new TZDate(entry.timestamp * 1000, IANAtz);
      return UTCTime
        ? format(d.withTimeZone("UTC"), "HH:mm:ss.SSSXXX")
        : format(d, "HH:mm:ss.SSSxxx");
    }

    // old entry structure
    let timestamp = UTCTime ? entry.utc_time : entry.machine_time;
    if (!timestamp) {
      return "";
    }
    let label = UTCTime ? "Z" : timestamp.substring(26, 32);
    timestamp = timestamp.substring(0, 26);
    return format(new Date(timestamp), "HH:mm:ss.SSS") + label;
  };

  const getTimeDelta = (prevEntry, currentEntry) => {
    if (prevEntry.utc_time && currentEntry.utc_time) {
      const previousEntryTime = new Date(prevEntry.utc_time).getTime();
      const currentEntryTime = new Date(currentEntry.utc_time).getTime();
      return formatMilliseconds(currentEntryTime - previousEntryTime);
    } else if (prevEntry.timestamp && currentEntry.timestamp) {
      return formatMilliseconds(
        (currentEntry.timestamp - prevEntry.timestamp) * 1000
      );
    }
    return "Unknown";
  };

  const selectedEntry = selectedEntries[selectedEntries.length - 1];
  if (selectedEntry && isReportLeaf(selectedEntry)) {
    let links = [];
    getAssertionsRecursively(links, assertions);

    // get time information of each assertion if needed
    if (displayTime) {
      // add time information to the array in a human readable format
      for (let i = 0; i < links.length; ++i) {
        // links[i].timeInfoArray = [index, start_time, duration]
        links[i].timeInfoArray = [i, createTimeInfoString(links[i], UTCTime)];
      }
      // calculate the time elapsed between assertions
      for (let i = links.length - 1; i > 0; --i) {
        let duration = `(+${getTimeDelta(links[i - 1], links[i])})`;
        links[i].timeInfoArray.push(duration);
      }
      if (links.length > 0) {
        let duration = "Unknown";
        if (selectedEntry.timer && selectedEntry.timer.run) {
          if (links[0].utc_time) {
            const previousEntryTime = new Date(
              selectedEntry.timer.run.at(-1).start
            );
            const currentEntryTime = new Date(links[0].utc_time);
            duration = formatMilliseconds(currentEntryTime - previousEntryTime);
          } else if (links[0].timestamp) {
            const previousEntryTime = selectedEntry.timer.run.at(-1).start;
            const currentEntryTime = links[0].timestamp;
            duration = formatMilliseconds(
              (currentEntryTime - previousEntryTime) * 1000
            );
          }
        }
        duration = "(+" + duration + ")";
        links[0].timeInfoArray.push(duration);
      }
    } else {
      for (let i = 0; i < links.length; ++i) {
        links[i].timeInfoArray = [];
      }
    }
    return assertions;
  } else {
    return [];
  }
};

/**
 * Get a message relating to the progress of fetching the testplan report.
 */
const getReportFetchMessage = (state) => {
  if (state.loading) {
    return "Fetching Testplan report...";
  } else {
    return "Waiting to fetch Testplan report...";
  }
};

/**
 * Get the selected entries in the report, from their UIDs.
 */
const GetSelectedEntries = (selectedUIDs, report) => {
  const [headSelectedUID, ...tailSelectedUIDs] = selectedUIDs;
  if (!headSelectedUID || !report) {
    return [];
  }

  if (tailSelectedUIDs.length > 0) {
    const targetUid = tailSelectedUIDs[0];
    const childEntry = report.entries.find(
      (entry) =>
        entry.uid === targetUid ||
        (entry._allPartUids && entry._allPartUids.includes(targetUid))
    );
    return [report, ...GetSelectedEntries(tailSelectedUIDs, childEntry)];
  } else {
    return [report];
  }
};

/**
 * Auto-select the first failed entry in the report when it is first loaded.
 * @param {reportNode} reportEntry - the current report entry to select from.
 * @return {Array[string]} List of UIDs of the currently selected entries.
 */
const findFirstFailure = (reportEntry) => {
  if (isReportLeaf(reportEntry) || reportEntry.entries.length === 0) {
    return [reportEntry.uid];
  } else {
    for (let entry in reportEntry.entries) {
      if (
        reportEntry.entries[entry].status === "failed" ||
        reportEntry.entries[entry].status === "error"
      ) {
        return [reportEntry.uid].concat(
          findFirstFailure(reportEntry.entries[entry])
        );
      }
    }
  }
};

const filterReport = (report, filter) => {
  if (filter.filters === null) {
    return { filter, report };
  }

  return {
    filter,
    report: {
      ...report,
      entries: filterEntries(report.entries, filter.filters),
    },
  };
};

const isValidSelection = (selection, entry) => {
  if (selection.length === 0) return true;

  const next_element = _.find(
    entry.entries,
    (entry) => entry.uid === _.head(selection)
  );
  return next_element
    ? isValidSelection(_.tail(selection), next_element)
    : false;
};

const getSelectedUIDsFromPath = ({ uid, selection }, uidDecoder) => {
  const uids = [uid, ...(selection ? selection.split("/") : [])];
  return uidDecoder ? uids.map((uid) => (uid ? uidDecoder(uid) : uid)) : uids;
};

export {
  isReportLeaf,
  PropagateIndices,
  GetReportState,
  CenterPane,
  GetSelectedEntries,
  MergeSplittedReport,
  findFirstFailure,
  filterReport,
  isValidSelection,
  getSelectedUIDsFromPath,
  applyPartsMerge,
};
