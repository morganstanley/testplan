import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {Button} from 'reactstrap';
import CopyToClipboard from 'react-copy-html-to-clipboard';

/**
 * Component that renders the buttons of copy html to clipboard.
 */
class CopyButton extends Component {
  render() {
    return (
      <CopyToClipboard
        text={this.props.value}
        options={{asHtml: true}}
      >
        <Button
          outline
          color='secondary'
          size='sm'
          active={false}
        >
          Copy
        </Button>
      </CopyToClipboard>
    );
  }
}

CopyButton.propTypes = {
  /** The content be copied to clipboard  */
  value: PropTypes.string,
};

export default CopyButton;
