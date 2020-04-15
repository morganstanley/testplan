import { css } from 'aphrodite';
import navStyles from '../../../Toolbar/navStyles';
import { STATUS_CATEGORY } from '../../../Common/defaults';

/** @typedef {keyof STATUS_CATEGORY} StatusType */
/**
 * Get the current toolbar style based on the testplan status.
 * @param {StatusType} [status]
 * @returns {ReturnType<typeof css>}
 */
export default (status) => css(
  navStyles.toolbar,
  {
    passed: navStyles.toolbarPassed,
    failed: navStyles.toolbarFailed,
    error: navStyles.toolbarFailed,
    unstable: navStyles.toolbarUnstable,
  }[STATUS_CATEGORY[status]] || navStyles.toolbarUnknown,
);
