import React from "react";
import { shallow, mount } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";
import moxios from "moxios";
import ReactRouterEnzymeContext from "react-router-enzyme-context";

import _ from "lodash";

import { BatchReportComponent } from "../BatchReport";
import Message from "../../Common/Message";
import {
  TESTPLAN_REPORT,
  SIMPLE_PASSED_REPORT,
  SIMPLE_FAILED_REPORT,
  SIMPLE_ERROR_REPORT,
  ERROR_REPORT,
} from "../../Common/sampleReports";

describe("BatchReport", () => {
  const renderBatchReport = (
    uid = "123",
    selection = undefined,
    displayTime = false,
    UTCTime = false,
  ) => {
    // Mock the match object that would be passed down from react-router.
    // BatchReport uses this object to get the report UID.
    const routerContext = new ReactRouterEnzymeContext();
    const mockMatch = {
      params: { uid, selection },
      path: "/testplan/:uid/:selection*",
    };
    routerContext.props().history.replace(`/testplan/${uid}/${selection}`);
    return shallow(
      <BatchReportComponent
        match={mockMatch}
        history={routerContext.props().history}
        displayTime={displayTime}
        UTCTime={UTCTime}
      />,
      {
        ...routerContext.get(),
      }
    );
  };

  const renderBatchReportFull = (uid = "123") => {
    // Mock the match object that would be passed down from react-router.
    // BatchReport uses this object to get the report UID.
    const mockMatch = {
      params: { uid: uid, selection: undefined },
      path: "/testplan/:uid/:selection*",
    };
    return mount(
      <BatchReportComponent match={mockMatch} displayTime={false} />
    );
  };

  function handleRedirect(batchReport) {
    const props = batchReport.instance().props;
    const selection = props.history.location.pathname
      .split("/")
      .slice(3)
      .join("/");
    const newProps = _.set({}, "match.params.selection", selection);
    _.defaultsDeep(newProps, props);
    batchReport.setProps(newProps);
  }

  beforeEach(() => {
    // Stop Aphrodite from injecting styles, this crashes the tests.
    StyleSheetTestUtils.suppressStyleInjection();
    moxios.install();
  });

  afterEach(() => {
    // Resume style injection once test is finished.
    StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    moxios.uninstall();
  });

  it("shallow renders without crashing", () => {
    renderBatchReport();
  });

  it("shallow renders the correct HTML structure when report loaded", () => {
    const batchReport = renderBatchReport(
      "520a92e4-325e-4077-93e6-55d7091a3f83"
    );
    batchReport.instance().setReport(TESTPLAN_REPORT);
    batchReport.update();
    expect(batchReport).toMatchSnapshot();
  });

  it("renders loading message when fetching report", () => {
    const batchReport = renderBatchReportFull();
    batchReport.setState({ loading: true });
    batchReport.update();
    expect(batchReport).toMatchSnapshot();
    const message = batchReport.find(Message);
    const expectedMessage = "Fetching Testplan report...";
    expect(message.props().message).toEqual(expectedMessage);
  });

  it("renders waiting message when waiting to start fetch", () => {
    const batchReport = renderBatchReportFull();
    batchReport.setState({ loading: false, error: null });
    batchReport.update();
    const message = batchReport.find(Message);
    const expectedMessage = "Waiting to fetch Testplan report...";
    expect(message.props().message).toEqual(expectedMessage);
  });

  it("loads a passed simple report", (done) => {
    moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
      status: 200,
      response: {},
    });
    const batchReport = renderBatchReport(
      "520a92e4-325e-4077-93e6-55d7091a3f83"
    );
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(
        "/api/v1/reports/520a92e4-325e-4077-93e6-55d7091a3f83"
      );
      request
        .respondWith({
          status: 200,
          response: SIMPLE_PASSED_REPORT,
        })
        .then(() => {
          batchReport.update();
          const props = batchReport.instance().props;
          expect(props.history.location.pathname).toBe(
            "/testplan/520a92e4-325e-4077-93e6-55d7091a3f83"
          );
          handleRedirect(batchReport);
          expect(batchReport).toMatchSnapshot();
          done();
        });
    });
  });

  it("loads a failed simple report", (done) => {
    moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
      status: 200,
      response: {},
    });
    const batchReport = renderBatchReport(
      "520a92e4-325e-4077-93e6-55d7091a3f83"
    );
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(
        "/api/v1/reports/520a92e4-325e-4077-93e6-55d7091a3f83"
      );
      request
        .respondWith({
          status: 200,
          response: SIMPLE_FAILED_REPORT,
        })
        .then(() => {
          batchReport.update();
          const props = batchReport.instance().props;
          expect(props.history.location.pathname).toBe(
            "/testplan/520a92e4-325e-4077-93e6-55d7091a3f83/21739167-b30f-4c13-a315-ef6ae52fd1f7/cb144b10-bdb0-44d3-9170-d8016dd19ee7/736706ef-ba65-475d-96c5-f2855f431028"
          );
          handleRedirect(batchReport);
          expect(batchReport).toMatchSnapshot();
          done();
        });
    });
  });

  it("loads a more complex report", (done) => {
    moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
      status: 200,
      response: {},
    });
    const batchReport = renderBatchReport(
      "520a92e4-325e-4077-93e6-55d7091a3f83"
    );
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(
        "/api/v1/reports/520a92e4-325e-4077-93e6-55d7091a3f83"
      );
      request
        .respondWith({
          status: 200,
          response: TESTPLAN_REPORT,
        })
        .then(() => {
          batchReport.update();
          const props = batchReport.instance().props;
          expect(props.history.location.pathname).toBe(
            "/testplan/520a92e4-325e-4077-93e6-55d7091a3f83/21739167-b30f-4c13-a315-ef6ae52fd1f7/cb144b10-bdb0-44d3-9170-d8016dd19ee7/78686a4d-7b94-4ae6-ab50-d9960a7fb714"
          );
          handleRedirect(batchReport);
          expect(batchReport).toMatchSnapshot();
          done();
        });
    });
  });

  it("loads a more complex error report", (done) => {
    moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
      status: 200,
      response: {},
    });
    const batchReport = renderBatchReport(
      "520a92e4-325e-4077-93e6-55d7091a3f83"
    );
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(
        "/api/v1/reports/520a92e4-325e-4077-93e6-55d7091a3f83"
      );
      request
        .respondWith({
          status: 200,
          response: ERROR_REPORT,
        })
        .then(() => {
          batchReport.update();
          const props = batchReport.instance().props;
          expect(props.history.location.pathname).toBe(
            "/testplan/520a92e4-325e-4077-93e6-55d7091a3f83/8c3c7e6b-48e8-40cd-86db-8c8aed2592c8/08d4c671-d55d-49d4-96ba-dc654d12be26"
          );
          handleRedirect(batchReport);
          expect(batchReport).toMatchSnapshot();
          done();
        });
    });
  });

  it.each([
    ["Multitest", "21739167-b30f-4c13-a315-ef6ae52fd1f7"],
    [
      "Testsuite",
      "21739167-b30f-4c13-a315-ef6ae52fd1f7/cb144b10-bdb0-44d3-9170-d8016dd19ee7",
    ],
    [
      "Testcase",
      "8c3c7e6b-48e8-40cd-86db-8c8aed2592c8/08d4c671-d55d-49d4-96ba-dc654d12be26/f73bd6ea-d378-437b-a5db-00d9e427f36a",
    ],
  ])("loads a report with selection at %s level", (level, selection, done) => {
    moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
      status: 200,
      response: {},
    });
    const batchReport = renderBatchReport(
      "520a92e4-325e-4077-93e6-55d7091a3f83",
      selection
    );
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(
        "/api/v1/reports/520a92e4-325e-4077-93e6-55d7091a3f83"
      );
      request
        .respondWith({
          status: 200,
          response: TESTPLAN_REPORT,
        })
        .then(() => {
          batchReport.update();
          const props = batchReport.instance().props;
          expect(props.history.location.pathname).toBe(
            `/testplan/520a92e4-325e-4077-93e6-55d7091a3f83/${selection}`
          );
          handleRedirect(batchReport);
          expect(batchReport).toMatchSnapshot();
          done();
        });
    });
  });

  it("loads a report with selection at Testcase level and UTC Time Information enabled", (done) => {
    moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
      status: 200,
      response: {},
    });
    const batchReport = renderBatchReport(
      "520a92e4-325e-4077-93e6-55d7091a3f83",
      "8c3c7e6b-48e8-40cd-86db-8c8aed2592c8/08d4c671-d55d-49d4-96ba-dc654d12be26/f73bd6ea-d378-437b-a5db-00d9e427f36a",
      true,
      true
    );
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(
        "/api/v1/reports/520a92e4-325e-4077-93e6-55d7091a3f83"
      );
      request
        .respondWith({
          status: 200,
          response: TESTPLAN_REPORT,
        })
        .then(() => {
          batchReport.update();
          const props = batchReport.instance().props;
          expect(props.history.location.pathname).toBe(
            `/testplan/520a92e4-325e-4077-93e6-55d7091a3f83/8c3c7e6b-48e8-40cd-86db-8c8aed2592c8/08d4c671-d55d-49d4-96ba-dc654d12be26/f73bd6ea-d378-437b-a5db-00d9e427f36a`
          );
          handleRedirect(batchReport);
          expect(batchReport).toMatchSnapshot();
          done();
        });
    });
  });

  it("loads a report with selection at Testcase level and Time Information enabled", (done) => {
    moxios.stubRequest("/api/v1/metadata/fix-spec/tags", {
      status: 200,
      response: {},
    });
    const batchReport = renderBatchReport(
      "520a92e4-325e-4077-93e6-55d7091a3f83",
      "8c3c7e6b-48e8-40cd-86db-8c8aed2592c8/08d4c671-d55d-49d4-96ba-dc654d12be26/f73bd6ea-d378-437b-a5db-00d9e427f36a",
      true
    );
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(
        "/api/v1/reports/520a92e4-325e-4077-93e6-55d7091a3f83"
      );
      request
        .respondWith({
          status: 200,
          response: TESTPLAN_REPORT,
        })
        .then(() => {
          batchReport.update();
          const props = batchReport.instance().props;
          expect(props.history.location.pathname).toBe(
            `/testplan/520a92e4-325e-4077-93e6-55d7091a3f83/8c3c7e6b-48e8-40cd-86db-8c8aed2592c8/08d4c671-d55d-49d4-96ba-dc654d12be26/f73bd6ea-d378-437b-a5db-00d9e427f36a`
          );
          handleRedirect(batchReport);
          expect(batchReport).toMatchSnapshot();
          done();
        });
    });
  });

  it("renders an error message when Testplan report cannot be found.", (done) => {
    const batchReport = renderBatchReportFull();
    moxios.wait(function () {
      let request = moxios.requests.mostRecent();
      request
        .respondWith({
          status: 404,
        })
        .then(function () {
          batchReport.update();
          const message = batchReport.find(Message);
          const expectedMessage = "Error: Request failed with status code 404";
          expect(message.props().message).toEqual(expectedMessage);
          done();
        });
    });
  });

  it("shallow renders the correct HTML structure when report with errors loaded", () => {
    const batchReport = renderBatchReportFull();
    batchReport.setState({ report: SIMPLE_ERROR_REPORT });
    batchReport.update();
    expect(batchReport).toMatchSnapshot();
  });
});
