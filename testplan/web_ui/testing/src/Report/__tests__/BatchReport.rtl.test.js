import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { StyleSheetTestUtils } from "aphrodite";
import { MemoryRouter, Route, useLocation } from "react-router-dom";
import moxios from "moxios";
import _ from "lodash";

import BatchReport from "../BatchReport";
import {
  MULTITEST_PARTS_REPORT,
} from "../../Common/sampleReports";

const renderBatchReport = (uid, selection = undefined, props = {}) => {
  const initialPath = selection
    ? `/testplan/${uid}/${selection}`
    : `/testplan/${uid}`;

  const locationRef = { current: null };

  const LocationCapture = () => {
    locationRef.current = useLocation();
    return null;
  };

  const result = render(
    <MemoryRouter initialEntries={[initialPath]}>
      <LocationCapture />
      <Route
        path="/testplan/:uid/:selection*"
        render={(routeProps) => <BatchReport {...routeProps} {...props} />}
      />
    </MemoryRouter>
  );

  return { ...result, location: locationRef };
};

const waitForReportRequest = (uid, report) => {
  return new Promise((resolve) => {
    moxios.wait(() => {
      const request = moxios.requests.get("GET", `/api/v1/reports/${uid}`);
      request
        .respondWith({
          status: 200,
          response: report,
        })
        .then(resolve);
    });
  });
};

describe("BatchReport", () => {
  beforeEach(() => {
    StyleSheetTestUtils.suppressStyleInjection();
    moxios.install();
    // Clear localStorage to reset jotai atomWithStorage preferences between tests
    localStorage.clear();
  });

  afterEach(() => {
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    moxios.uninstall();
  });

  describe("Merge multitest", () => {
    it("merges multitest parts when clicking merge button", async () => {
      const uid = MULTITEST_PARTS_REPORT.uid;

      moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
        status: 200,
        response: {},
      });

      const { asFragment } = renderBatchReport(uid);

      await waitForReportRequest(uid, MULTITEST_PARTS_REPORT);

      await waitFor(() => {
        expect(screen.getByText("Please select an entry.")).toBeInTheDocument();
        expect(screen.getByText("SplitMultiTest - part(0/2)")).toBeInTheDocument();
        expect(screen.getByText("SplitMultiTest - part(1/2)")).toBeInTheDocument();
      });

      const mt_part0_text = screen.getByText("SplitMultiTest - part(0/2)");
      const mt_part0_treeItem = mt_part0_text.closest(".MuiTreeItem-root");
      const mt_part0_expandIcon = mt_part0_treeItem.querySelector(".MuiTreeItem-iconContainer");
      fireEvent.click(mt_part0_expandIcon);
      const suite1_text = screen.getByText("Suite1");
      const suite1_treeItem = suite1_text.closest(".MuiTreeItem-root");
      const suite1_expandIcon = suite1_treeItem.querySelector(".MuiTreeItem-iconContainer");
      fireEvent.click(suite1_expandIcon);

      // Should only see case 2
      expect(screen.queryByText("case1")).not.toBeInTheDocument();
      expect(screen.getByText("case2")).toBeInTheDocument();
      expect(screen.queryByText("case3")).not.toBeInTheDocument();
      expect(asFragment()).toMatchSnapshot("before merge");

      const mergeButton = screen.getByText("Merge multitest parts");
      fireEvent.click(mergeButton);

      await waitFor(() => {
        expect(screen.getByText("SplitMultiTest")).toBeInTheDocument();
        expect(screen.queryByText("SplitMultiTest - part(0/2)")).not.toBeInTheDocument();
        expect(screen.queryByText("SplitMultiTest - part(1/2)")).not.toBeInTheDocument();
      });

      // Expand the merged multitest to see suites
      const merged_mt_text = screen.getByText("SplitMultiTest");
      const merged_mt_treeItem = merged_mt_text.closest(".MuiTreeItem-root");
      const merged_mt_expandIcon = merged_mt_treeItem.querySelector(".MuiTreeItem-iconContainer");
      fireEvent.click(merged_mt_expandIcon);
      const merged_suite1_text = screen.getByText("Suite1");
      const merged_suite1_treeItem = merged_suite1_text.closest(".MuiTreeItem-root");
      const merged_suite1_expandIcon = merged_suite1_treeItem.querySelector(".MuiTreeItem-iconContainer");
      fireEvent.click(merged_suite1_expandIcon);

      // Can see case 1 - 3 in order in the snapshot
      expect(screen.getByText("case1")).toBeInTheDocument();
      expect(screen.getByText("case2")).toBeInTheDocument();
      expect(screen.getByText("case3")).toBeInTheDocument();
      expect(asFragment()).toMatchSnapshot("after merge");
    });

    it("toggles merge off when clicking button again", async () => {
      const uid = MULTITEST_PARTS_REPORT.uid;

      moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
        status: 200,
        response: {},
      });
      renderBatchReport(uid);

      await waitForReportRequest(uid, MULTITEST_PARTS_REPORT);

      await waitFor(() => {
        expect(screen.getByText("Please select an entry.")).toBeInTheDocument();
      });

      const mergeButton = screen.getByText("Merge multitest parts");
      fireEvent.click(mergeButton);

      await waitFor(() => {
        expect(screen.getByText("SplitMultiTest")).toBeInTheDocument();
      });

      fireEvent.click(mergeButton);

      await waitFor(() => {
        expect(screen.getByText("SplitMultiTest - part(0/2)")).toBeInTheDocument();
        expect(screen.getByText("SplitMultiTest - part(1/2)")).toBeInTheDocument();
        expect(screen.queryByText(/^SplitMultiTest$/)).not.toBeInTheDocument();
      });
    });

    it("navigates to correct testcase and fetches correct assertions file after merge", async () => {
      const uid = MULTITEST_PARTS_REPORT.uid;
      const part0 = MULTITEST_PARTS_REPORT.entries[0];
      const part1 = MULTITEST_PARTS_REPORT.entries[1];

      moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
        status: 200,
        response: {},
      });
      const part1AssertionsUrl = `/api/v1/reports/${uid}/attachments/assertions_${part1.uid}`;
      const part0AssertionsUrl = `/api/v1/reports/${uid}/attachments/assertions_${part0.uid}`;
      moxios.stubRequest(part1AssertionsUrl, {
        status: 200,
        response: { [part1.entries[0].entries[0].uid]: [] },
      });
      moxios.stubRequest(part0AssertionsUrl, {
        status: 200,
        response: { [part0.entries[1].entries[0].uid]: [] },
      });

      const { location } = renderBatchReport(uid);

      await waitForReportRequest(uid, MULTITEST_PARTS_REPORT);

      await waitFor(() => {
        expect(screen.getByText("Please select an entry.")).toBeInTheDocument();
      });

      const mergeButton = screen.getByText("Merge multitest parts");
      fireEvent.click(mergeButton);

      await waitFor(() => {
        expect(screen.getByText("SplitMultiTest")).toBeInTheDocument();
      });

      const merged_mt_text = screen.getByText("SplitMultiTest");
      const merged_mt_treeItem = merged_mt_text.closest(".MuiTreeItem-root");
      const merged_mt_expandIcon = merged_mt_treeItem.querySelector(".MuiTreeItem-iconContainer");
      fireEvent.click(merged_mt_expandIcon);
      const suite1_text = screen.getByText("Suite1");
      const suite1_treeItem = suite1_text.closest(".MuiTreeItem-root");
      const suite1_expandIcon = suite1_treeItem.querySelector(".MuiTreeItem-iconContainer");
      fireEvent.click(suite1_expandIcon);
      const case1_text = screen.getByText("case1");
      fireEvent.click(case1_text);

      await waitFor(() => {
        expect(screen.queryByText("Please select an entry.")).not.toBeInTheDocument();
      });

      // header + sidebar(treeview)
      expect(screen.getAllByText("case1")).toHaveLength(2);

      // Verify the full URL path for case1 (from part1)
      const part1Suite1 = part1.entries[0];
      const part1Suite1Case1 = part1Suite1.entries[0];
      const part1Suite1Case1ExpectedPath = `/testplan/${uid}/${part1.uid}/${part1Suite1.uid}/${part1Suite1Case1.uid}`;
      await waitFor(() => {
        expect(location.current.pathname).toBe(part1Suite1Case1ExpectedPath);
        // Verify assertions were fetched from part1's assertions file
        const assertionsRequest = moxios.requests.get("GET", part1AssertionsUrl);
        expect(assertionsRequest).toBeTruthy();
      });

      // Click case2 (from part0)
      const case2_text = screen.getByText("case2");
      fireEvent.click(case2_text);

      // Verify the full URL path for case2 (from part0)
      const part0Suite1 = part0.entries[1];
      const part0Suite1Case2 = part0Suite1.entries[0];
      const part0Suite1Case2ExpectedPath = `/testplan/${uid}/${part0.uid}/${part0Suite1.uid}/${part0Suite1Case2.uid}`;
      await waitFor(() => {
        expect(location.current.pathname).toBe(part0Suite1Case2ExpectedPath);
        // Verify assertions were fetched from part0's assertions file
        const assertionsRequest = moxios.requests.get("GET", part0AssertionsUrl);
        expect(assertionsRequest).toBeTruthy();
      });
    });

    it("merges status and counter correctly when a testcase fails", async () => {
      const reportWithFailure = _.cloneDeep(MULTITEST_PARTS_REPORT);
      const part1 = reportWithFailure.entries[1];
      const part1Suite1 = part1.entries[0];
      const part1Case1 = part1Suite1.entries[0];
      part1Case1.status = "failed";
      part1Case1.counter = { passed: 0, failed: 1, error: 0, total: 1 };
      part1Suite1.status = "failed";
      part1Suite1.counter = { passed: 1, failed: 1, error: 0, total: 2 };
      part1.status = "failed";
      part1.counter = { passed: 1, failed: 1, error: 0, total: 2 };
      reportWithFailure.status = "failed";
      reportWithFailure.counter = { passed: 3, failed: 1, error: 0, total: 4 };
      const uid = reportWithFailure.uid;

      moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
        status: 200,
        response: {},
      });
      const part1AssertionsUrl = `/api/v1/reports/${uid}/attachments/assertions_${part1.uid}`;
      // stub the assertion call since we will navigate to the failed testcase
      moxios.stubRequest(part1AssertionsUrl, {
        status: 200,
        response: { [part1.entries[0].entries[0].uid]: [] },
      });

      const {asFragment} = renderBatchReport(uid);

      await waitForReportRequest(uid, reportWithFailure);

      const mergeButton = screen.getByText("Merge multitest parts");
      fireEvent.click(mergeButton);

      // Verify the merged multitest shows failed status
      const mergedMtText = screen.getByTitle("SplitMultiTest - failed");
      expect(mergedMtText).toBeInTheDocument();

      // Check the counter display shows correct merged values (3 passed / 1 failed)
      // Navigate from the merged multitest element to its parent label, then find the counter
      const mergedMtLabel = mergedMtText.closest(".MuiTreeItem-label");
      const counterSpan = mergedMtLabel.querySelector('[title="passed/failed testcases"]');
      const passedCount = counterSpan.querySelector('[class*="passed"]');
      const failedCount = counterSpan.querySelector('[class*="failed"]');

      expect(passedCount).toHaveTextContent("3");
      expect(failedCount).toHaveTextContent("1");
    });
  }); 
});
