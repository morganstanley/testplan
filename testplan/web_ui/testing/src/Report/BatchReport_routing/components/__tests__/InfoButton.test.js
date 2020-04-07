/// <reference types="jest" />
// @ts-nocheck
/* eslint-disable max-len */
import React from 'react';
import { render } from 'react-dom';
import { act } from 'react-dom/test-utils';
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
    `\{ [ %O, %p ] = useReportState(...${JSON.stringify(expectedArgs)}) \}`,
    (isShowInfoModal, setShowInfoModal) => {

      beforeEach(() => {
        StyleSheetTestUtils.suppressStyleInjection();
        self.container = self.document.createElement('div');
        self.document.body.appendChild(self.container);
        useReportState
          .mockReturnValue([ isShowInfoModal, setShowInfoModal ])
          .mockName('useReportState');
        jest.isolateModules(() => {
          const { default: InfoButton } = require('../InfoButton');
          act(() => {
            render(<InfoButton/>, self.container);
          });
        });
      });

      afterEach(() => {
        StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
        self.document.body.removeChild(self.container);
        self.container = null;
        jest.resetAllMocks();
      });

      it("correctly renders + calls hook & runs no event handlers", () => {
        expect(self.container).toMatchSnapshot();
        expect(useReportState).toHaveBeenCalledTimes(1);
        expect(useReportState).toHaveBeenLastCalledWith(...expectedArgs);
        expect(setShowInfoModal).not.toHaveBeenCalled();
      });

      describe(`<${clickTgtQuery.toUpperCase()}> onClick event`, () => {
        beforeEach(() => {
          act(() => {
            self.container.querySelector(clickTgtQuery).dispatchEvent(
              new MouseEvent('click', { bubbles: true })
            );
          });
        });
        it('correctly renders & handles onClick', () => {
          expect(self.container).toMatchSnapshot();
          expect(setShowInfoModal).toHaveBeenCalledTimes(1);
          expect(setShowInfoModal).not.toHaveBeenLastCalledWith(isShowInfoModal);
          expect(useReportState).toHaveBeenCalledTimes(1);
          expect(useReportState).toHaveBeenLastCalledWith(...expectedArgs);
        });
      });
    },
  );
});
