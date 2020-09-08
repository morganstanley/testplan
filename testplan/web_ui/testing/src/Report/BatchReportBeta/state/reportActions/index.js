import reportSlice from '../reportSlice';

export const {
  setLastResponseContentLength,
  setReportUID,
} = reportSlice.actions;

export { default as fetchReport } from './fetchReport';
