import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {Button} from 'reactstrap';
import copy from 'copy-html-to-clipboard';

class CopyToClipboard extends React.PureComponent {
  static propTypes = {
    text: PropTypes.any.isRequired,
    children: PropTypes.element.isRequired,
    onCopy: PropTypes.func,
    options: PropTypes.shape({
      debug: PropTypes.bool,
      message: PropTypes.string,
      asHtml: PropTypes.bool,
      onlyHtml: PropTypes.bool,
      canUsePrompt: PropTypes.bool,
    })
  };


  static defaultProps = {
    onCopy: undefined,
    options: undefined
  };


  onClick = event => {
    const {
      text,
      onCopy,
      children,
      options
    } = this.props;

    const elem = React.Children.only(children);

    let textToCopy;
    if (typeof text == 'function')
        textToCopy = text();
    else
        textToCopy = text;

    const result = copy(textToCopy, options);

    if (onCopy) {
      onCopy(textToCopy, result);
    }

    if (elem && elem.props) {
      if (typeof elem.props.onClick === 'function') {
        elem.props.onClick(event);
      } else if (typeof elem.props.onTouchTap === 'function') {
        elem.props.onTouchTap(event);
      }
    }
    
  };


  render() {
    const {
      text: _text,
      onCopy: _onCopy,
      options: _options,
      children,
      ...props
    } = this.props;
    const elem = React.Children.only(children);

    return React.cloneElement(
      elem, {...props, onClick: this.onClick, onTouchTap: this.onClick}
    );
  }
}

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
