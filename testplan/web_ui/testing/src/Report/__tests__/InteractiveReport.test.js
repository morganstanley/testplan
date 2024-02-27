/* Tests the InteractiveReport component. */
import React from "react";
import { shallow } from "enzyme";
import { StyleSheetTestUtils } from "aphrodite";
import moxios from "moxios";
import ReactRouterEnzymeContext from "react-router-enzyme-context";

import InteractiveReport, {
  InteractiveReportComponent,
} from "../InteractiveReport.js";
import { PropagateIndices } from "../reportUtils.js";

const initialReport = () => ({
  category: "testplan",
  uid: "TestplanUID",
  timer: {},
  status: "unknown",
  runtime_status: "ready",
  env_status: null,
  meta: {},
  status_override: null,
  attachments: {},
  tags_index: {},
  name: "TestplanName",
  parent_uids: [],
  type: "TestGroupReport",
  hash: 12345,
  entries: [
    {
      category: "multitest",
      uid: "MultiTestUID",
      timer: {},
      description: null,
      tags: {},
      status: "unknown",
      runtime_status: "ready",
      env_status: "STOPPED",
      part: null,
      status_override: null,
      name: "MultiTestName",
      fix_spec_path: null,
      parent_uids: ["TestplanUID"],
      type: "TestGroupReport",
      category: "multitest",
      hash: 12345,
      entries: [
        {
          category: "testsuite",
          uid: "SuiteUID",
          timer: {},
          description: null,
          tags: {},
          status: "unknown",
          runtime_status: "ready",
          env_status: null,
          part: null,
          status_override: null,
          name: "SuiteName",
          fix_spec_path: null,
          parent_uids: ["TestplanUID", "MultiTestUID"],
          type: "TestGroupReport",
          category: "testsuite",
          hash: 12345,
          entries: [
            {
              type: "TestCaseReport",
              parent_uids: ["TestplanUID", "MultiTestUID", "SuiteUID"],
              logs: [],
              entries: [],
              status_reason: null,
              runtime_status: "ready",
              tags: {},
              uid: "setup",
              category: "synthesized",
              status: "unknown",
              status_override: null,
              timer: {},
              name: "setup",
              description: null,
              hash: 12345,
              definition_name: "setup"
            },
            {
              category: "testcase",
              uid: "testcaseUID",
              timer: {},
              description: null,
              tags: {},
              type: "TestCaseReport",
              status: "unknown",
              runtime_status: "ready",
              env_status: null,
              logs: [],
              entries: [],
              status_override: null,
              name: "testcaseName",
              type: "TestCaseReport",
              parent_uids: ["TestplanUID", "MultiTestUID", "SuiteUID"],
              hash: 12345,
            },
            {
              category: "parametrization",
              description: "Parametrized testcase.",
              env_status: null,
              fix_spec_path: null,
              name: "ParametrizationName",
              parent_uids: ["TestplanUID", "MultiTestUID", "SuiteUID"],
              part: null,
              runtime_status: "ready",
              status: "unknown",
              status_override: null,
              tags: {},
              timer: {},
              uid: "ParametrizationUID",
              entries: [
                {
                  category: "testcase",
                  description: null,
                  entries: [],
                  logs: [],
                  name: "ParametrizationName__val_1",
                  parent_uids: [
                    "TestplanUID",
                    "MultiTestUID",
                    "SuiteUID",
                    "ParametrizationUID",
                  ],
                  status: "unknown",
                  runtime_status: "ready",
                  status_override: null,
                  tags: {},
                  timer: {},
                  type: "TestCaseReport",
                  uid: "ParametrizationUID__val_1",
                },
              ],
            },
          ],
        },
      ],
    },
  ],
});

const renderInteractiveReport = () => {
  // Mock the match object that would be passed down from react-router.
  // InteractiveReport uses this object to get the report UID.
  const routerContext = new ReactRouterEnzymeContext();
  const mockMatch = {
    params: { uid: "TestplanUID", selection: undefined },
    path: "/interactive/:uid/:selection*",
  };
  return shallow(
    <InteractiveReportComponent
      match={mockMatch}
      history={routerContext.props().history}
      poll_intervall="1000000"
    />, //give time to call getReport as the testcase wants
    {
      ...routerContext.get(),
    }
  );
};

describe("InteractiveReport", () => {
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

  it("Loads report skeleton when mounted", (done) => {
    const interactiveReport = renderInteractiveReport();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report");
      request
        .respondWith({
          status: 200,
          response: {
            category: "testplan",
            uid: "TestplanUID",
            timer: {},
            status: "unknown",
            runtime_status: "ready",
            meta: {},
            entry_uids: ["MultiTestUID"],
            parent_uids: [],
            status_override: null,
            attachments: {},
            tags_index: {},
            name: "TestplanName",
            hash: 12345,
          },
        })
        .then(() => {
          moxios.wait(() => {
            const request = moxios.requests.mostRecent();
            expect(request.url).toBe("/api/v1/interactive/report/tests");
            request
              .respondWith({
                status: 200,
                response: [
                  {
                    category: "multitest",
                    uid: "MultiTestUID",
                    timer: {},
                    description: null,
                    tags: {},
                    status: "unknown",
                    runtime_status: "ready",
                    part: null,
                    status_override: null,
                    entry_uids: ["SuiteUID"],
                    parent_uids: ["TestplanUID"],
                    name: "MultitestName",
                    fix_spec_path: null,
                    hash: 12345,
                  },
                ],
              })
              .then(() => {
                moxios.wait(() => {
                  const request = moxios.requests.mostRecent();
                  expect(request.url).toBe(
                    "/api/v1/interactive/report/tests/MultiTestUID/suites"
                  );
                  request
                    .respondWith({
                      status: 200,
                      response: [
                        {
                          category: "testsuite",
                          uid: "SuiteUID",
                          timer: {},
                          description: null,
                          tags: {},
                          status: "unknown",
                          runtime_status: "ready",
                          part: null,
                          status_override: null,
                          entry_uids: ["testcaseUID"],
                          parent_uids: ["TestplanUID", "MultitestUID"],
                          name: "SuiteName",
                          fix_spec_path: null,
                          hash: 12345,
                        },
                      ],
                    })
                    .then(() => {
                      moxios.wait(() => {
                        const request = moxios.requests.mostRecent();
                        expect(request.url).toBe(
                          "/api/v1/interactive/report/tests/MultiTestUID" +
                            "/suites/SuiteUID/testcases"
                        );
                        request
                          .respondWith({
                            status: 200,
                            response: [
                              {
                                category: "testcase",
                                uid: "testcaseUID",
                                timer: {},
                                description: null,
                                tags: {},
                                type: "TestCaseReport",
                                status: "unknown",
                                runtime_status: "ready",
                                logs: [],
                                entries: [],
                                status_override: null,
                                name: "testcaseName",
                                parent_uids: [
                                  "TestplanUID",
                                  "MultiTestUID",
                                  "SuiteUID",
                                ],
                                hash: 12345,
                              },
                              {
                                category: "parametrization",
                                description: "Parametrized testcase.",
                                env_status: null,
                                entry_uids: ["ParametrizationUID__val_1"],
                                fix_spec_path: null,
                                name: "ParametrizationName",
                                parent_uids: [
                                  "TestplanUID",
                                  "MultiTestUID",
                                  "SuiteUID",
                                ],
                                part: null,
                                runtime_status: "ready",
                                status: "unknown",
                                status_override: null,
                                tags: {},
                                timer: {},
                                uid: "ParametrizationUID",
                              },
                            ],
                          })
                          .then(() => {
                            moxios.wait(() => {
                              const request = moxios.requests.mostRecent();
                              expect(request.url).toBe(
                                "/api/v1/interactive/report/tests/MultiTestUID" +
                                  "/suites/SuiteUID/testcases/ParametrizationUID" +
                                  "/parametrizations"
                              );
                              request
                                .respondWith({
                                  status: 200,
                                  response: [
                                    {
                                      category: "testcase",
                                      description: null,
                                      entries: [],
                                      logs: [],
                                      name: "ParametrizationName__val_1",
                                      parent_uids: [
                                        "TestplanUID",
                                        "MultiTestUID",
                                        "SuiteUID",
                                        "ParametrizationUID",
                                      ],
                                      status: "unknown",
                                      runtime_status: "ready",
                                      status_override: null,
                                      tags: {},
                                      timer: {},
                                      type: "TestCaseReport",
                                      uid: "ParametrizationUID__val_1",
                                    },
                                  ],
                                })
                                .then(() => {
                                  expect(InteractiveReport).toMatchSnapshot();
                                  done();
                                });
                            });
                          });
                      });
                    });
                });
              });
          });
        });
    });
  });

  const testRunEntry = (done, clickedEntry, expectedURL) => {
    const interactiveReport = renderInteractiveReport();
    const report = PropagateIndices(initialReport());

    interactiveReport.setState({
      report: report,
    });
    interactiveReport.update();

    const mockEvent = {
      stopPropagation: jest.fn(),
      preventDefault: jest.fn(),
    };
    interactiveReport
      .instance()
      .handleClick(mockEvent, clickedEntry, "running");

    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(expectedURL);
      expect(request.config.method).toBe("put");
      const putData = JSON.parse(request.config.data);
      expect(putData.uid).toBe(clickedEntry.uid);
      expect(putData.runtime_status).toBe("running");

      request
        .respondWith({
          status: 200,
          response: putData,
        })
        .then(() => {
          expect(interactiveReport).toMatchSnapshot();
          done();
        });
    });
  };

  it("handles tests being run", (done) =>
    testRunEntry(
      done,
      initialReport().entries[0],
      "/api/v1/interactive/report/tests/MultiTestUID"
    ));

  it("handles individual test suites being run", (done) =>
    testRunEntry(
      done,
      initialReport().entries[0].entries[0],
      "/api/v1/interactive/report/tests/MultiTestUID/suites/SuiteUID"
    ));

  it("handles individual testcases being run", (done) =>
    testRunEntry(
      done,
      initialReport().entries[0].entries[0].entries[1],
      "/api/v1/interactive/report/tests/MultiTestUID/suites/SuiteUID" +
        "/testcases/testcaseUID"
    ));

  it("handles individual parametrizations being run", (done) =>
    testRunEntry(
      done,
      initialReport().entries[0].entries[0].entries[2].entries[0],
      "/api/v1/interactive/report/tests/MultiTestUID/suites/SuiteUID" +
        "/testcases/ParametrizationUID/parametrizations" +
        "/ParametrizationUID__val_1"
    ));

  it("Parially refreshes the report on update.", (done) => {
    const interactiveReport = renderInteractiveReport();
    const report = initialReport();

    interactiveReport.setState({
      report: report,
    });
    interactiveReport.update();

    interactiveReport.instance().getReport();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report");
      const requestCount = moxios.requests.count();
      request
        .respondWith({
          status: 200,

          // Do not change the hash - no more API requests should be received.
          response: {
            category: "testplan",
            uid: "TestplanUID",
            timer: {},
            status: "unknown",
            runtime_status: "ready",
            meta: {},
            entry_uids: ["MultitestUID"],
            parent_uids: [],
            status_override: null,
            attachments: {},
            tags_index: {},
            name: "TestplanName",
            hash: 12345,
          },
        })
        .then(() => {
          moxios.wait(() => {
            expect(moxios.requests.count()).toBe(requestCount);
            expect(interactiveReport).toMatchSnapshot();
            done();
          });
        });
    });
  });

  it("Updates testcase state", (done) => {
    const interactiveReport = renderInteractiveReport();
    const report = initialReport();

    interactiveReport.setState({
      report: report,
    });
    interactiveReport.update();

    interactiveReport.instance().getReport();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report");
      const requestCount = moxios.requests.count();
      request
        .respondWith({
          status: 200,

          response: {
            category: "testplan",
            uid: "TestplanUID",
            timer: {},
            status: "unknown",
            runtime_status: "running",
            meta: {},
            entry_uids: ["MultitestUID"],
            parent_uids: [],
            status_override: null,
            attachments: {},
            tags_index: {},
            name: "TestplanName",
            hash: 11111,
          },
        })
        .then(() => {
          moxios.wait(() => {
            const request = moxios.requests.mostRecent();
            expect(request.url).toBe("/api/v1/interactive/report/tests");
            request
              .respondWith({
                status: 200,
                response: [
                  {
                    category: "multitest",
                    uid: "MultitestUID",
                    timer: {},
                    description: null,
                    tags: {},
                    status: "ready",
                    runtime_status: "running",
                    part: null,
                    status_override: null,
                    entry_uids: ["SuiteUID"],
                    parent_uids: ["TestplanUID"],
                    name: "MultitestName",
                    fix_spec_path: null,
                    hash: 22222,
                  },
                ],
              })
              .then(() => {
                moxios.wait(() => {
                  const request = moxios.requests.mostRecent();
                  expect(request.url).toBe(
                    "/api/v1/interactive/report/tests/MultitestUID/suites"
                  );
                  request
                    .respondWith({
                      status: 200,
                      response: [
                        {
                          category: "testsuite",
                          uid: "SuiteUID",
                          timer: {},
                          description: null,
                          tags: {},
                          runtime_status: "ready",
                          status: "running",
                          part: null,
                          status_override: null,
                          entry_uids: ["test_basic_assertions"],
                          parent_uids: ["TestplanUID", "MultitestUID"],
                          name: "SuiteName",
                          fix_spec_path: null,
                          hash: 33333,
                        },
                      ],
                    })
                    .then(() => {
                      moxios.wait(() => {
                        const request = moxios.requests.mostRecent();
                        expect(request.url).toBe(
                          "/api/v1/interactive/report/tests/MultitestUID" +
                            "/suites/SuiteUID/testcases"
                        );
                        request
                          .respondWith({
                            status: 200,
                            response: [
                              {
                                category: "testcase",
                                uid: "TestcaseUID",
                                timer: {},
                                description: null,
                                tags: {},
                                type: "TestCaseReport",
                                status: "ready",
                                runtime_status: "running",
                                logs: [],
                                entries: [],
                                status_override: null,
                                name: "testcaseName",
                                parent_uids: [
                                  "TestplanUID",
                                  "MultitestUID",
                                  "SuiteUID",
                                ],
                                hash: 44444,
                              },
                            ],
                          })
                          .then(() => {
                            expect(interactiveReport).toMatchSnapshot();
                            done();
                          });
                      });
                    });
                });
              });
          });
        });
    });
  });

  it("Handles environment being started", (done) => {
    const interactiveReport = renderInteractiveReport();
    const report = PropagateIndices(initialReport());

    interactiveReport.setState({
      report: report,
    });
    interactiveReport.update();

    const clickedEntry = report.entries[0];
    const mockEvent = {
      stopPropagation: jest.fn(),
      preventDefault: jest.fn(),
    };
    interactiveReport
      .instance()
      .envCtrlCallback(mockEvent, clickedEntry, "start");

    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report/tests/MultiTestUID");
      expect(request.config.method).toBe("put");
      const putData = JSON.parse(request.config.data);
      expect(putData.uid).toBe(clickedEntry.uid);
      expect(putData.env_status).toBe("STARTING");

      request
        .respondWith({
          status: 200,
          response: putData,
        })
        .then(() => {
          expect(interactiveReport).toMatchSnapshot();
          done();
        });
    });
  });

  it("Resets testcase state", (done) => {
    const interactiveReport = renderInteractiveReport();

    const report = initialReport();
    const multitest = report.entries[0];
    expect(multitest.category).toBe("multitest");
    multitest.env_status = "STARTED";

    const testcase = report.entries[0].entries[0].entries[1];
    expect(testcase.category).toBe("testcase");

    // Add an assertion entry.
    testcase.entries = [
      {
        machine_time: "2020-01-28T17:27:46.134440+00:00",
        second: "foo",
        description: null,
        passed: true,
        meta_type: "assertion",
        type: "Equal",
        category: "DEFAULT",
        utc_time: "2020-01-28T17:27:46.134429+00:00",
        line_no: 24,
        label: "==",
        first: "foo",
      },
    ];

    interactiveReport.setState({
      report: report,
    });
    interactiveReport.update();
    interactiveReport.instance().resetReport();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report");
      expect(request.config.method).toBe("put");
      const putData = JSON.parse(request.config.data);

      request
        .respondWith({
          status: 200,
          response: putData,
        })
        .then(() => {
          moxios.wait(() => {
            const request = moxios.requests.mostRecent();
            expect(request.url).toBe("/api/v1/interactive/report");
            expect(request.config.method).toBe("put");
            const putData = JSON.parse(request.config.data);
            expect(putData.runtime_status).toBe("resetting");
            done();
          });
        });
    });
  });

  it("Run all tests", (done) => {
    const interactiveReport = renderInteractiveReport();

    const report = initialReport();
    const multitest = report.entries[0];
    expect(multitest.category).toBe("multitest");
    multitest.env_status = "STARTED";

    const suite_setup = report.entries[0].entries[0].entries[0];
    expect(suite_setup.category).toBe("synthesized");
    const testcase = report.entries[0].entries[0].entries[1];
    expect(testcase.category).toBe("testcase");

    interactiveReport.setState({
      filteredReport: {
        report: report,
        filter: {text: null}
      },
    });
    interactiveReport.update();
    interactiveReport.instance().runAll();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report");
      expect(request.config.method).toBe("put");
      const putData = JSON.parse(request.config.data);

      request
        .respondWith({
          status: 200,
          response: putData,
        })
        .then(() => {
          moxios.wait(() => {
            const request = moxios.requests.mostRecent();
            expect(request.url).toBe("/api/v1/interactive/report");
            expect(request.config.method).toBe("put");
            const putData = JSON.parse(request.config.data);
            expect(putData.runtime_status).toBe("running");
            expect(putData.entries).not.toBeDefined();
            done();
          });
        });
    });
  });

  it("Run filtered tests", (done) => {
    const interactiveReport = renderInteractiveReport();

    const report = initialReport();
    const multitest = report.entries[0];
    expect(multitest.category).toBe("multitest");
    multitest.env_status = "STARTED";

    const testcase = report.entries[0].entries[0].entries[1];
    expect(testcase.category).toBe("testcase");

    interactiveReport.setState({
      filteredReport: {
        report: report,
        filter: {text: "something"}
      },
    });
    interactiveReport.update();
    interactiveReport.instance().runAll();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report");
      expect(request.config.method).toBe("put");
      const putData = JSON.parse(request.config.data);

      request
        .respondWith({
          status: 200,
          response: putData,
        })
        .then(() => {
          moxios.wait(() => {
            const request = moxios.requests.mostRecent();
            expect(request.url).toBe("/api/v1/interactive/report");
            expect(request.config.method).toBe("put");
            const putData = JSON.parse(request.config.data);
            expect(putData.runtime_status).toBe("running");
            expect(putData.entries).toHaveLength(1);
            expect(putData.entries[0].name).toBe("MultiTestName");
            done();
          });
        });
    });
  });
});
