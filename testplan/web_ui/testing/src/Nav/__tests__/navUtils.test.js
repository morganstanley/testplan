import React from 'react';

import {ParseNavSelection} from '../navUtils';
import {TESTPLAN_REPORT} from '../../Common/sampleReports';

describe('BatchReport/navUtils', () => {

  describe('ParseNavSelection', () => {

    it('nothing selected - returns empty nav_breadcrumbs & top level ' +
       'entry in nav_list.', () => {
      const selected = [];
      const selection = ParseNavSelection([TESTPLAN_REPORT], selected);

      // There should be no breadcrumbs as nothing has been selected.
      expect(selection.navBreadcrumbs.length).toEqual(0);

      // The list should contain the top level entry (testplan entry) as nothing
      // has been selected.
      expect(selection.navList.length).toEqual(1);
      expect(selection.navList[0].uid).toEqual(TESTPLAN_REPORT.uid);
    });

    it('non testcase selected - returns selected entries in nav_breadcrumbs ' +
       '& last selected entry\'s children in nav_list.', () => {
      const selected = [{uid: TESTPLAN_REPORT.uid, type: 'testplan'},
                        {uid: TESTPLAN_REPORT.entries[0].uid, type: 'multitest'}];
      const selection = ParseNavSelection([TESTPLAN_REPORT], selected);

      // The breadcrumbs should contain all of the selected entries.
      expect(selection.navBreadcrumbs.length).toEqual(2);
      expect(selection.navBreadcrumbs[0].uid).toEqual(selected[0].uid);
      expect(selection.navBreadcrumbs[1].uid).toEqual(selected[1].uid);

      // The list should contain all of the children of the last selected
      // entry.
      const suites = TESTPLAN_REPORT.entries[0].entries;
      expect(selection.navList.length).toEqual(2);
      expect(selection.navList[0].uid).toEqual(suites[0].uid);
      expect(selection.navList[1].uid).toEqual(suites[1].uid);
    });

    it('testcase selected - returns non testcase selected entries in ' +
       'nav_breadcrumbs & second to last selected entry\'s children in ' +
       'nav_list.', () => {
      const selected = [
        {uid: TESTPLAN_REPORT.uid, type: 'testplan'},
        {uid: TESTPLAN_REPORT.entries[0].uid, type: 'multitest'},
        {uid: TESTPLAN_REPORT.entries[0].entries[0].uid, type: 'suite'},
        {uid: TESTPLAN_REPORT.entries[0].entries[0].entries[0].uid, type: 'testcase'}
      ];
      const selection = ParseNavSelection([TESTPLAN_REPORT], selected);

      // The breadcrumbs should contain all but the last selected entry as it
      // is a testcase. These never go into the breadcrumbs.
      expect(selection.navBreadcrumbs.length).toEqual(3);
      expect(selection.navBreadcrumbs[0].uid).toEqual(selected[0].uid);
      expect(selection.navBreadcrumbs[1].uid).toEqual(selected[1].uid);
      expect(selection.navBreadcrumbs[2].uid).toEqual(selected[2].uid);

      // The list should contain all of the children of the second to last
      // selected entry, as the last selected entry is a testcase.
      const testcases = TESTPLAN_REPORT.entries[0].entries[0].entries;
      expect(selection.navList.length).toEqual(2);
      expect(selection.navList[0].uid).toEqual(testcases[0].uid);
      expect(selection.navList[1].uid).toEqual(testcases[1].uid);
    });

    it('testcase selected - attaches correct assertions to testcases in nav_list.', () => {
      const selected = [
        {uid: TESTPLAN_REPORT.uid, type: 'testplan'},
        {uid: TESTPLAN_REPORT.entries[0].uid, type: 'multitest'},
        {uid: TESTPLAN_REPORT.entries[0].entries[0].uid, type: 'suite'},
        {uid: TESTPLAN_REPORT.entries[0].entries[0].entries[0].uid, type: 'testcase'}
      ];
      const selection = ParseNavSelection([TESTPLAN_REPORT], selected);

      // The testcase entries in the list should have the assertion data
      // so it can be passed to the AssertionPane.
      const firstTestcaseAssertions = TESTPLAN_REPORT.entries[0].entries[0].entries[0].entries;
      const secondTestcaseAssertions = TESTPLAN_REPORT.entries[0].entries[0].entries[1].entries;
      expect(selection.navList[0].entries).toEqual(firstTestcaseAssertions);
      expect(selection.navList[1].entries).toEqual(secondTestcaseAssertions);
    });

  });

});
