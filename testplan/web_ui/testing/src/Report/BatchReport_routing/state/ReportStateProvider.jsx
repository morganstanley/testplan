import React from 'react';

import ReportStateContext from './ReportStateContext';
import ReportActionsContext from './ReportActionsContext';
import * as uriQueryActions from './uriQueryActions';
import actionCreators from './actionCreators';
import { uiHistory } from '../components/UIRouter';
import { mapToQueryString } from '../utils';

/**
 * This function adds hooks to {@link actionCreators} such that whenever one is
 * the 'to' value in {@link uriQueryActions.hashQueryActionCreatorMap} is used then the
 * corresponding 'from' value is set in the URL.
 */
function addQueryParamHooksToActionCreators() {
  const actionCreatorQueryParamMap = new Map(
    Object.entries(uriQueryActions.hashQueryActionCreatorMap).map(
      ([queryParam, func]) => [func, queryParam]
    )
  );
  return Object.fromEntries(
    Object.entries(actionCreators).map(([name, func]) => {
      // `Map.get` essentially uses `Object.is` to match keys, see
      // http://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Map#Key_equality
      const queryParam = actionCreatorQueryParamMap.get(func);
      if(!queryParam) return [name, func];
      return [name, (val) => {
        // @ts-ignore
        const unhookedAction = func(val);
        const origCallback = unhookedAction.callback;
        return {
          ...unhookedAction,
          callback: draftState => {
            if(typeof origCallback === 'function') origCallback(draftState);
            draftState.uri.hash.query.set(queryParam, val);
            uiHistory.push({
              ...uiHistory.location,
              search: mapToQueryString(draftState.uri.hash.query)
            });
          }
        };
      }];
    })
  );
}

/**
 * <p>
 * This binds our action creators to the passed dispatch function so our actions
 * are automatically dispatched when calling one of the returned functions.
 * </p>
 * <p>
 * This function also adds hooks for the action creators mapped in
 * {@link uriQueryActions.hashQueryActionCreatorMap} so that when one of the mapped action
 * creators is called then the associated query param is automatically appended
 * to the window's URL, i.e. it implements item (2) from that object's jsdoc.
 * </p>
 * @callback {React.Dispatch<ReturnType<AppActionCreatorsObj>>} dispatchFunc
 * @returns {Record<
 *   keyof AppActionCreatorsObj,
 *   function(Parameters<AppActionCreators>): void
 * > & React.Dispatch<ReturnType<AppActionCreators>>}
 */
const bindDispatchToActions = dispatchFunc => {
  // the raw dispatch func is also made available on the returned object
  const hookedActionCreators = addQueryParamHooksToActionCreators();
  const boundActionCreators = { dispatch: dispatchFunc };
  for(const [ name, func ] of Object.entries(hookedActionCreators)) {
    const wrappedFunc = (...args) => {
      const actions = func(...args);
      const actionsArr = Array.isArray(actions) ? actions : [ actions ];
      for(const action of actionsArr) {
        dispatchFunc(action);
      }
    };
    Object.defineProperty(wrappedFunc, "length", { value: func.length });
    Object.defineProperty(wrappedFunc, "name", { value: func.name });
    boundActionCreators[name] = wrappedFunc;
  }
  return boundActionCreators;
};

/**
 * Makes children eligible for using the `useReportState` hook
 * @type {React.FunctionComponent<React.PropsWithChildren<any>>}
 */
export default function ReportStateProvider({ children, ...props }) {
  const stateContext = React.useContext(ReportStateContext);
  const actionsContext = React.useContext(ReportActionsContext);
  const [ state, dispatch ] = React.useReducer(actionsContext, stateContext);
  const boundActions = bindDispatchToActions(dispatch);
  return (
    // @ts-ignore
    <ReportActionsContext.Provider value={boundActions}>
      <ReportStateContext.Provider value={state}>
        {React.Children.map(children, C => React.cloneElement(C, props))}
      </ReportStateContext.Provider>
    </ReportActionsContext.Provider>
  );
}
