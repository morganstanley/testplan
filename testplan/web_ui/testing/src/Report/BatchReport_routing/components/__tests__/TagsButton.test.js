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

describe('TagsButton', () => {

  const expectedArgs = [
    'app.reports.batch.isShowTags',
    'setAppBatchReportIsShowTags'
  ],
    mkSetShowTags = () => jest.fn().mockName(expectedArgs[1]),
    clickTgtQuery = 'span';

  describe.each(_shuffle([
    [ true, mkSetShowTags() ],
    [ false, mkSetShowTags() ],
  ]))(
    `\{ [ %O, %p ] = useReportState(...${JSON.stringify(expectedArgs)}) \}`,
    (isShowTags, setShowTags) => {

      beforeEach(() => {
        StyleSheetTestUtils.suppressStyleInjection();
        self.container = self.document.createElement('div');
        self.document.body.appendChild(self.container);
        useReportState
          .mockReturnValue([ isShowTags, setShowTags ])
          .mockName('useReportState');
        /**
         * This is necessary because TagsButton uses FontAwesomeIcon which
         * keeps internally a count of its uses and changes its <svg>
         * 'aria-labelledby' attribute depending upon that count, meaning the
         * tests using it are not independent, i.e. the order in which the tests
         * run determine what the snapshot will look like. This 'isolateModules'
         * effectively resets that internal count on each run.
         * @type {import("../TagsButton").default}
         */
        jest.isolateModules(() => {
          const { default: TagsButton } = require('../TagsButton');
          act(() => {
            render(<TagsButton/>, self.container);
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
        expect(setShowTags).not.toHaveBeenCalled();
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
          expect(setShowTags).toHaveBeenCalledTimes(1);
          expect(setShowTags).not.toHaveBeenLastCalledWith(isShowTags);
          expect(useReportState).toHaveBeenCalledTimes(1);
          expect(useReportState).toHaveBeenLastCalledWith(...expectedArgs);
        });
      });
    },
  );
});
