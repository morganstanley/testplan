import React from 'react';
import _cloneDeep from 'lodash/cloneDeep';
import { getChangedBitsCalculator, makeMaskMap } from '../utils';
import defaultState from './defaultState';

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
