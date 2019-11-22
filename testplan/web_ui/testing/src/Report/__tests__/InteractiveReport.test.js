/* Tests the InteractiveReport component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import moxios from 'moxios';

import InteractiveReport from '../InteractiveReport.js';
import {FakeInteractiveReport} from '../../Common/sampleReports.js';
import {ReportToNavEntry} from '../../Common/utils.js';

const INITIAL_REPORT = {
  "uid": "Assertions Example",
  "timer": {},
  "status": "ready",
  "meta": {},
  "status_override": null,
  "attachments": {},
  "tags_index": {},
  "name": "Assertions Example",
  "parent_uids": [],
  "type": "TestGroupReport",
  "category": "testplan",
  "entries": [{
    "uid": "Assertions Test",
    "timer": {},
    "description": null,
    "tags": {},
    "status": "ready",
    "part": null,
    "status_override": null,
    "category": "multitest",
    "name": "Assertions Test",
    "fix_spec_path": null,
    "parent_uids": ["Assertions Example"],
    "type": "TestGroupReport",
    "category": "multitest",
    "entries": [{
      "uid": "SampleSuite",
      "timer": {},
      "description": null,
      "tags": {},
      "status": "ready",
      "part": null,
      "status_override": null,
      "category": "suite",
      "name": "SampleSuite",
      "fix_spec_path": null,
      "parent_uids": ["Assertions Example", "Assertions Test"],
      "type": "TestGroupReport",
      "category": "suite",
      "entries": [{
        "uid": "test_basic_assertions",
        "timer": {},
        "description": null,
        "tags": {},
        "type": "TestCaseReport",
        "status": "ready",
        "logs": [],
        "suite_related": false,
        "entries": [],
        "status_override": null,
        "name": "test_basic_assertions",
        "type": "TestCaseReport",
        "parent_uids": [
          "Assertions Example", "Assertions Test", "SampleSuite",
        ],
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
          "uid": "Assertions Example",
          "timer": {},
          "status": "ready",
          "meta": {},
          "entry_uids": [
            "Assertions Test"
          ],
          "parent_uids": [],
          "status_override": null,
          "attachments": {},
          "tags_index": {},
          "name": "Assertions Example"
        },
      }).then(() => {
        moxios.wait(() => {
          const request = moxios.requests.mostRecent();
          expect(request.url).toBe("/api/v1/interactive/report/tests");
          request.respondWith({
            status: 200,
            response: [
              {
                "uid": "Assertions Test",
                "timer": {},
                "description": null,
                "tags": {},
                "status": "ready",
                "part": null,
                "status_override": null,
                "category": "multitest",
                "entry_uids": [
                  "SampleSuite"
                ],
                "parent_uids": ["Assertions Example"],
                "name": "Assertions Test",
                "fix_spec_path": null
              }
            ]
          }).then(() => {
            moxios.wait(() => {
              const request = moxios.requests.mostRecent();
              expect(request.url).toBe(
                "/api/v1/interactive/report/tests/Assertions Test/suites"
              );
              request.respondWith({
                status: 200,
                response: [{
                  "uid": "SampleSuite",
                  "timer": {},
                  "description": null,
                  "tags": {},
                  "status": "ready",
                  "part": null,
                  "status_override": null,
                  "category": "suite",
                  "entry_uids": [
                    "test_basic_assertions",
                  ],
                  "parent_uids": ["Assertions Example", "Assertions Test"],
                  "name": "SampleSuite",
                  "fix_spec_path": null
                }]
              }).then(() => {
                moxios.wait(() => {
                  const request = moxios.requests.mostRecent();
                  expect(request.url).toBe(
                    "/api/v1/interactive/report/tests/Assertions Test"
                    + "/suites/SampleSuite/testcases"
                  );
                  request.respondWith({
                    status: 200,
                    response: [{
                      "uid": "test_basic_assertions",
                      "timer": {},
                      "description": null,
                      "tags": {},
                      "type": "TestCaseReport",
                      "status": "ready",
                      "logs": [],
                      "suite_related": false,
                      "entries": [],
                      "status_override": null,
                      "name": "test_basic_assertions",
                      "parent_uids": [
                        "Assertions Example", "Assertions Test", "SampleSuite",
                      ],
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
      selected: interactiveReport.instance().autoSelect(INITIAL_REPORT),
    });
    interactiveReport.update();
    expect(interactiveReport.state("selected")).toStrictEqual([
      {uid: "Assertions Example", type: "testplan"}
    ]);

    const mockEvent = {stopPropagation: jest.fn()};
    interactiveReport.instance().handleNavClick(
      mockEvent,
      {uid: "Assertions Test", type: "TestGroupReport", category: "multitest"},
      1,
    );
    interactiveReport.update();

    expect(interactiveReport.state("selected")).toStrictEqual([
      {uid: "Assertions Example", type: "testplan"},
      {uid: "Assertions Test", type: "multitest"},
    ]);
    expect(interactiveReport).toMatchSnapshot();
  });

  const testRunEntry = (done, clickedEntry, expectedURL) => {
    const interactiveReport = shallow(<InteractiveReport />);
    interactiveReport.setState({
      report: INITIAL_REPORT,
      selected: interactiveReport.instance().autoSelect(INITIAL_REPORT),
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
    {uid: "Assertions Test", parent_uids: ["Assertions Example"]},
    "/api/v1/interactive/report/tests/Assertions Test",
  ));

  it("handles individual test suites being run", done => testRunEntry(
    done,
    {
      uid: "SampleSuite",
      parent_uids: ["Assertions Example", "Assertions Test"],
    },
    "/api/v1/interactive/report/tests/Assertions Test/suites/SampleSuite",
  ));

  it("handles individual testcases being run", done => testRunEntry(
    done,
    {
      uid: "test_basic_assertions",
      parent_uids: ["Assertions Example", "Assertions Test", "SampleSuite"],
    },
    "/api/v1/interactive/report/tests/Assertions Test/suites/SampleSuite"
    + "/testcases/test_basic_assertions",
  ));

});

