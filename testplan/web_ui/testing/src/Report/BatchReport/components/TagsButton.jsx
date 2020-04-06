import React from 'react';
import NavItem from 'reactstrap/lib/NavItem';
import { css } from 'aphrodite';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faTags } from '@fortawesome/free-solid-svg-icons';

import useReportState from '../hooks/useReportState';
import { default as navStyles } from '../../../Toolbar/navStyles';

library.add(faTags);

/**
 * Return the button which toggles the display of tags.
 * @returns {React.FunctionComponentElement}
 */
export default function TagsButton() {
  const [ isShowTags, setShowTags ] = useReportState(
    'app.reports.batch.isShowTags', 'setAppBatchReportIsShowTags',
  );
  return (
    <NavItem>
      <div className={css(navStyles.buttonsBar)}>
        <span onClick={() => setShowTags(!isShowTags)}>
          <FontAwesomeIcon key='toolbar-tags'
                           icon={faTags.iconName}
                           title='Toggle tags'
                           className={css(navStyles.toolbarButton)}
          />
        </span>
      </div>
    </NavItem>
  );
}
