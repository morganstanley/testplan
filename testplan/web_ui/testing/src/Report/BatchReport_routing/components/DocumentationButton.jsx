import React from 'react';
import NavItem from 'reactstrap/lib/NavItem';
import { css } from 'aphrodite';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faBook } from '@fortawesome/free-solid-svg-icons';

import useReportState from '../hooks/useReportState';
import navStyles from '../../../Toolbar/navStyles';

library.add(faBook);

/**
 * Return the button which links to the documentation.
 * @returns {React.FunctionComponentElement}
 */
export default function DocumentationButton() {
  const [ docURL ] = useReportState('documentation.url.external', false);
  return (
    <NavItem>
      <a href={docURL}
         rel='noopener noreferrer'
         target='_blank'
         className={css(navStyles.buttonsBar)}
      >
        <FontAwesomeIcon key='toolbar-document'
                         className={css(navStyles.toolbarButton)}
                         icon={faBook.iconName}
                         title='Documentation'
        />
      </a>
    </NavItem>
  );
}
