import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {StyleSheet, css} from 'aphrodite';

/**
 * Filter box, enter filter expressions to filter entries from the Nav
 * component.
 */
class FilterBox extends Component {
  render() {
    return (
      <div
        className={css(styles.searchBox)}
        style={{width: this.props.width}}>
        <input
          className={css(styles.searchBoxInput)}
          type="text"
          placeholder="&#xf002; Filter"
          onKeyUp={this.props.handleNavFilter}
      />
      </div>
    );
  }
}

FilterBox.propTypes = {
  /** Function to handle expressions entered into the Filter box */
  handleNavFilter: PropTypes.func,
};

const styles = StyleSheet.create({
  searchBox: {
    height: '100%',
  },
  searchBoxInput: {
    height: '100%',
    width: '100%',
    border: 'none',
    display: 'block',
    boxSizing: 'border-box',
    padding: '0.4em 0.8em 0.4em 0.8em',
    position: 'relative',
    fontFamily: 'FontAwesome, "Helvetica Neue", Helvetica, Arial, sans-serif',
    fontSize: "small",
  }
});

export default FilterBox;
