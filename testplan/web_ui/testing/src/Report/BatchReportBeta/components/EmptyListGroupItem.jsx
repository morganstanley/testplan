import React from 'react';
import { ListGroupItem } from 'reactstrap';
import { css } from 'aphrodite';
import { navUtilsStyles } from '../styles';

const LGI_CLASSES = css(navUtilsStyles.navButton);

export default function EmptyListGroupItem() {
  return (
    <ListGroupItem className={LGI_CLASSES}>
      No entries to display...
    </ListGroupItem>
  );
}
