/* Tests the InteractiveReport component. */
import React from 'react';
import {shallow} from 'enzyme';
import {StyleSheetTestUtils} from "aphrodite";
import moxios from 'moxios';

import InteractiveReport from '../InteractiveReport.js';
import {FakeInteractiveReport} from '../../Common/sampleReports.js';
import {ReportToNavEntry} from '../../Common/utils.js';

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
											"name": "test_basic_assertions"
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
});
