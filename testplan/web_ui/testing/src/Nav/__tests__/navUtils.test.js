import React from "react";
import { StyleSheetTestUtils } from "aphrodite";

import {
  CreateNavButtons,
  GetSelectedUid,
  applyNamedFilter,
} from "../navUtils";
import { TESTPLAN_REPORT } from "../../Common/sampleReports";
import { PropagateIndices } from "../../Report/reportUtils";

describe("navUtils", () => {
  describe("CreateNavButtons", () => {
    beforeEach(() => {
      // Stop Aphrodite from injecting styles, this crashes the tests.
      StyleSheetTestUtils.suppressStyleInjection();
    });

    afterEach(() => {
      // Resume style injection once test is finished.
      StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    });

    const entries = PropagateIndices(TESTPLAN_REPORT).entries;

    it("returns an array of nav buttons", () => {
      const props = {
        breadcrumbLength: 1,
        displayTags: false,
        displayTime: false,
        displayEmpty: true,
        handleNavClick: jest.fn(),
        entries: entries,
        filter: null,
        url: "/testplan/:uid/:selection*",
      };
      const createEntryComponent = jest.fn();

      const navButtons = CreateNavButtons(props, createEntryComponent);
      expect(navButtons.length).toBe(props.entries.length);
      expect(navButtons).toMatchSnapshot();
    });
  });

  describe("GetSelectedUid", () => {
    it("gets the selected UID", () => {
      const selected = [TESTPLAN_REPORT];
      const uid = GetSelectedUid(selected);
      expect(uid).toBe(TESTPLAN_REPORT.uid);
    });
  });

  describe("FilterByStatus", () => {
    const entries = [
      {
        counter: { passed: 1, failed: 0, total: 1 },
        status: "passed",
      },
      {
        counter: { passed: 0, failed: 1, total: 1 },
        status: "failed",
      },
      {
        counter: { passed: 0, failed: 0, total: 1, error: 1 },
        status: "error",
      },
      {
        counter: { passed: 1, failed: 0, total: 1 },
        status: "passed",
        entries: [{ status: "xfail", entries: [] }],
      },
    ];

    it("returns empty list when filter array is empty", () => {
      expect(applyNamedFilter(entries, [])).toStrictEqual([]);
    });

    it("returns all entries when filter is null", () => {
      expect(applyNamedFilter(entries, null)).toStrictEqual(entries);
    });

    it("filters to failed and error entries", () => {
      const result = applyNamedFilter(entries, ["failed", "error"]);
      expect(result).toStrictEqual([entries[1], entries[2]]);
    });

    it("filters to passed entries", () => {
      const result = applyNamedFilter(entries, ["passed"]);
      expect(result).toStrictEqual([entries[0], entries[3]]);
    });

    it("shows parent entry when a descendant matches the filter", () => {
      const result = applyNamedFilter(entries, ["xfail"]);
      expect(result).toStrictEqual([entries[3]]);
    });
  });
});
