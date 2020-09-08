/* eslint-disable max-len */
import { createSelector } from '@reduxjs/toolkit';
import _ from 'lodash';

export const createReportSelector = (...funcs) => _.spread(createSelector)([ state => state.report, ...funcs ]);
export const mkGetLastResponseContentLength = () => createReportSelector(({ lastResponseContentLength }) => lastResponseContentLength);
export const mkGetReportUid = () => createReportSelector(({ uid }) => uid);
export const mkGetReportDocument = () => createReportSelector(({ document }) => document);
export const mkGetReportIsFetching = () => createReportSelector(({ isFetching }) => isFetching);
export const mkGetReportIsFetchCancelled = () => createReportSelector(({ isFetchCancelled }) => isFetchCancelled);
export const mkGetReportLastFetchError = () => createReportSelector(({ fetchError }) => fetchError);
export const getLastResponseContentLength = mkGetLastResponseContentLength();
export const getReportUid = mkGetReportUid();
export const getReportDocument = mkGetReportDocument();
export const getReportIsFetching = mkGetReportIsFetching();
export const getReportIsFetchCancelled = mkGetReportIsFetchCancelled();
export const getReportLastFetchError = mkGetReportLastFetchError();
