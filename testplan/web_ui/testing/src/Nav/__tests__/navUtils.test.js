import React from 'react';
import {StyleSheetTestUtils} from "aphrodite";

import {CreateNavButtons, GetSelectedUid, applyNamedFilter} from '../navUtils';
import {TESTPLAN_REPORT} from '../../Common/sampleReports';
import { PropagateIndices } from '../../Report/reportUtils';

describe('navUtils', () => {

  describe('CreateNavButtons', () => {

    beforeEach(() => {
      // Stop Aphrodite from injecting styles, this crashes the tests.
      StyleSheetTestUtils.suppressStyleInjection();
    });

    afterEach(() => {
      // Resume style injection once test is finished.
      StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
    });

    const entries = PropagateIndices(TESTPLAN_REPORT).entries

    it('returns an array of nav buttons', () => {
      const props = {
        breadcrumbLength: 1,
        displayTags: false,
        displayTime: false,
        displayEmpty: true,
        handleNavClick: jest.fn(),
        entries: entries,
        filter: null,
        url: "/testplan/:uid/:selection*"
      }
      const createEntryComponent = jest.fn();

      const navButtons = CreateNavButtons(
        props, createEntryComponent
      );
      expect(navButtons.length).toBe(props.entries.length);
      expect(navButtons).toMatchSnapshot();
    });
  });

  describe('GetSelectedUid', () => {
    it('gets the selected UID', () => {
      const selected = [TESTPLAN_REPORT];
      const uid = GetSelectedUid(selected);
      expect(uid).toBe(TESTPLAN_REPORT.uid);
    });
  });

  describe('FilterFailedOrError', () => {
    it('filters failed or error', () => {
      const entries = [
        {
        "counter": {
                "passed": 1,
                "failed": 0,
                "total": 1,
        },
        "status": "passed",
        },
        {
        "counter": {
            "passed": 0,
            "failed": 1,
            "total": 1,
        },
        "status": "failed",
        },
        {
        "counter": {
            "passed": 0,
            "failed": 0,
            "total": 1,
            "error": 1
        },
        "status": "error",
        }];

      const filteredResult = applyNamedFilter(entries, 'fail');
      const expectedfilteredResult = [
        {
        "counter": {
            "passed": 0,
            "failed": 1,
            "total": 1,
        },
        "status": "failed",
        },
        {
        "counter": {
            "passed": 0,
            "failed": 0,
            "total": 1,
            "error": 1
        },
        "status": "error",
        }];
      expect(filteredResult).toStrictEqual(expectedfilteredResult);
    });
  });

});

