import React from 'react';
import axios from 'axios';
import _cloneDeep from 'lodash/cloneDeep';

import * as filterStates from '../utils/filterStates';
import { getChangedBitsCalculator, makeMaskMap } from '../utils';

const API_BASE_URL =
  ['testing', 'development'].includes(process.env.NODE_ENV || '') &&
  process.env.REACT_APP_API_BASE_URL !== undefined ?
    process.env.REACT_APP_API_BASE_URL
    : new URL('/api/v1', window.location.origin).toString();

const API_CORS_HEADERS =
  window.location.origin !== new URL(API_BASE_URL).origin ? {
    'Access-Control-Allow-Origin': new URL(API_BASE_URL).origin,
  } : {};

export const defaultState = {
  documentation: {
    url: {
      external: 'http://testplan.readthedocs.io',
      internal: 'http://testplan.readthedocs.io',
    },
  },
  /** "type {boolean} */
  isTesting: false,
  uri: {
    hash: {
      /** @type {Map<string, string>} */
      aliases: new Map(),
      /** @type {Map<string, any>} */
      query: new Map(),
    },
    /** @type {Map<string, any>} */
    query: new Map(),
  },
  api: {
    /** @type {string} */
    baseURL: API_BASE_URL,
    /** @type {Object.<string, string>} */
    headers: {
      ...axios.defaults.headers.common,
      Accept: 'application/json',
      ...API_CORS_HEADERS,
    }
  },
  app: {
    reports: {
      batch: {
        /** @type {boolean} */
        isShowHelpModal: false,
        /** @type {boolean} */
        isDisplayEmpty: true,
        /** @type {string} */
        centerPanelPlaceholderMessage: 'Please select an entry.',
        /** @type {FilterStates[keyof FilterStates]} */
        // @ts-ignore
        filter: filterStates.ALL,
        /** @type {boolean} */
        isFetching: false,
        /** @type {string} */
        isFetchingMessage: 'Fetching Testplan report...',
        /** @type {boolean} */
        isLoading: false,
        /** @type {string} */
        isLoadingMessage: 'Waiting to fetch Testplan report...',
        /** @type {null | Error} */
        fetchError: null,
        /** @type {string} */
        fetchErrorMessagePrelude: 'Error fetching Testplan report.',
        /** @type {boolean} */
        isShowTags: false,
        /** @type {null | Object.<string, any>} */
        jsonReport: null,
        /** @type {boolean} */
        isShowInfoModal: false,
        /** @type {null | Object.<string, ActuallyAny>} */
        selectedTestCase: null,
        /** @type {boolean} */
        doAutoSelect: true,
      },
      interactive: null,
    },
  },
};

const state = _cloneDeep(defaultState);
export const stateMaskMap = makeMaskMap(state);

export default Object.defineProperty(
  React.createContext(state, getChangedBitsCalculator(stateMaskMap)),
  'displayName',
  {
    value: 'ReportStateContext',
    writable: false,
  }
);
