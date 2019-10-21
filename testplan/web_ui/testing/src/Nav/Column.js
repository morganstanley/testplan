import React, {Component, Fragment} from 'react';
import PropTypes from 'prop-types';
import {StyleSheet, css} from 'aphrodite';

import {LIGHT_GREY, COLUMN_WIDTH} from "../Common/defaults";

/**
 * Vertical column with draggable right side.
 */
class Column extends Component {
  constructor(props) {
    super(props);
    this.state = {
      width: COLUMN_WIDTH,
    };
  }

  /**
   * Placeholder to handle column's right side being dragged to new width
   */
  handleDrag() {
    const width = COLUMN_WIDTH;
    if (this.props.setWidth !== null) {
      this.props.setWidth(width);
    }
    this.setState({width: width});
  }

  render() {
    const navStyle = {width: `${this.state.width}em`};
    const gripStyle = {left: `${this.state.width}em`};
    return (
      <Fragment>
        <div className={css(styles.column)} style={navStyle}>
          {this.props.children}
        </div>
        <div className={css(styles.grip)} style={gripStyle}/>
      </Fragment>
    );
  }
}

Column.propTypes = {
  /** Function to pass this column's width to a higher order component */
  setWidth: PropTypes.func,
  /** Contents of the column */
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node,
  ]),
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
    zIndex: 200,
  },
  grip: {
    cursor: 'col-resize',
    position: 'absolute',
    width: '0.3em',
    height: '100%',
    zIndex: '50000',
    backgroundColor: 'transparent',
  },
});

export default Column;
