import React, { createContext, useReducer, useContext } from 'react';
import produce from 'immer';

/// State
const defaultState = {
  app: {
    reports: {
      batch: {
        uri: {
          hash: {
            componentAliases: new Map(),
          },
        },
      },
    },
  },
};

// Action types
export const actionTypes = {
  APP_URI_HASH_COMPONENT_ALIAS: 'APP_URI_HASH_COMPONENT_ALIAS',
};

// Action subtypes
const changeTypes = { SET: 'SET', DELETE: 'DELETE', NONE: 'NONE' };

/// Reducer
/* eslint-disable default-case */
export const appReducer = produce(defaultState, (state, action) => {
  // default case not needed: immerjs.github.io/immer/docs/example-reducer
  switch(action.type) {
    case actionTypes.APP_URI_HASH_COMPONENT_ALIAS:
      switch(action.change) {
        case changeTypes.SET:
          state.app.reports.batch.uri.hash.componentAliases.set(
            action.payload.component,
            action.payload.alias
          );
          return;
        case changeTypes.DELETE:
          delete state.app.reports.batch.uri.hash.componentAliases.delete(
            action.payload.component
          );
          return;
      }
      return;
  }
});
/* eslint-enable default-case */

/// Action creators
export const actionCreators = {
  unboundSetUriHashComponentAlias: (component, alias) => ({
    type: actionTypes.APP_URI_HASH_COMPONENT_ALIAS,
    change: changeTypes.SET,
    payload: { component, alias }
  }),
  unboundDeleteUriHashComponentAlias: (component) => ({
    type: actionTypes.APP_URI_HASH_COMPONENT_ALIAS,
    change: changeTypes.DELETE,
    payload: { component }
  }),
};

/// Bound Action Creator
const bindDispatch = dispatchFunc => ({
  setUriHashComponentAlias: (component, alias) => dispatchFunc(
    actionCreators.unboundSetUriHashComponentAlias(component, alias)
  ),
  deleteUriHashComponentAlias: (component) => dispatchFunc(
    actionCreators.unboundDeleteUriHashComponentAlias(component)
  ),
});

/// Context
/**
 * This is returned from `useContext(AppContext)` when we're in a component
 * that's not a child of `AppContext.Provider`.
 * @see https://reactjs.org/docs/context.html#reactcreatecontext
 */
const NOT_CHILD_OF_APP_CONTEXT_PROVIDER = 'NOT_CHILD_OF_APP_CONTEXT_PROVIDER';
export const AppContext = createContext(NOT_CHILD_OF_APP_CONTEXT_PROVIDER);
/**
 * @see https://reactjs.org/docs/context.html#contextdisplayname
 *  This is displayed in error messages and React DevTools
 **/
AppContext.displayName =
  ' /* global state store ==> */' +
  ' AppContext' +
  ' /* ==> access from a child of `AppStateProvider` with `useAppState` */';

// Provider component
// TODO: Allow consumers to request only part of the context
//       by accepting an argument here and memoizing all
export function AppStateProvider({ children, ...props }) {
  const [ appState, unboundAppDispatch ] = useReducer(appReducer, defaultState);
  const appActions = bindDispatch(unboundAppDispatch);
  return (
    <AppContext.Provider value={[ appState, appActions ]}>
      {React.Children.map(children, Child => <Child {...props} />)}
    </AppContext.Provider>
  );
}

/// Hook
export function useAppState() {
  const context = useContext(AppContext);
  if(context === NOT_CHILD_OF_APP_CONTEXT_PROVIDER) {
    throw new Error('This component is not a child of `AppStateProvider`.');
  }
  return /* [ appState, appActions ] = */ context;
}
