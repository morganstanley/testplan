import React from 'react';
import { NavItem } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faBook } from '@fortawesome/free-solid-svg-icons';
import { TOOLBAR_BUTTON_CLASSES, BUTTONS_BAR_CLASSES } from '../styles';

library.add(faBook);

export default function DocumentationButton() {
  return (
    <NavItem className={BUTTONS_BAR_CLASSES}>
      <a href='http://testplan.readthedocs.io/'
         rel='noopener noreferrer'
         target='_blank'
      >
        <FontAwesomeIcon key='toolbar-document'
                         className={TOOLBAR_BUTTON_CLASSES}
                         icon={faBook.iconName}
                         title='Documentation'
        />
      </a>
    </NavItem>
  );
}
