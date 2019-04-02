import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {Scrollbars} from 'react-custom-scrollbars';
import {library} from '@fortawesome/fontawesome-svg-core';
import {
  faCaretSquareUp,
} from '@fortawesome/free-solid-svg-icons';


library.add(
  faCaretSquareUp
);

/**
 * A scrollable container that after rendering an initial amount of items will
 * only render the rest of them (in chunks) if they are required, or in this
 * case, when the user scrolls to the bottom of the container.
 */
class InfiniteScroll extends Component {
  constructor(props) {
    super(props);

    this.state = {
      hasMore: true,
      isLoading: false,
      items: [],
      currentIndex: 0,
      id: undefined,
    };

    this.scrollbars = React.createRef();
    this.loadItems = this.loadItems.bind(this);
    this.onScroll = this.onScroll.bind(this);
  }

  /**
   * Calculate if the container is scrolled to the bottom.
   *
   * @param {object} el - Container DOM element.
   * @returns {boolean}
   * @public
   */
  static isContainerScrolledToTheBottom(el) {
    return el.getScrollHeight() - el.getScrollTop() === el.getClientHeight();
  }

  /**
   * Handler function for the container's onScroll event. If the component is
   * not already loading new items and there are items that are not yet loaded,
   * it will check if the container is scrolled to the bottom and call
   * [loadItems]{@link InfiniteScroll#loadItems}.
   *
   */
  onScroll() {
    if (this.state.isLoading || !this.state.hasMore)
      return;

    if (InfiniteScroll.isContainerScrolledToTheBottom(this.scrollbars.current))
      this.loadItems(this.props.sliceSize);
  }

  /**
   * Load the first batch of items to be displayed.
   *
   * @public
   */
  UNSAFE_componentWillMount() {
    this.loadItems(this.props.initSliceSize);
  }

  /**
   * Load items from the props to state.
   *
   * @param sliceSize - number of items to be loaded
   * @public
   */
  loadItems(sliceSize = 30) {
    this.setState({ isLoading: true }, () => {
      let nextItems = this.props.items.slice(
        this.state.currentIndex, this.state.currentIndex + sliceSize);

      this.setState({
        hasMore: nextItems.length === sliceSize,
        isLoading: false,
        items: [...this.state.items, ...nextItems],
        currentIndex: this.state.items.length + nextItems.length,
      });
    });
  }

  render() {
    const {isLoading, items} = this.state;

    const children = React.Children.map(this.props.children, child => {
      return React.cloneElement(child, {
        entries: items,
      });
    });

    return (
      <Scrollbars autoHide onScroll={this.onScroll} ref={this.scrollbars}>
        <div style={{paddingRight: '2rem'}}>
          {children}
          {isLoading && <div>Loading...</div>}
        </div>
      </Scrollbars>
    );
  }
}

InfiniteScroll.propTypes = {
  /** Array of items to be rendered */
  items: PropTypes.arrayOf(PropTypes.object),
  /** State of the expand all/collapse all functionality */
  globalIsOpen: PropTypes.bool,
  /** Function to reset the expand all/collapse all state if an individual 
   * assertion's visibility is changed */
  resetGlobalIsOpen: PropTypes.func,
  /** Number of items to be rendered when the page is first loaded */
  initSliceSize: PropTypes.number,
  /** Number of extra items to be rendered each time the user scrolled to the 
   * bottom */
  sliceSize: PropTypes.number,
  /** Components will be rendered in InfiniteScroll */
  children: PropTypes.oneOfType([PropTypes.array, PropTypes.object]),
};

export default InfiniteScroll;
