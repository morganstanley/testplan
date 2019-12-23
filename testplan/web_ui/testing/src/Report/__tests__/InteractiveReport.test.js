/* Tests the InteractiveReport component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import moxios from 'moxios';

import InteractiveReport from '../InteractiveReport.js';
import {FakeInteractiveReport} from '../../Common/sampleReports.js';

const INITIAL_REPORT = {
  "category": "testplan",
  "uid": "TestplanUID",
  "timer": {},
  "status": "ready",
  "env_status": null,
  "meta": {},
  "status_override": null,
  "attachments": {},
  "tags_index": {},
  "name": "TestplanName",
  "parent_uids": [],
  "type": "TestGroupReport",
  "hash": 12345,
  "entries": [{
    "category": "multitest",
    "uid": "MultiTestUID",
    "timer": {},
    "description": null,
    "tags": {},
    "status": "ready",
    "env_status": "STOPPED",
    "part": null,
    "status_override": null,
    "name": "MultiTestName",
    "fix_spec_path": null,
    "parent_uids": ["TestplanUID"],
    "type": "TestGroupReport",
    "category": "multitest",
    "hash": 12345,
    "entries": [{
      "category": "suite",
      "uid": "SuiteUID",
      "timer": {},
      "description": null,
      "tags": {},
      "status": "ready",
      "env_status": null,
      "part": null,
      "status_override": null,
      "name": "SuiteName",
      "fix_spec_path": null,
      "parent_uids": ["TestplanUID", "MultiTestUID"],
      "type": "TestGroupReport",
      "category": "suite",
      "hash": 12345,
      "entries": [{
        "category": "testcase",
        "uid": "testcaseUID",
        "timer": {},
        "description": null,
        "tags": {},
        "type": "TestCaseReport",
        "status": "ready",
        "env_status": null,
        "logs": [],
        "suite_related": false,
        "entries": [],
        "status_override": null,
        "name": "testcaseName",
        "type": "TestCaseReport",
        "parent_uids": [
          "TestplanUID", "MultiTestUID", "SuiteUID",
        ],
        "hash": 12345,
      }],
    }],
  }],
};


describe('InteractiveReport', () => {
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

  it("Loads report skeleton when mounted", done => {
    const interactiveReport = shallow(<InteractiveReport />);
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report");
      request.respondWith({
        status: 200,
        response: {
          "category": "testplan",
          "uid": "TestplanUID",
          "timer": {},
          "status": "ready",
          "meta": {},
          "entry_uids": [
            "MultiTestUID"
          ],
          "parent_uids": [],
          "status_override": null,
          "attachments": {},
          "tags_index": {},
          "name": "TestplanName",
          "hash": 12345,
        },
      }).then(() => {
        moxios.wait(() => {
          const request = moxios.requests.mostRecent();
          expect(request.url).toBe("/api/v1/interactive/report/tests");
          request.respondWith({
            status: 200,
            response: [
              {
                "category": "multitest",
                "uid": "MultiTestUID",
                "timer": {},
                "description": null,
                "tags": {},
                "status": "ready",
                "part": null,
                "status_override": null,
                "entry_uids": [
                  "SuiteUID"
                ],
                "parent_uids": ["TestplanUID"],
                "name": "MultitestName",
                "fix_spec_path": null,
                "hash": 12345,
              }
            ]
          }).then(() => {
            moxios.wait(() => {
              const request = moxios.requests.mostRecent();
              expect(request.url).toBe(
                "/api/v1/interactive/report/tests/MultiTestUID/suites"
              );
              request.respondWith({
                status: 200,
                response: [{
                  "category": "suite",
                  "uid": "SuiteUID",
                  "timer": {},
                  "description": null,
                  "tags": {},
                  "status": "ready",
                  "part": null,
                  "status_override": null,
                  "entry_uids": [
                    "testcaseUID",
                  ],
                  "parent_uids": ["TestplanUID", "MultitestUID"],
                  "name": "SuiteName",
                  "fix_spec_path": null,
                  "hash": 12345,
                }]
              }).then(() => {
                moxios.wait(() => {
                  const request = moxios.requests.mostRecent();
                  expect(request.url).toBe(
                    "/api/v1/interactive/report/tests/MultiTestUID"
                    + "/suites/SuiteUID/testcases"
                  );
                  request.respondWith({
                    status: 200,
                    response: [{
                      "category": "testcase",
                      "uid": "testcaseUID",
                      "timer": {},
                      "description": null,
                      "tags": {},
                      "type": "TestCaseReport",
                      "status": "ready",
                      "logs": [],
                      "suite_related": false,
                      "entries": [],
                      "status_override": null,
                      "name": "testcaseName",
                      "parent_uids": [
                        "TestplanUID", "MultiTestUID", "SuiteUID",
                      ],
                      "hash": 12345,
                    }]
                  }).then(() => {
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

  it("handles navigation entries being clicked", () => {
    const interactiveReport = shallow(<InteractiveReport />);
    interactiveReport.setState({
      report: INITIAL_REPORT,
      selectedUIDs: interactiveReport.instance().autoSelect(INITIAL_REPORT),
    });
    interactiveReport.update();
    expect(interactiveReport.state("selectedUIDs")).toStrictEqual([
      INITIAL_REPORT.uid,
    ]);

    const mockEvent = {stopPropagation: jest.fn()};
    interactiveReport.instance().handleNavClick(
      mockEvent,
      INITIAL_REPORT.entries[0],
      1,
    );
    interactiveReport.update();

    expect(interactiveReport.state("selectedUIDs")).toStrictEqual([
      INITIAL_REPORT.uid,
      INITIAL_REPORT.entries[0].uid,
    ]);
    expect(interactiveReport).toMatchSnapshot();
  });

  const testRunEntry = (done, clickedEntry, expectedURL) => {
    const interactiveReport = shallow(<InteractiveReport />);
    interactiveReport.setState({
      report: INITIAL_REPORT,
      selectedUIDs: interactiveReport.instance().autoSelect(INITIAL_REPORT),
    });
    interactiveReport.update();

    const mockEvent = {stopPropagation: jest.fn()};
    interactiveReport.instance().handlePlayClick(mockEvent, clickedEntry);

    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(expectedURL);
      expect(request.config.method).toBe("put");
      const putData = JSON.parse(request.config.data);
      expect(putData.uid).toBe(clickedEntry.uid);
      expect(putData.status).toBe("running");

      request.respondWith({
        status: 200,
        response: putData,
      }).then(() => {
        expect(interactiveReport).toMatchSnapshot();
        done();
      });
    });
  };

  it("handles tests being run", done => testRunEntry(
    done,
    INITIAL_REPORT.entries[0],
    "/api/v1/interactive/report/tests/MultiTestUID",
  ));

  it("handles individual test suites being run", done => testRunEntry(
    done,
    INITIAL_REPORT.entries[0].entries[0],
    "/api/v1/interactive/report/tests/MultiTestUID/suites/SuiteUID",
  ));

  it("handles individual testcases being run", done => testRunEntry(
    done,
    INITIAL_REPORT.entries[0].entries[0].entries[0],
    "/api/v1/interactive/report/tests/MultiTestUID/suites/SuiteUID"
    + "/testcases/testcaseUID",
  ));


  it("Parially refreshes the report on update.", done => {
    const interactiveReport = shallow(<InteractiveReport />);
    interactiveReport.setState({
      report: INITIAL_REPORT,
      selectedUIDs: interactiveReport.instance().autoSelect(INITIAL_REPORT),
    });
    interactiveReport.update();

    interactiveReport.instance().getReport();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report");
      const requestCount = moxios.requests.count();
      request.respondWith({
        status: 200,

        // Do not change the hash - no more API requests should be received.
        response: {
          "category": "testplan",
          "uid": "TestplanUID",
          "timer": {},
          "status": "ready",
          "meta": {},
          "entry_uids": [
            "MultitestUID"
          ],
          "parent_uids": [],
          "status_override": null,
          "attachments": {},
          "tags_index": {},
          "name": "TestplanName",
          "hash": 12345,
        },
      }).then(() => {
        moxios.wait(() => {
          expect(moxios.requests.count()).toBe(requestCount);
          expect(interactiveReport).toMatchSnapshot();
          done();
        });
      });
    });
  });


  it("Updates testcase state", done => {
    const interactiveReport = shallow(<InteractiveReport />);
    interactiveReport.setState({
      report: INITIAL_REPORT,
      selectedUIDs: interactiveReport.instance().autoSelect(INITIAL_REPORT),
    });
    interactiveReport.update();

    interactiveReport.instance().getReport();
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe("/api/v1/interactive/report");
      const requestCount = moxios.requests.count();
      request.respondWith({
        status: 200,

        response: {
          "category": "testplan",
          "uid": "TestplanUID",
          "timer": {},
          "status": "running",
          "meta": {},
          "entry_uids": [
            "MultitestUID"
          ],
          "parent_uids": [],
          "status_override": null,
          "attachments": {},
          "tags_index": {},
          "name": "TestplanName",
          "hash": 11111
        },
      }).then(() => {
        moxios.wait(() => {
          const request = moxios.requests.mostRecent();
          expect(request.url).toBe("/api/v1/interactive/report/tests");
          request.respondWith({
            status: 200,
            response: [
              {
                "category": "multitest",
                "uid": "MultitestUID",
                "timer": {},
                "description": null,
                "tags": {},
                "status": "running",
                "part": null,
                "status_override": null,
                "entry_uids": [
                  "SuiteUID"
                ],
                "parent_uids": ["TestplanUID"],
                "name": "MultitestName",
                "fix_spec_path": null,
                "hash": 22222
              }
            ]
          }).then(() => {
            moxios.wait(() => {
              const request = moxios.requests.mostRecent();
              expect(request.url).toBe(
                "/api/v1/interactive/report/tests/MultitestUID/suites"
              );
              request.respondWith({
                status: 200,
                response: [{
                  "category": "suite",
                  "uid": "SuiteUID",
                  "timer": {},
                  "description": null,
                  "tags": {},
                  "status": "running",
                  "part": null,
                  "status_override": null,
                  "entry_uids": [
                    "test_basic_assertions",
                  ],
                  "parent_uids": ["TestplanUID", "MultitestUID"],
                  "name": "SuiteName",
                  "fix_spec_path": null,
                  "hash": 33333
                }]
              }).then(() => {
                moxios.wait(() => {
                  const request = moxios.requests.mostRecent();
                  expect(request.url).toBe(
                    "/api/v1/interactive/report/tests/MultitestUID"
                    + "/suites/SuiteUID/testcases"
                  );
                  request.respondWith({
                    status: 200,
                    response: [{
                      "category": "testcase",
                      "uid": "TestcaseUID",
                      "timer": {},
                      "description": null,
                      "tags": {},
                      "type": "TestCaseReport",
                      "status": "running",
                      "logs": [],
                      "suite_related": false,
                      "entries": [],
                      "status_override": null,
                      "name": "testcaseName",
                      "parent_uids": [
                        "TestplanUID", "MultitestUID", "SuiteUID",
                      ],
                      "hash": 44444
                    }]
                  }).then(() => {
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

  it('Handles environment being started', done => {
    const interactiveReport = shallow(<InteractiveReport />);
    interactiveReport.setState({
      report: INITIAL_REPORT,
      selectedUIDs: interactiveReport.instance().autoSelect(INITIAL_REPORT),
    });
    interactiveReport.update();

    const clickedEntry = INITIAL_REPORT.entries[0];
    const mockEvent = {stopPropagation: jest.fn()};
    interactiveReport.instance().envCtrlCallback(
      mockEvent, clickedEntry, "start",
    );

    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      expect(request.url).toBe(
        "/api/v1/interactive/report/tests/MultiTestUID"
      );
      expect(request.config.method).toBe("put");
      const putData = JSON.parse(request.config.data);
      expect(putData.uid).toBe(clickedEntry.uid);
      expect(putData.env_status).toBe("STARTING");

      request.respondWith({
        status: 200,
        response: putData,
      }).then(() => {
        expect(interactiveReport).toMatchSnapshot();
        done();
      });
    });
  });
});

