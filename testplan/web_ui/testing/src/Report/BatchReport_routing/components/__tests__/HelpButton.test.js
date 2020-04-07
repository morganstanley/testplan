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
    `\{ [ %O, %p ] = useReportState(...${JSON.stringify(expectedArgs)}) \}`,
    (isShowHelpModal, setShowHelpModal) => {

      beforeEach(() => {
        StyleSheetTestUtils.suppressStyleInjection();
        self.container = self.document.createElement('div');
        self.document.body.appendChild(self.container);
        useReportState
          .mockReturnValue([ isShowHelpModal, setShowHelpModal ])
          .mockName('useReportState');
        jest.isolateModules(() => {
          const { default: HelpButton } = require('../HelpButton');
          act(() => {
            render(<HelpButton/>, self.container);
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
        expect(setShowHelpModal).not.toHaveBeenCalled();
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
