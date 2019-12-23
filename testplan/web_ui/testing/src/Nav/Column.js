import React from 'react';
import {StyleSheet, css} from 'aphrodite';

import {LIGHT_GREY} from "../Common/defaults";

/**
 * Vertical column for navigation bar.
 */

const Column = (props) => {
  const leftStyle = {width: `${props.width}em`};
  const rightStyle = {left: `${props.width}em`};

  return (
    <>
      <div className={css(styles.column)} style={leftStyle}>
        {props.children}
      </div>
      <div className={css(styles.column)} style={rightStyle}/>
    </>
  );
};

const styles = StyleSheet.create({
  column: {
    height: '100%',
    border: 'none',
    position: 'absolute',
    backgroundColor: LIGHT_GREY,
    boxShadow: '0px 2px 5px 0px rgba(0, 0, 0, 0.26), ' +
      '0px 2px 10px 0px rgba(0, 0, 0, 0.16)',
    display: 'inline-block',
    top: '4.5em',
    'padding-bottom': '4.5em',
    zIndex: 200,
  },
});

export default Column;
