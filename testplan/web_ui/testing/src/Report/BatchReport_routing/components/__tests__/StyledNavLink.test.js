/** @jest-environment jsdom */
// @ts-nocheck
import '@testing-library/react/dont-cleanup-after-each';
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { StyleSheetTestUtils, css } from 'aphrodite';
import { Router } from 'react-router-dom';
import _shuffle from 'lodash/shuffle';
import _isEqual from 'lodash/isEqual';
import _zip from 'lodash/zip';
import _get from 'lodash/get';
import StyledNavLink from '../StyledNavLink';
import useReportState from '../../hooks/useReportState';
import {
  findAllDeep, filterObjectDeep, deriveURLPathsFromReport
} from '../../../../__tests__/fixtures/testUtils';
import { navUtilsStyles } from '../../style';
import { APP_BATCHREPORT_SELECTED_TEST_CASE } from '../../state/actionTypes';
import { createMemoryHistory, createLocation, createPath } from 'history';

jest.mock('../../hooks/useReportState');

function uidFromPathname2ObjPathMapCurrier(obj, pathname2ObjPathMap) {
  return pathname => {
    const maybeErr = new Error(`Can't get UID for report entry at ${pathname}`);
    const pathnameObjPath = pathname2ObjPathMap.get(pathname);
    if(!pathnameObjPath) throw maybeErr;
    const uidObjPath = pathnameObjPath.slice(0, -1).concat(['uid']);
    const uid = _get(obj, uidObjPath);
    if(!uid) throw maybeErr;
    return uid;
  };
}

const IS_ACTIVE_CLASSES = css(navUtilsStyles.navButtonInteract),
  TESTPLAN_REPORT_1 =
    require('../../../../__tests__/mocks/documents/TESTPLAN_REPORT_1.json'),
  TESTPLAN_REPORT_2 =
    require('../../../../__tests__/mocks/documents/TESTPLAN_REPORT_2.json'),
  TESTPLAN_REPORT_1_SLIM = filterObjectDeep(
    TESTPLAN_REPORT_1,
    [ 'name', 'uid', 'entries', 'category' ]
  ),
  TESTPLAN_REPORT_2_SLIM = filterObjectDeep(
    TESTPLAN_REPORT_2,
    [ 'name', 'uid', 'entries', 'category' ]
  ),
  pathname2ObjectPathMap_TPR1 = new Map(),
  TESTPLAN_REPORT_1_SLIM_URLS = deriveURLPathsFromReport(
    TESTPLAN_REPORT_1_SLIM,
    null,
    null,
    pathname2ObjectPathMap_TPR1
  ),
  TESTPLAN_REPORT_1_SLIM_UIDS = TESTPLAN_REPORT_1_SLIM_URLS.map(
    uidFromPathname2ObjPathMapCurrier(
      TESTPLAN_REPORT_1_SLIM,
      pathname2ObjectPathMap_TPR1
    )
  ),
  TESTPLAN_REPORT_1_SLIM_URLS_UIDS = _zip(
    TESTPLAN_REPORT_1_SLIM_URLS,
    TESTPLAN_REPORT_1_SLIM_UIDS,
  ),
  pathname2ObjectPathMap_TPR2 = new Map(),
  TESTPLAN_REPORT_2_SLIM_URLS = deriveURLPathsFromReport(
    TESTPLAN_REPORT_2_SLIM,
    null,
    null,
    pathname2ObjectPathMap_TPR2
  ),
  TESTPLAN_REPORT_2_SLIM_UIDS = TESTPLAN_REPORT_2_SLIM_URLS.map(
    uidFromPathname2ObjPathMapCurrier(
      TESTPLAN_REPORT_2_SLIM,
      pathname2ObjectPathMap_TPR2
    )
  ),
  TESTPLAN_REPORT_2_SLIM_URLS_UIDS = _zip(
    TESTPLAN_REPORT_2_SLIM_URLS,
    TESTPLAN_REPORT_2_SLIM_UIDS,
  ),
  TESTPLAN_REPORT_URL_UID_MAP = new Map(
    TESTPLAN_REPORT_1_SLIM_URLS_UIDS.concat(TESTPLAN_REPORT_2_SLIM_URLS_UIDS)
  );

/// make quintuplets:
/// [ <current pathname+querystring>, <linked-to pathname>, <curr-UID>, <linked-to-UID>, <0-index> ]
// current location.pathname
const startPathnames = Array.from(TESTPLAN_REPORT_URL_UID_MAP.keys());
// linked-to location.pathname: the last "to" location is ''
const destPathnames = startPathnames.slice(1).concat(['/']);
// random querystrings ('a'.charCodeAt(0) == 97), length is 1 less than others
const randomQSs = startPathnames.slice(1).map(
  (_, i) => `?${String.fromCharCode(97 + (i % 26))}=${i}`
);
// join each query string with each startPathnames, skipping the first
const startURLs = _zip(startPathnames, randomQSs.concat([''])).map(
  ([pth, qs]) => `${pth}${qs}`
);
const urlIdx = startURLs.map((_, i) => i);
const startUIDs = Array.from(TESTPLAN_REPORT_URL_UID_MAP.values());
const destUIDs = startUIDs.slice(1).concat(['']);
const URL_QUINTUPLETS = _zip(
  startURLs,  // current pathname+querystring
  destPathnames,  // linked-to pathname
  startUIDs,
  destUIDs,
  urlIdx,  // 0-index
);

// here we:
// > get all testcases from our mock reports
// > shuffle them with a null
// > remove duplicates
const SAMPLE_TESTCASES = _shuffle([ null ].concat(
  findAllDeep(
    TESTPLAN_REPORT_1_SLIM,
    { category: 'testcase' },
    [ 'entries' ],
  )
).concat(
  findAllDeep(
    TESTPLAN_REPORT_2_SLIM,
    { category: 'testcase' },
    [ 'entries' ],
  )
).filter(  // remove duplicates
  (el, i, arr) =>
    !arr.slice(i + 1).find(_el => _isEqual(_el, el))
));

global.env = {
  history: createMemoryHistory({
    initialEntries: [ '/' ],
    initialIndex: 1,
  }),
  hasRendered: false,
  wrapper: ({ children }) => (
    <Router history={global.env.history}>
      {children}
    </Router>
  ),
};

describe.each(SAMPLE_TESTCASES)(
  '<StyledNavLink .../> with report %j',
  (selectedTestCase) => {

    const expectedHookArgs = [ APP_BATCHREPORT_SELECTED_TEST_CASE ];

    beforeAll(() => {
      useReportState
        .mockName('useReportState')
        .mockReturnValue([ selectedTestCase ]);
      StyleSheetTestUtils.suppressStyleInjection();
    });

    describe.each(URL_QUINTUPLETS)(
      'current URL => linked-to pathname: %j => %j',
      (currURL, toPathname, currUID, toUID, iterationNum) => {

        beforeAll(() => {
          if(!global.env.hasRendered) {
            global.env.rendered = render((
              <StyledNavLink pathname={toPathname} dataUid={toUID} />
            ), {
              wrapper: global.env.wrapper,
            });
            global.env.hasRendered = true;
          } else {
            global.env.rendered.rerender((
              <StyledNavLink pathname={toPathname} dataUid={toUID}/>
            ), { wrapper: global.env.wrapper });
          }
          global.env.linkElem = null;
        });

        it('calls useReportState correctly', () => {
          // we call jest.resetAllMocks() so this might just be 1
          expect(useReportState).toHaveBeenCalledTimes(1);
          expect(useReportState).toHaveBeenLastCalledWith(...expectedHookArgs);
        });

        it('renders as expected', () => {
          expect(global.env.rendered.container).toMatchSnapshot();
        });

        it(`${
          iterationNum > 0 
            ? 'sent us to the URL we linked to previously while '
              + 'maintaining the query params' 
            : '(skipping)'
        }`, () => {
          if(iterationNum > 0) {
            const { pathname: expectedCurrPathname } = createLocation(currURL);
            // the previous query string should have been carried over
            const { search: prevQS } = global.env.history.entries.slice(-1)[0];
            expect(global.env.history.location).toEqual(
              expect.objectContaining({
                pathname: expectedCurrPathname,
                search: prevQS,
              })
            );
          }
        });

        it('has an anchor element correct href', () => {
          const anchors = global.env.rendered.container.querySelectorAll('a');
          expect(anchors).toHaveLength(1);
          // the component should have picked up our current query string
          // even though we didn't pass it in as props
          const expectedFullHref = createPath({
            pathname: toPathname,
            search: global.env.history.location.search,
          });
          expect(anchors[0]).toHaveAttribute('href', expectedFullHref);
          global.env.linkElem = anchors[0];
        });

        it('should react appropriately to a change in query params', () => {
          // it's expected that the change in location will trigger a rerender
          // and thus a change of the query params in the anchor's href
          expect(useReportState).toHaveBeenCalledTimes(1);  // no change
          global.env.history.push(currURL);
          const { search: expectedNewQueryParams } = createLocation(currURL);
          expect(global.env.linkElem).toHaveAttribute(
            'href', createPath({
              pathname: toPathname,
              search: expectedNewQueryParams,
            })
          );
          expect(useReportState).toHaveBeenCalledTimes(2);
        });

        const isCurrUID =
          selectedTestCase !== null && toUID === selectedTestCase.uid,
          repl1 = isCurrUID ? '' : 'in',
          repl2 = isCurrUID ? '=' : '!';
        it(`has ${repl1}active classes since testcase UID ${repl2}== currUID`,
          () => {
            if(isCurrUID) {
              expect(global.env.linkElem).toHaveClass(IS_ACTIVE_CLASSES);
            } else {
              expect(global.env.linkElem).not.toHaveClass(IS_ACTIVE_CLASSES);
            }
          },
        );

        it("doesn't malfunction when we click the link", () => {
          expect(useReportState).toHaveBeenCalledTimes(2);  // no change
          fireEvent.click(global.env.linkElem);
          // should rerender since location changed twice
          // and it's using `useLocation`
          expect(useReportState).toHaveBeenCalledTimes(3);
        });

        afterAll(() => {
          jest.clearAllMocks();
          delete global.env.linkElem;
        });

      });

    afterAll(() => {
      StyleSheetTestUtils.clearBufferAndResumeStyleInjection();
      jest.resetAllMocks();
      global.env.rendered.cleanup();
    });

  },
);
