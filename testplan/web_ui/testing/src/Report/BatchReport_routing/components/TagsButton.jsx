import React from 'react';
import NavItem from 'reactstrap/lib/NavItem';
import { css } from 'aphrodite';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faTags } from '@fortawesome/free-solid-svg-icons';

import useReportState from '../hooks/useReportState';
import navStyles from '../../../Toolbar/navStyles';

library.add(faTags);

/**
 * Return the button which toggles the display of tags.
 * @returns {React.FunctionComponentElement}
 */
export default function TagsButton() {
  const [ isShowTags, setShowTags ] = useReportState(
    'app.reports.batch.isShowTags',
    'setAppBatchReportIsShowTags',
  );
  const onClick = evt => {
    evt.stopPropagation();
    setShowTags(!isShowTags);
  };
  return (
    <NavItem>
      <div className={css(navStyles.buttonsBar)}>
        <span onClick={onClick}>
          <FontAwesomeIcon key='toolbar-tags'
                           className={css(navStyles.toolbarButton)}
                           icon={faTags.iconName}
                           title='Toggle tags'
          />
        </span>
      </div>
    </NavItem>
  );
}
