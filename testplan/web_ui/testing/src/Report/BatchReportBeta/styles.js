import { StyleSheet, css } from 'aphrodite';
import navStyles from '../../Toolbar/navStyles';
import { styles as navUtilsStyles } from '../../Nav/navUtils';

export { default as CommonStyles } from '../../Common/Styles';
export { styles as navBreadcrumbStyles } from '../../Nav/NavBreadcrumbs';
export { navUtilsStyles };
export { COLUMN_WIDTH } from '../../Common/defaults';

export const navListStyles = StyleSheet.create({
  buttonList: {
    'overflow-y': 'auto',
    'height': '100%',
  }
});

export const batchReportStyles = StyleSheet.create({
  batchReport: {
    /** overflow will hide dropdown div */
    // overflow: 'hidden'
  }
});

export const BATCH_REPORT_CLASSES = css(batchReportStyles.batchReport);
export const TOOLBAR_CLASSES = css(navStyles.toolbar);
export const TOOLBAR_BUTTON_CLASSES = css(navStyles.toolbarButton);
export const BUTTONS_BAR_CLASSES = css(navStyles.buttonsBar);
export const FILTER_BOX_CLASSES = css(navStyles.filterBox);
export const FILTER_DROPDOWN_CLASSES = css(navStyles.filterDropdown);
export const FILTER_LABEL_CLASSES = css(navStyles.filterLabel);
export const DROPDOWN_ITEM_CLASSES = css(navStyles.dropdownItem);
export const ACTIVE_LINK_CLASSES = css(navUtilsStyles.navButtonInteractFocus);
export const UNDECORATED_LINK_STYLE = {
  textDecoration: 'none',
  color: 'currentColor',
};
