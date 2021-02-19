/* eslint-disable max-len */
import { createSelector } from '@reduxjs/toolkit';
import { css } from 'aphrodite';
import _ from 'lodash';
import { mkGetReportDocument } from './reportSelectors';
import navStyles from '../../../Toolbar/navStyles';
import { STATUS_CATEGORY } from '../../../Common/defaults';
import { COLUMN_WIDTH } from '../../../Common/defaults';

const STATUS_CATEGORY_STYLE_MAP = {
  passed: navStyles.toolbarPassed,
  failed: navStyles.toolbarFailed,
  error: navStyles.toolbarFailed,
  unstable: navStyles.toolbarUnstable,
};

export const createUISelector = (...funcs) => _.spread(createSelector)([ state => state.ui, ...funcs ]);
export const mkGetUIIsShowHelpModal = () => createUISelector(({ isShowHelpModal }) => isShowHelpModal);
export const mkGetUIIsDisplayEmpty = () => createUISelector(({ isDisplayEmpty }) => isDisplayEmpty);
export const mkGetUIFilter = () => createUISelector(({ filter }) => filter);
export const mkGetUIIsShowTags = () => createUISelector(({ isShowTags }) => isShowTags);
export const mkGetUIIsShowInfoModal = () => createUISelector(({ isShowInfoModal }) => isShowInfoModal);
export const mkGetUISelectedEntry = () => createUISelector(({ selectedEntry }) => selectedEntry);

export const mkGetUIToolbarStyle = () => createSelector(
  mkGetReportDocument(),
  document => {
    let statusStyle = navStyles.toolbarUnknown;
    if(_.isObject(document) && document.status) {
      const statcat = STATUS_CATEGORY[document.status];
      if(statcat in STATUS_CATEGORY_STYLE_MAP) {
        statusStyle = STATUS_CATEGORY_STYLE_MAP[statcat];
      }
    }
    return css(navStyles.toolbar, statusStyle);
  },
);


export const mkGetUISidebarWidthFirstAvailable = () => createUISelector(
  uiState => (
    uiState.sidebarWidthPx || uiState.sidebarWidthEm || `${COLUMN_WIDTH}em`
  ),
);

export const getUISelectedEntry = mkGetUISelectedEntry();
export const getSideBarWidth = mkGetUISidebarWidthFirstAvailable();
