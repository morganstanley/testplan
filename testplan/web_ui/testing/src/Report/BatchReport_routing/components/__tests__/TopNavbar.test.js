/// <reference types="jest" />
// @ts-nocheck
/* eslint-disable max-len */
import React from 'react';
import { shallow } from 'enzyme';
import { StyleSheetTestUtils } from 'aphrodite';
import _shuffle from 'lodash/shuffle';
import TopNavbar from '../TopNavbar';

import {
  fakeReportAssertions, TESTPLAN_REPORT,
} from '../../../../Common/fakeReport'
import useReportState from '../../hooks/useReportState';
jest.mock('../../hooks/useReportState');

describe('TopNavbar', () => {
  const expectedArgs = [ 'app.reports.batch.jsonReport', false ];
  describe.each(_shuffle([ [ fakeReportAssertions ], [ TESTPLAN_REPORT ], ]))(
    `\{ [ %j ] = useReportState(...${JSON.stringify(expectedArgs)}) \}`,
    (jsonReport) => {
      beforeEach(() => {
        StyleSheetTestUtils.suppressStyleInjection();
        self.container = self.document.createElement('div');
        Object.assign(self,{console:{...console,_err:console.error,error:jest.fn()}});
        self.document.body.appendChild(self.container);
        useReportState.mockReturnValue([ jsonReport ]).mockName('useReportState');
      });
      afterEach(() => {
        StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
        let[{error:{mock:{calls:c}},_err,warn:w},l]=[self.console,0];
        c.forEach((...a)=>a[0]?.match(/\buseContext\b/m)?l++:_err(...a));
        if(l)w(`${l} useContext warnings`);
        Object.assign(self,{console:{error:_err,_err:null,err:null}});
        self.document.body.removeChild(self.container);
        self.container = null;
        jest.resetAllMocks();
      });
      it('renders correctly', () => {
        const tree = shallow(<TopNavbar/>);
        expect(tree).toMatchSnapshot();
      });
    },
  );
});
