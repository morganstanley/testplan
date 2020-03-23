import React from 'react';
import {StyleSheet, css} from 'aphrodite';

import {LIGHT_GREY, MIN_COLUMN_WIDTH} from "../Common/defaults";

/**
 * Vertical column for navigation bar.
 */

class Column extends React.Component {
  constructor(props) {
    super(props);
    this.mouseDown = this.mouseDown.bind(this);
    this.mouseMove = this.mouseMove.bind(this);
    this.mouseUp = this.mouseUp.bind(this);
  }

  mouseDown(e) {
    document.addEventListener('mousemove', this.mouseMove, false);
    document.addEventListener('mouseup', this.mouseUp, false);
  }

  mouseMove(e) {
    let event = e || window.event ;
    event.stopPropagation();
    if (event.clientX < MIN_COLUMN_WIDTH) {
      return;
    } else {
      this.props.handleColumnResizing(`${event.clientX}px`);
    }
  }

  mouseUp(e) {
    document.removeEventListener('mousemove', this.mouseMove);
	document.removeEventListener('mouseup', this.mouseUp);
  }

  render() {
    const columnStyles = StyleSheet.create({
      leftColumn: {
        width: this.props.width,
      },
      rightColumn: {
        left: this.props.width,
        width: '3px',
        backgroundColor: 'transparent',
        boxShadow: 'none',
        cursor: 'w-resize',
      },
    });

    return (
      <>
        <div className={css(styles.column, columnStyles.leftColumn)}>
          {this.props.children}
        </div>
        <div
          className={css(styles.column, columnStyles.rightColumn)}
          onMouseDown={this.mouseDown}
        >
          <div className={css(styles.column, styles.splitter)} />
        </div>
      </>
    );
  }
}

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
  splitter: {
    top: '0',
    left: '1px',
    width: '1px',
    cursor: 'w-resize',
    zIndex: 300,
  },
});

export default Column;
