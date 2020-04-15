/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { render } from 'react-dom';
import { act, Simulate } from 'react-dom/test-utils';
import { StyleSheetTestUtils } from 'aphrodite';
import _shuffle from 'lodash/shuffle';

import useReportState from '../../hooks/useReportState';
jest.mock('../../hooks/useReportState');

describe('HelpButton', () => {

  const expectedArgs = [
    'app.reports.batch.isShowHelpModal',
    'setAppBatchReportShowHelpModal'
  ];
  const mkSetShowHelpModal = () => jest.fn().mockName(expectedArgs[1]);
  const clickTgtQuery = 'span';

  describe.each(_shuffle([
    [ true, mkSetShowHelpModal() ],
    [ false, mkSetShowHelpModal() ],
  ]))(
    `{ [ %O, %p ] = useReportState(...${JSON.stringify(expectedArgs)}) }`,
    (isShowHelpModal, setShowHelpModal) => {

      beforeEach(() => {
        StyleSheetTestUtils.suppressStyleInjection();
        global.container = global.document.createElement('div');
        global.document.body.appendChild(global.container);
        useReportState.mockReturnValue([ isShowHelpModal, setShowHelpModal ])
          .mockName('useReportState');
        jest.isolateModules(() => {
          const { default: HelpButton } = require('../HelpButton');
          act(() => {
            render(<HelpButton/>, global.container);
          });
        });
      });

      afterEach(() => {
        StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
        global.document.body.removeChild(global.container);
        global.container = null;
        jest.resetAllMocks();
      });

      it("correctly renders + calls hook & runs no event handlers", () => {
        expect(global.container).toMatchSnapshot();
        expect(useReportState).toHaveBeenCalledTimes(1);
        expect(useReportState).toHaveBeenLastCalledWith(...expectedArgs);
        expect(setShowHelpModal).not.toHaveBeenCalled();
      });

      describe(`<${clickTgtQuery.toUpperCase()}> onClick event`, () => {
        beforeEach(() => {
          Simulate.click(global.container.querySelector(clickTgtQuery));
        });
        it('correctly renders & handles onClick', () => {
          expect(global.container).toMatchSnapshot();
          expect(setShowHelpModal).toHaveBeenCalledTimes(1);
          expect(setShowHelpModal).not
            .toHaveBeenLastCalledWith(isShowHelpModal);
          expect(useReportState).toHaveBeenCalledTimes(1);
          expect(useReportState).toHaveBeenLastCalledWith(...expectedArgs);
        });
      });
    },
  );
});
