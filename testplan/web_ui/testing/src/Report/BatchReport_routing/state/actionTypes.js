/**
 * These double as slicers that can be passed to lodash.at to grab part of the
 * state. This is what's used behind the scenes in `useReportState`.
 * @example
 * lodash.at({ isTesting: true, ... }, IS_TESTING) === [ true ]
 * lodash.at({
 *   app: {
 *     reports: {
 *       batch: {
 *         fetchError: new Error("sample error")
 *       }
 *     }
 *   }
 * }, APP_BATCHREPORT_FETCH_ERROR)[0].message === "sample error"
 * lodash.at({
 *   uri: {
 *     query: '?a=1&b=2',
 *     hash: {
 *       query: '?c=3&d=4',
 *     }
 *   }
 * }, [ URI_HASH_QUERY, URI_QUERY ]) === [ '?c=3&d=4', '?a=1&b=2' ]
 */
export const IS_TESTING = 'isTesting';
export const URI_HASH_ALIASES = 'uri.hash.aliases';
export const URI_HASH_QUERY = 'uri.hash.query';
export const URI_QUERY = 'uri.query';
export const APP_BATCHREPORT_DO_AUTO_SELECT = 'app.reports.batch.doAutoSelect';
export const APP_BATCHREPORT_DISPLAY_EMPTY = 'app.reports.batch.isDisplayEmpty';
export const APP_BATCHREPORT_FILTER = 'app.reports.batch.filter';
export const APP_BATCHREPORT_FETCHING = 'app.reports.batch.isFetching';
export const APP_BATCHREPORT_LOADING = 'app.reports.batch.isLoading';
export const APP_BATCHREPORT_FETCH_ERROR = 'app.reports.batch.fetchError';
export const APP_BATCHREPORT_SHOW_TAGS = 'app.reports.batch.isShowTags';
export const APP_BATCHREPORT_JSON_REPORT = 'app.reports.batch.jsonReport';
export const APP_BATCHREPORT_SHOW_HELP_MODAL =
  'app.reports.batch.isShowHelpModal';
export const APP_BATCHREPORT_SHOW_INFO_MODAL =
  'app.reports.batch.isShowInfoModal';
export const APP_BATCHREPORT_SELECTED_TEST_CASE =
  'app.reports.batch.selectedTestCase';
