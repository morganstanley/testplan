/** @jest-environment jsdom */
// @ts-nocheck
import React from 'react';
import { act, cleanup, renderHook } from 'react-hooks-testing-library';
import _at from 'lodash/at';
import _shuffle from 'lodash/shuffle';
import uriComponentCodec from '../../utils/uriComponentCodec';
import useReportState from '../useReportState';
import ReportStateProvider from '../../state/ReportStateProvider';
import * as actionTypes from '../../state/actionTypes';
import actionCreators from '../../state/actionCreators';
import defaultState from '../../state/defaultState';
import {
  randomSamples, getPaths,
} from '../../../../__tests__/fixtures/testUtils';

const HookWrapper = props => (<ReportStateProvider {...props} />);

describe("'useReportState' hook", () => {

  afterEach(cleanup);
  const ALL_STATE_PATH_STRINGS = getPaths(defaultState);
  const ALL_STATE_PATH_ARRAYS = getPaths(defaultState, true);
  const ALL_ACTION_CREATOR_PATH_STRINGS = getPaths(actionCreators);
  const ALL_ACTION_CREATOR_PATH_ARRAYS = getPaths(actionCreators, true);

  it("returns null state and dispatchers when passed (false, false)", () => {
    const { result } = renderHook(
      () => useReportState(false, false),
      { wrapper: HookWrapper },
    );
    expect(result.error).toBeFalsy();
    const [ state, actionDispatch ] = result.current;
    expect(state).toBeNull();
    expect(actionDispatch).toBeNull();
  });

  it(
    "returns full state and dispatchers when passed (undefined, undefined)",
    () => {
      const { result } = renderHook(
        () => useReportState(),
        { wrapper: HookWrapper },
      );
      expect(result.error).toBeFalsy();
      const [ state, actionDispatchers ] = result.current;
      expect(state).toStrictEqual(defaultState);

      // the action dispatchers object has an extra raw "dispatch" function
      const actionDispatcherSansDispatchNames =
        Object.keys(actionDispatchers).filter(nm => nm !== 'dispatch');
      actionDispatcherSansDispatchNames.sort();
      const actionCreatorNames = Object.keys(actionCreators);
      actionCreatorNames.sort();
      expect(actionDispatcherSansDispatchNames).toEqual(actionCreatorNames);

      // check that the dispatchers take the same number of args as the creators
      const actionDispatcherSansDispatchNArgs =
        actionDispatcherSansDispatchNames
          .map(nm => actionDispatchers[nm].length);
      const actionCreatorNArgs =
        actionCreatorNames
          .map(nm => actionDispatchers[nm].length);
      expect(actionDispatcherSansDispatchNArgs).toEqual(actionCreatorNArgs);
    },
  );

  describe('first returned value (state)', () => {

    it("returns the entire state when passed 'undefined''", () => {
      const { result } = renderHook(
        () => useReportState(undefined, false),
        { wrapper: HookWrapper },
      );
      expect(result.error).toBeFalsy();
      const [ state, actionDispatchers ] = result.current;
      expect(actionDispatchers).toBeNull();
      expect(state).toStrictEqual(defaultState);
    });

    describe.each([
      /** ALL_STATE_PATH_STRINGS looks like [ 'a.b', 'a.b.c', ...] */
      ['string', ALL_STATE_PATH_STRINGS],
      /** ALL_STATE_PATH_ARRAYS looks like [ ['a', 'b'], ['a', 'b', 'c'], ... ] */
      ['array', ALL_STATE_PATH_ARRAYS],
    ])('slicers passed as %s',
      (tp, slicers) => {

        /**
         * Jest will implicitly convert a depth-1 array into an array-of-arrays
         * which will break our tests unless we ensure no depth-1 arrays are
         * passed to our it.each() tests.
         * @example
         * // After this conversion we should have:
         * [
         *   [
         *     'a.b'    // passed to 1st it.each
         *   ],
         *   [
         *     'a.b.c'  // passed to 2nd it.each
         *   ],
         *   ...        // and so on
         * ]
         * // or
         * [
         *   [ 
         *     [['a','b']]      // passed to 1st it.each 
         *   ],
         *   [
         *     [['a','b','c']]  // passed to 2nd it.each
         *   ],
         *   ...                // and so on
         * ]
         * @see https://jestjs.io/docs/en/api#testeachtablename-fn-timeout
         * @type {Array<string[]> | Array<Array<string[]>>}
         */
        const RESOLVED_SLICERS =
          slicers.map(v => [ tp === 'string' ? v : [v] ]);

        /**
         * Each `stateSlicer` is:
         * 'a.b.c'
         * -or-
         * [['a','b','c']]
         */
        it.each(RESOLVED_SLICERS)(
          'yields correct state slice when passed a single path %j',
          (stateSlicer) => {

            const { result, rerender } = renderHook(
              () => useReportState(stateSlicer, false),
              { wrapper: HookWrapper },
            );
            expect(result.error).toBeFalsy();
            const [ stateSlice1, actionDispatchers1 ] = result.current;
            expect(actionDispatchers1).toBeNull();

            expect(stateSlice1).not.toBeInstanceOf(Array);
            // nothings been dispatched so everything should be at its default
            const defaultStateSlice = _at(defaultState, stateSlicer)[0];
            expect(stateSlice1).toStrictEqual(defaultStateSlice);

            rerender([ stateSlicer ], false);
            expect(result.error).toBeFalsy();
            const [ stateSlice2, actionDispatchers2 ] = result.current;
            expect(actionDispatchers2).toBeNull();

            // passing a singleton array should yield the same value as just
            // passing the array's single value itself
            expect(stateSlice2).toStrictEqual(stateSlice1);
          },
        );

        /**
         * For the same reasons as in `RESOLVED_SLICERS` we apply a
         * transformation to yield:
         * [
         *   [
         *     ['a.b', 'a.b.c', ...]  // passed to 1st it.each
         *   ],
         *   [
         *     ['a', 'a.b.c.d', ...]  // passed to 2nd it.each
         *   ],
         *   ...                      // and so on
         * ]
         * -or-
         * [
         *   [
         *     [['a','b'], ['a','b','c'], ...]  // passed to 1st it.each
         *   ],
         *   [
         *     [['a'], ['a','b','c','d'], ...]  // passed to 2nd it.each
         *   ],
         *   ...                                 // and so on
         * ]
         */
        const RESOLVED_SLICER_SAMPLES =
          randomSamples(slicers, 10, 2).map(v => [ v ]);

        /**
         * Each `stateSlicerArr` is:
         * ['a.b', 'a.b.c', ...]
         * -or-
         * [['a','b'], ['a','b','c'], ...]
         */
        it.each(RESOLVED_SLICER_SAMPLES)(
          `yields correct state slices when passed multiple paths %j`,
          (stateSlicerArr) => {

            const { result } = renderHook(
              () => useReportState(stateSlicerArr, false),
              { wrapper: HookWrapper },
            );
            expect(result.error).toBeFalsy();
            const [ stateSlices, actionDispatchers ] = result.current;
            expect(actionDispatchers).toBeNull();

            expect(stateSlices).toBeInstanceOf(Array);
            const defaultStateSlices = _at(defaultState, stateSlicerArr);
            expect(stateSlices).toStrictEqual(defaultStateSlices);
          },
        );

      },
    );

  });

  describe('second returned value (action dispatchers)', () => {

    it("returns all action dispatchers when passed 'undefined''", () => {
      const { result } = renderHook(
        () => useReportState(false, undefined),
        { wrapper: HookWrapper },
      );
      expect(result.error).toBeFalsy();
      const [ state, actionDispatchers ] = result.current;
      expect(state).toBeNull();
      const allACNames = Object.keys(actionCreators);
      allACNames.sort();
      const returnedADNames = Object.keys(actionDispatchers);
      returnedADNames.sort();
      // the action dispatchers have an extra "dispatch" function so we just
      // check that the actioin creator names are a subset of the action
      // dispatcher names
      expect(returnedADNames).toEqual(expect.arrayContaining(allACNames));
    });

    describe.each([
      ['string', ALL_ACTION_CREATOR_PATH_STRINGS],
      ['array', ALL_ACTION_CREATOR_PATH_ARRAYS],
    ])('slicers passed as %s',
      (tp, slicers) => {

        /**
         * see the previous 'slicers passed as %s' for description
         * @type {Array<string[]> | Array<Array<string[]>>}
         */
        const RESOLVED_SLICERS =
          slicers.map(v => [ tp === 'string' ? v : [v] ]);

        it.each(RESOLVED_SLICERS)(
          'yields correct action dispatch slice when passed a single path %j',
          (acSlicer) => {

            const { result, rerender } = renderHook(
              () => useReportState(false, acSlicer),
              { wrapper: HookWrapper },
            );
            expect(result.error).toBeFalsy();
            const [ stateSlice1, actionDispatcher1 ] = result.current;
            expect(stateSlice1).toBeNull();

            expect(actionDispatcher1).not.toBeInstanceOf(Array);
            const acSlice = _at(actionCreators, acSlicer)[0];
            expect(typeof actionDispatcher1).toBe('function');
            expect(actionDispatcher1.name).toBe(acSlice.name);
            expect(actionDispatcher1.length).toBe(acSlice.length);

            rerender(false, [ acSlicer ]);
            expect(result.error).toBeFalsy();
            const [ stateSlice2, actionDispatcher2 ] = result.current;
            expect(stateSlice2).toBeNull();

            expect(actionDispatcher2.name).toBe(actionDispatcher1.name);
            expect(actionDispatcher2.length).toBe(actionDispatcher1.length);
          },
        );

        /** see the previous 'slicers passed as %s' for description */
        const RESOLVED_SLICER_SAMPLES =
          randomSamples(slicers, 10, 2).map(v => [ v ]);

        it.each(RESOLVED_SLICER_SAMPLES)(
          `yields correct action dispatch slices when passed multiple paths %j`,
          (acSlicerArr) => {

            const { result } = renderHook(
              () => useReportState(false, acSlicerArr),
              { wrapper: HookWrapper },
            );
            expect(result.error).toBeFalsy();
            const [ stateSlices, actionDispatchers ] = result.current;
            expect(stateSlices).toBeNull();

            expect(actionDispatchers).toBeInstanceOf(Array);

            const defaultACs = _at(actionCreators, acSlicerArr);
            for(let i = 0; i < actionDispatchers.length; ++i) {
              const ad = actionDispatchers[i];
              const defaultAC = defaultACs[i];
              expect(typeof ad).toBe('function');
              expect(typeof ad).toBe(typeof defaultAC);
              expect(ad.name).toBe(defaultAC.name);
              expect(ad.length).toBe(defaultAC.length);
            }
          },
        );

      },
    );

  });

  describe("action dispatchers' effects on state", () => {

    it.each(_shuffle(
      /**
       * @type {Array} ActionCreatorTestParams
       * @property {string} ActionCreatorTestParams[0] - actionCreatorName
       * @property {string} ActionCreatorTestParams[1] - stateSlice
       * @property {any[]} ActionCreatorTestParams[2] - actionCreatorParams
       * @property {any} ActionCreatorTestParams[3] - expectedStateVal
       */
      [
        [
          'mapUriHashQueryToState',
          actionTypes.URI_HASH_QUERY,
          [ '?a=1&b=true&c=%7B"x"%3A+null%7D' ],
          new Map([
            [ 'a', 1 ],
            [ 'b', true ],
            [ 'c', { x: null } ],
          ])
        ],
        [
          'mapUriQueryToState',
          actionTypes.URI_QUERY,
          [ '?a=1&b=true&c=%7B"x"%3A+null%7D' ],
          new Map([
            [ 'a', 1 ],
            [ 'b', true ],
            [ 'c', { x: null } ],
          ])
        ],
        [
          'saveUriHashQuery',
          actionTypes.URI_HASH_QUERY,
          [ new Map([
            [ 'a', 1 ],
            [ 'b', true ],
            [ 'c', { x: null } ],
          ]) ],
          new Map([
            [ 'a', 1 ],
            [ 'b', true ],
            [ 'c', { x: null } ],
          ])
        ],
        [
          'saveUriQuery',
          actionTypes.URI_QUERY,
          [ new Map([
            [ 'a', 1 ],
            [ 'b', true ],
            [ 'c', { x: null } ],
          ]) ],
          new Map([
            [ 'a', 1 ],
            [ 'b', true ],
            [ 'c', { x: null } ],
          ])
        ],
        [
          'setAppBatchReportDoAutoSelect',
          actionTypes.APP_BATCHREPORT_DO_AUTO_SELECT,
          [ false ],
          false
        ],
        [
          'setAppBatchReportFetchError',
          actionTypes.APP_BATCHREPORT_FETCH_ERROR,
          [ new Error('some message') ],
          new Error('some message')
        ],
        [
          'setAppBatchReportFilter',
          actionTypes.APP_BATCHREPORT_FILTER,
          [ 'all' ],
          'all'
        ],
        [
          'setAppBatchReportIsDisplayEmpty',
          actionTypes.APP_BATCHREPORT_DISPLAY_EMPTY,
          [ true ],
          true
        ],
        [
          'setAppBatchReportIsFetching',
          actionTypes.APP_BATCHREPORT_FETCHING,
          [ null ],
          null
        ],
        [
          'setAppBatchReportIsLoading',
          actionTypes.APP_BATCHREPORT_LOADING,
          [ false ],
          false
        ],
        [
          'setAppBatchReportIsShowTags',
          actionTypes.APP_BATCHREPORT_SHOW_TAGS,
          [ true ],
          true
        ],
        [
          'setAppBatchReportJsonReport',
          actionTypes.APP_BATCHREPORT_JSON_REPORT,
          [ { type: 'testplan', uid: 'aaa-bbb-ccc-...' } ],
          { type: 'testplan', uid: 'aaa-bbb-ccc-...' }
        ],
        [
          'setAppBatchReportSelectedTestCase',
          actionTypes.APP_BATCHREPORT_SELECTED_TEST_CASE,
          [ { type: 'testcase', uid: 'aaa-bbb-ccc-...' } ],
          { type: 'testcase', uid: 'aaa-bbb-ccc-...' }
        ],
        [
          'setAppBatchReportShowHelpModal',
          actionTypes.APP_BATCHREPORT_SHOW_HELP_MODAL,
          [ false ],
          false
        ],
        [
          'setAppBatchReportShowInfoModal',
          actionTypes.APP_BATCHREPORT_SHOW_INFO_MODAL,
          [ true ],
          true
        ],
        [
          'setIsTesting',
          actionTypes.IS_TESTING,
          [ false ],
          false
        ],
        [
          'setUriHashPathComponentAlias',
          actionTypes.URI_HASH_ALIASES,
          [ uriComponentCodec.encode('Pre / Post Test'), 'Pre / Post Test' ],
          new Map([
            [ uriComponentCodec.encode('Pre / Post Test'), 'Pre / Post Test' ]
          ])
        ],
      ]
    ))(
      "tests that action creator '%s' changes the state at object path '%s'",
      (actionCreatorName, stateSlicer, actionCreatorParams, expectedState) => {

        const { result } = renderHook(
          () => useReportState(stateSlicer, actionCreatorName),
          { wrapper: HookWrapper },
        );
        expect(result.error).toBeFalsy();

        const defaultStateSlice = _at(defaultState, stateSlicer)[0];
        const [ stateSliceInit, actionDispatch ] = result.current;
        expect(stateSliceInit).toStrictEqual(defaultStateSlice);

        act(() => {
          actionDispatch(...actionCreatorParams);
        });
        const [ stateSliceAfter ] = result.current;
        expect(result.error).toBeFalsy();
        expect(stateSliceAfter).toStrictEqual(expectedState);
      },
    );

  });

});
