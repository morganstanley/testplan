/** @jest-environment jsdom */
// @ts-nocheck
/* eslint-disable max-len */
import React from 'react';
import { shallow } from 'enzyme';
import { StyleSheetTestUtils } from 'aphrodite';
import _shuffle from 'lodash/shuffle';
import TopNavbar from '../TopNavbar';
import useReportState from '../../hooks/useReportState';

const fakeReportAssertions =
  require('../../../../__tests__/mocks/documents/fakeReportAssertions.json');
const TESTPLAN_REPORT =
  require('../../../../__tests__/mocks/documents/TESTPLAN_REPORT_2.json');

jest.mock('../../hooks/useReportState');

describe('TopNavbar', () => {

  const expectedArgs = [ 'app.reports.batch.jsonReport', false ];

  describe.each(_shuffle([
    [ fakeReportAssertions ],
    [ TESTPLAN_REPORT ],
  ]))(
    `{ [ %j ] = useReportState(...${JSON.stringify(expectedArgs)}) }`,
    (jsonReport) => {

      beforeEach(() => {
        StyleSheetTestUtils.suppressStyleInjection();
        global.container = global.document.createElement('div');
        Object.assign(global,{console:{...console,_err:console.error,error:jest.fn()}});
        global.document.body.appendChild(global.container);
        useReportState.mockReturnValue([ jsonReport ]).mockName('useReportState');
      });

      afterEach(() => {
        StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
        let[{error:{mock:{calls:c}},_err,warn:w},l]=[global.console,0];
        c.forEach((...a)=>a[0]?.match(/\buseContext\b/m)?l++:_err(...a));
        if(l)w(`${l} useContext warnings`);
        Object.assign(global,{console:{error:_err,_err:null,err:null}});
        global.document.body.removeChild(global.container);
        global.container = null;
        jest.resetAllMocks();
      });

      it('renders correctly', () => {
        const tree = shallow(<TopNavbar/>);
        expect(tree).toMatchSnapshot();
      });
    },
  );
});
