import actionCreators from './actionCreators';

/** @typedef {typeof actionCreators} ActionCreatorType */
/**
 * <p>
 * This function returns an object that maps URl query parameters with action
 * creators. The keys of the returned object should be URL query params and the
 * values should be values from {@link actionCreators}.
 * </p>
 * <p/>
 * This object is used like so:
 * <ol><li>
 *   A query param (key) is manually set in the URL =>
 *   the mapped action creator (value) is dispatched
 * </li><li>
 *   One of the mapped action creators (values) is dispatched =>
 *   the associated query param (key) is set in the URL
 * </li></ol>
 * <p>
 * <b>IMPORTANT1</b>: This must be maintained as a 1-1 mapping, i.e. it should
 *                    be a valid js object of the same length if the values were
 *                    swapped with the keys.
 * </p>
 * <p>
 * <b>IMPORTANT2</b>: The action creators must take a single argument and return
 *                    a single action (not an array of actions).
 * </p>
 * <p>
 * This must be a function to prevent circular import errors with
 * './actionCreators'.
 * </p>
 * @example
 * // This object means `http://.../#/a/b/c?displayEmpty=true` will call
 * // `actionCreators.setAppBatchReportIsDisplayEmpty(true)`:
 * { displayEmpty: actionCreators.setAppBatchReportIsDisplayEmpty }
 *
 * @returns {Object.<string, ActionCreatorType[keyof ActionCreatorType]>}
 */
export const hashQueryActionCreatorMap = () => ({
  displayEmpty: actionCreators.setAppBatchReportIsDisplayEmpty,
  filter: actionCreators.setAppBatchReportFilter,
  showTags: actionCreators.setAppBatchReportIsShowTags,
  doAutoSelect: actionCreators.setAppBatchReportDoAutoSelect,
  isTesting: actionCreators.setIsTesting,
});

/**
 * This function has the same purpose as {@link hashQueryActionCreatorMap}
 * except it denotes actions to execute for non-hash query params.
 * @example
 * // This object means `http://.../?displayEmpty=false#/a/b/c` will call
 * // `actionCreators.setAppBatchReportIsDisplayEmpty(false)`:
 * { displayEmpty: actionCreators.setAppBatchReportIsDisplayEmpty }
 *
 * @see hashQueryActionCreatorMap
 * @returns {Object.<string, ActionCreatorType[keyof ActionCreatorType]>}
 */
export const queryActionCreatorMap = () => ({

});
