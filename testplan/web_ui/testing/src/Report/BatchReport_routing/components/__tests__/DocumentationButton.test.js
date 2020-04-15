/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { render } from 'react-dom';
import { act } from 'react-dom/test-utils';
import { StyleSheetTestUtils } from 'aphrodite';
import _shuffle from 'lodash/shuffle';

import useReportState from '../../hooks/useReportState';
jest.mock('../../hooks/useReportState');

describe('DocumentationButton', () => {

  const expectedArgs = [ 'documentation.url.external', false ];

  describe.each(_shuffle([
    [ 'http://www.example.com/behavior/base.aspx' ],
    [ 'http://www.example.com/' ],
    [ 'http://www.example.com/boot/acoustics.php?basin=arch' ],
    [ 'http://example.com/' ],
    [ 'https://attraction.example.com/' ],
    [ 'http://www.example.com/' ],
    [ 'https://www.randomlists.com/urls' ],
  ]))(
    `{ [ "%s" ] = useReportState(...${JSON.stringify(expectedArgs)}) }`,
    (docURL) => {

      beforeEach(() => {
        StyleSheetTestUtils.suppressStyleInjection();
        global.container = window.document.createElement('div');
        global.document.body.appendChild(global.container);
        useReportState.mockReturnValue([ docURL ])
          .mockName('useReportState');
        jest.isolateModules(() => {
          const {
            default: DocumentationButton
          } = require('../DocumentationButton');
          act(() => { render(<DocumentationButton/>, global.container); });
        });
      });

      afterEach(() => {
        StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
        global.document.body.removeChild(global.container);
        global.container = null;
        jest.resetAllMocks();
      });

      it("correctly renders + calls hook & runs no event handlers", () => {
        expect(global.container.querySelector('a').href).toBe(docURL);
        expect(global.container).toMatchSnapshot();
      });
    },
  );
});
