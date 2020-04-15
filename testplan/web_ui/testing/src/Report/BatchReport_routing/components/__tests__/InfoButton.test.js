/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { render } from 'react-dom';
import { act, Simulate } from 'react-dom/test-utils';
import { StyleSheetTestUtils } from 'aphrodite';
import _shuffle from 'lodash/shuffle';

import useReportState from '../../hooks/useReportState';
jest.mock('../../hooks/useReportState');

describe('InfoButton', () => {

  const expectedArgs = [
    'app.reports.batch.isShowInfoModal',
    'setAppBatchReportShowInfoModal'
  ];
  const mkSetShowInfoModal = () => jest.fn().mockName(expectedArgs[1]);
  const clickTgtQuery = 'span';

  describe.each(_shuffle([
    [ true, mkSetShowInfoModal() ],
    [ false, mkSetShowInfoModal() ],
  ]))(
    `{ [ %O, %p ] = useReportState(...${JSON.stringify(expectedArgs)}) }`,
    (isShowInfoModal, setShowInfoModal) => {

      beforeEach(() => {
        StyleSheetTestUtils.suppressStyleInjection();
        global.container = global.document.createElement('div');
        global.document.body.appendChild(global.container);
        useReportState.mockReturnValue([ isShowInfoModal, setShowInfoModal ])
          .mockName('useReportState');
        jest.isolateModules(() => {
          const { default: InfoButton } = require('../InfoButton');
          act(() => { render(<InfoButton/>, global.container); });
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
        expect(setShowInfoModal).not.toHaveBeenCalled();
      });

      // this sub-suite is needed in order to have a second snapshot
      describe(`<${clickTgtQuery.toUpperCase()}> onClick event`, () => {
        it('correctly renders & handles onClick', () => {
          Simulate.click(global.container.querySelector(clickTgtQuery));
          expect(global.container).toMatchSnapshot();
          expect(setShowInfoModal).toHaveBeenCalledTimes(1);
          // eslint-disable-next-line max-len
          expect(setShowInfoModal).not.toHaveBeenLastCalledWith(isShowInfoModal);
          expect(useReportState).toHaveBeenCalledTimes(1);
          expect(useReportState).toHaveBeenLastCalledWith(...expectedArgs);
        });
      });
    },
  );
});
