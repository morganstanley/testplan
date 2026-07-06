import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { MemoryRouter, Route } from "react-router-dom";
import moxios from "moxios";
import _ from "lodash";

import { taggedReport } from "../../Common/fakeReport";
import { MULTITEST_EXCEPTION_REPORT } from "../../Common/sampleReports";
import { PropagateIndices } from "../reportUtils";
import SearchFieldParser from "../../Parser/SearchFieldParser";
import { filterEntries } from "../reportFilter";
import BatchReport from "../BatchReport";

describe("Report/reportFilter", () => {
  let report;
  const validate = (search_string, ...validations) => {
    const filter = SearchFieldParser.parse(search_string);
    const filtered = filterEntries(report.entries, filter);
    const [paths, expected_values] = _.unzip(validations);
    expect(_.at(filtered, paths)).toEqual(expected_values);
  };

  const empty_result = ["length", 0];

  beforeAll(() => {
    report = PropagateIndices(taggedReport);
  });

  describe("multitest filter", () => {
    const multitest_primary = [
      ["length", 1],
      ["[0].name", "Primary"],
      ["[0].entries.length", 2],
      ["[0].entries[0].entries.length", 2],
      ["[0].entries[1].entries.length", 3],
    ];

    it.each([
      //case insensitive
      ["primary", ...multitest_primary],
      ["mt:primary", ...multitest_primary],
      ["multitest:primary", ...multitest_primary],
      //case is ok
      ["Primary", ...multitest_primary],
      ["mt:Primary", ...multitest_primary],
      ["multitest:Primary", ...multitest_primary],
      //partial
      ["rima", ...multitest_primary],
      ["mt:rima", ...multitest_primary],
      ["multitest:rima", ...multitest_primary],
      ["mt:BlaBla", empty_result],
      ["multitest:BlaBla", empty_result],
    ])('should filter correctly with: "%s"', validate);
  });

  describe("suite filter", () => {
    const suite_gamma = [
      ["length", 1],
      ["[0].name", "Secondary"],
      ["[0].entries.length", 1],
      ["[0].entries[0].name", "Gamma"],
      ["[0].entries[0].entries.length", 3],
    ];

    it.each([
      //case insensitive
      ["gamma", ...suite_gamma],
      ["s:gamma", ...suite_gamma],
      ["testsuite:gamma", ...suite_gamma],
      //case is ok
      ["Gamma", ...suite_gamma],
      ["s:Gamma", ...suite_gamma],
      ["testsuite:Gamma", ...suite_gamma],
      //partial
      ["amm", ...suite_gamma],
      ["s:amm", ...suite_gamma],
      ["testsuite:amm", ...suite_gamma],
      ["s:BlaBla", empty_result],
      ["testsuite:BlaBla", empty_result],
    ])('should filter correctly with: "%s"', validate);
  });

  describe("testcase filter", () => {
    const testcase_3 = [
      ["length", 2],
      ["[0].entries.length", 1],
      ["[0].entries[0].name", "Beta"],
      ["[0].entries[0].entries.length", 1],
      ["[0].entries[0].entries[0].name", "test_3"],
      ["[1].entries.length", 1],
      ["[1].entries[0].name", "Gamma"],
      ["[1].entries[0].entries.length", 1],
      ["[1].entries[0].entries[0].name", "test_3"],
    ];

    it.each([
      //case insensitive
      ["Test_3", ...testcase_3],
      ["c:Test_3", ...testcase_3],
      ["testcase:Test_3", ...testcase_3],
      //case is ok
      ["test_3", ...testcase_3],
      ["c:test_3", ...testcase_3],
      ["testcase:test_3", ...testcase_3],
      //partial
      ["st_3", ...testcase_3],
      ["c:st_3", ...testcase_3],
      ["testcase:st_3", ...testcase_3],
      ["c:BlaBla", empty_result],
      ["testcase:BlaBla", empty_result],
    ])('should filter correctly with: "%s"', validate);
  });

  describe("tag filter", () => {
    const tag_server = [
      ["length", 2],
      ["[0].entries.length", 1],
      ["[0].entries[0].name", "Beta"],
      ["[0].entries[0].entries.length", 2],
      ["[0].entries[0].entries[0].name", "test_1"],
      ["[0].entries[0].entries[1].name", "test_3"],
      ["[1].entries.length", 1],
      ["[1].entries[0].name", "Gamma"], // The Gamma is tagged so expecting all case
      ["[1].entries[0].entries.length", 3],
    ];

    it.each([
      //case insensitive
      ["Server", ...tag_server],
      ["tag:Server", ...tag_server],
      //case is ok
      ["server", ...tag_server],
      ["tag:server", ...tag_server],
      //partial actually no partial so test it that way
      ["serv", empty_result],
      ["tag:serv", empty_result],
      ["c:BlaBla", empty_result],
      ["testcase:BlaBla", empty_result],
    ])('should filter correctly with: "%s"', validate);
  });

  describe("named tag filter", () => {
    const tag_blue = [
      ["length", 2],
      ["[0].entries.length", 1],
      ["[0].entries[0].name", "Beta"],
      ["[0].entries[0].entries.length", 2],
      ["[0].entries[0].entries[0].name", "test_2"],
      ["[0].entries[0].entries[1].name", "test_3"],
      ["[1].entries.length", 1],
      ["[1].entries[0].name", "Gamma"],
      ["[1].entries[0].entries.length", 1],
      ["[1].entries[0].entries[0].name", "test_2"],
    ];

    it.each([
      //case insensitive
      ["color=Blue", ...tag_blue],
      ["tag:color=Blue", ...tag_blue],
      ["tag:Color=Blue", ...tag_blue],
      //case is ok
      ["color=blue", ...tag_blue],
      ["tag:color=blue", ...tag_blue],
      // non named search
      ["tag:blue", empty_result],
      // search for tag name only
      ["tag:color", empty_result],
      //partial actually no partial so test it that way
      ["color=blu", empty_result],
      ["tag:color=blu", empty_result],
      ["colo=blue", empty_result],
      ["tag:colo=blue", empty_result],
      ["c:BlaBla", empty_result],
      ["testcase:BlaBla", empty_result],
    ])('should filter correctly with: "%s"', validate);
  });

  describe("multiple terms", () => {
    const primary_testcase_3 = [
      ["length", 1],
      ["[0].name", "Primary"],
      ["[0].entries.length", 1],
      ["[0].entries[0].name", "Beta"],
      ["[0].entries[0].entries.length", 1],
      ["[0].entries[0].entries[0].name", "test_3"],
    ];

    const secondary_testcase_3 = [
      ["length", 1],
      ["[0].name", "Secondary"],
      ["[0].entries.length", 1],
      ["[0].entries[0].name", "Gamma"],
      ["[0].entries[0].entries.length", 1],
      ["[0].entries[0].entries[0].name", "test_3"],
    ];

    it.each([
      ["mt:primary c:test_3", ...primary_testcase_3],
      ["s:beta c:test_3", ...primary_testcase_3],
      ["tag:color=blue c:test_3", ...primary_testcase_3],
      ["s:alpha c:test_3", empty_result],
      ["mt:secondary c:test_3", ...secondary_testcase_3],
      ["mt:secondary c:test_3", ...secondary_testcase_3],
    ])('should filter correctly with: "%s"', validate);
  });

  describe("grouped terms", () => {
    const tag_blue_server = [
      ["length", 2],
      ["[0].entries.length", 1],
      ["[0].entries[0].name", "Beta"],
      ["[0].entries[0].entries.length", 1],
      ["[0].entries[0].entries[0].name", "test_3"],
      ["[1].entries.length", 1],
      ["[1].entries[0].name", "Gamma"],
      ["[1].entries[0].entries.length", 1],
      ["[1].entries[0].entries[0].name", "test_2"],
    ];

    const tag_red_client = [
      ["length", 1],
      ["[0].entries.length", 1],
      ["[0].entries[0].name", "Gamma"],
      ["[0].entries[0].entries.length", 2],
      ["[0].entries[0].entries[0].name", "test_1"],
      ["[0].entries[0].entries[1].name", "test_2"],
    ];

    it.each([
      ["tag:server tag:color=blue", ...tag_blue_server],
      ["tag:(server color=blue)", ...tag_blue_server],
      ["tag:(client color=red)", ...tag_red_client],
      ["tag:(client color=red BlaBla)", empty_result],
    ])('should filter correctly with: "%s"', validate);
  });

  const tag_blue_or_server = [
    ["length", 2],
    ["[0].entries.length", 1],
    ["[0].entries[0].name", "Beta"],
    ["[0].entries[0].entries.length", 3],
    ["[1].entries.length", 1],
    ["[1].entries[0].name", "Gamma"],
    ["[1].entries[0].entries.length", 3],
  ];

  const all = [
    ["length", 2],
    ["[0].entries.length", 2],
    ["[0].entries[0].name", "Alpha"],
    ["[0].entries[0].entries.length", 2],
    ["[0].entries[1].name", "Beta"],
    ["[0].entries[1].entries.length", 3],
    ["[1].entries.length", 1],
    ["[1].entries[0].name", "Gamma"],
    ["[1].entries[0].entries.length", 3],
  ];

  describe("OR terms", () => {
    it.each([
      ["tag:server OR tag:color=blue", ...tag_blue_or_server],
      ["{tag:server tag:color=blue}", ...tag_blue_or_server],
      ["tag:server OR tag:color=blue OR mt:primary", ...all],
      ["{tag:server tag:color=blue mt:primary}", ...all],
    ])('should filter correctly with: "%s"', validate);
  });

  describe("Free Text", () => {
    it.each([
      ["server color=blue", ...tag_blue_or_server],
      ["server blue", ...tag_blue_or_server],
      ["primary server", ...all],
      ["alpha beta gamma", ...all],
      ["test_1 test_2 test_3", ...all],
      ["ary BlaBla", ...all],
    ])('should filter correctly with: "%s"', validate);
  });
});

// End-to-end test that drives the filter through the real UI (BatchReport +
// the toolbar search box) rather than calling filterEntries() directly. Uses a
// sanitized copy of a real report.json, whose top-level "hohoo" multitest has
// log output but no child entries (it errored during setup).
describe("Report/reportFilter (e2e via BatchReport)", () => {
  const uid = MULTITEST_EXCEPTION_REPORT.uid;
  // The first failure lives in this multitest, so navigating to it on load
  // triggers a fetch for its assertions file.
  const failingMt = MULTITEST_EXCEPTION_REPORT.entries[0]; // "Basic Assertions Test"

  const respondWithReport = () => {
    moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
      status: 200,
      response: {},
    });
    moxios.stubRequest(
      `/api/v1/reports/${uid}/attachments/assertions_${failingMt.uid}`,
      { status: 200, response: {} }
    );
    return new Promise((resolve) => {
      moxios.wait(() => {
        moxios.requests
          .get("GET", `/api/v1/reports/${uid}`)
          .respondWith({ status: 200, response: MULTITEST_EXCEPTION_REPORT })
          .then(resolve);
      });
    });
  };

  beforeEach(() => {
    moxios.install();
    localStorage.clear();
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it("keeps a logs-only group when it matches the search filter", async () => {
    render(
      <MemoryRouter initialEntries={[`/testplan/${uid}`]}>
        <Route
          path="/testplan/:uid/:selection*"
          render={(routeProps) => <BatchReport {...routeProps} />}
        />
      </MemoryRouter>
    );
    await respondWithReport();

    // Both top-level multitests are visible before filtering.
    await waitFor(() => {
      expect(screen.getByTitle("hohoo - error")).toBeInTheDocument();
    });
    expect(
      screen.getByTitle("Basic Assertions Test - failed")
    ).toBeInTheDocument();

    // The toolbar search box is the only text input on screen.
    const searchBox = screen.getByRole("textbox");

    // Search for the logs-only group.
    fireEvent.change(searchBox, { target: { value: "hohoo" } });

    // "hohoo" has no child entries, only logs -- it must still be displayed,
    // while the unrelated multitest gets filtered out of the nav.
    await waitFor(() => {
      expect(
        screen.queryByTitle("Basic Assertions Test - failed")
      ).not.toBeInTheDocument();
    });
    expect(screen.getByTitle("hohoo - error")).toBeInTheDocument();

    // Clearing the search box restores the full nav -- both multitests show.
    fireEvent.change(searchBox, { target: { value: "" } });

    await waitFor(() => {
      expect(
        screen.getByTitle("Basic Assertions Test - failed")
      ).toBeInTheDocument();
    });
    expect(screen.getByTitle("hohoo - error")).toBeInTheDocument();
  });
});
