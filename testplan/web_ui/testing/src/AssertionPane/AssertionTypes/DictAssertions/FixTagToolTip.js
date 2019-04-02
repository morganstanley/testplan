import React, {Component} from 'react';
import ToolTip from 'react-portal-tooltip';
import PropTypes from 'prop-types';
import {css, StyleSheet} from 'aphrodite';
import {Card, CardHeader, CardBody} from 'reactstrap';

/**
 * Display a tooltip for FIX tags.
 */
class FixTagToolTip extends Component {
  constructor(props) {
    super(props);

    this.showTooltip = this.showTooltip.bind(this);
    this.hideTooltip = this.hideTooltip.bind(this);

    this.state = {
      isTooltipActive: false,
    };
  }

  /**
   * Activate the tooltip.
   */
  showTooltip() {
    this.setState({
      isTooltipActive: true,
    });
  }

  /**
   * Deactivate the tooltip.
   */
  hideTooltip() {
    this.setState({
      isTooltipActive: false,
    });
  }

  render() {
    // This must be moved to prepareDictRowData and every cell will have it's
    // FIX tag info as well.
    // const fixInformation = getFixInformation(
    //   fixTagInfo,
    //   this.props.cellValue,
    //   this.props.keyValue,
    //   this.props.colField
    // );
    const fixInformation = {};
    const cardHeader =
      fixInformation.name
        ? (
          <CardHeader className={css(styles.toolTipPadding)}>
            {fixInformation.name}
          </CardHeader>
        )
        : null;

    return (
      fixInformation.descr || fixInformation.value
        ? (
          <ToolTip
            active={this.state.isTooltipActive}
            position='right'
            arrow='center'
            parent={this.props.parent}
            tooltipTimeout={0}
            style={{
              style: {
                padding: 0,
                boxShadow: '5px 5px 3px rgba(0, 0, 0, .5)',
              },
              arrowStyle: {}
            }}
          >
            <Card className={css(styles.toolTipCard)}>
              {cardHeader}
              <CardBody className={css(styles.toolTipPadding)}>
                {fixInformation.descr || fixInformation.value}
              </CardBody>
            </Card>
          </ToolTip>
        )
        : null
    );
  }
}

FixTagToolTip.propTypes = {
  /** ID of the tooltips parent */
  parent: PropTypes.string,
  /** Cell data */
  data: PropTypes.object,
};

const styles = StyleSheet.create({
  toolTipCard: {
    maxWidth: '250px',
    fontSize: '13px',
  },

  toolTipPadding: {
    padding: '.375rem .5rem',
  },
});

export default FixTagToolTip;
