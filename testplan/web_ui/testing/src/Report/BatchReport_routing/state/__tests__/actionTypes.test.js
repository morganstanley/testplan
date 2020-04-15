import _at from 'lodash/at';
import * as actionTypes from '../actionTypes';
import defaultState from '../defaultState';
import { getPaths } from '../../../../__tests__/fixtures/testUtils';

describe('Action Types', () => {
  const ALL_STATE_PATH_STRINGS = getPaths(defaultState);
  it.each(Object.entries(actionTypes))(
    `checks that action type %s's value "%s" is a valid state object path`,
    (actionType, actionTypeVal) => {
      // @ts-ignore
      expect(ALL_STATE_PATH_STRINGS.indexOf(actionTypeVal)).not.toBe(-1);
      expect(_at(defaultState, actionTypeVal)[0]).not.toBeUndefined();
    },
  );
});
