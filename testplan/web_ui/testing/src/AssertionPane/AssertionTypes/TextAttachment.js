import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {StyleSheet, css} from 'aphrodite';
import axios from 'axios';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { FadeLoader } from 'react-spinners';

//Max number of lines displayed in the preview window
const DISPLAY_NUM = 20
//Line requirement for a scroll bar to be rendered when expanded
const SCROLLBAR_MIN_LIMIT = 60

/**
* TextAttachment component:
*   * Gets text file using Axios
*   * Returns JSX depending on how long the text file is
*/

class TextAttachment extends Component {
  constructor(props) {
    super(props);
      this.state = {
      loading: false,
      error: null,
      textContent: "",
      originalText: null,
      numberOfLines: null,
      expandButtonPushed: false,
      scrollbar: null,
    };
  }

  /**
  * Fetch the text attachment once the component has mounted.
  * @public
  */
  componentDidMount() {
    this.setState({loading: true});
    this.getTextAttachment()
  }

  /*
  * Prepare the contents of the collapsed .txt content, by displaying the
  * last DISPLAY_NUM lines of the text file (or the entire text file if
  * it has less lines than DISPLAY_NUM - short files).
  *
  * @param {array} text_array (each element of array is one line of text)
  * @return {jsx} Content for the .txt file content when collapsed
  * @private
  */
  getCollapsedText(text_array){
    let last_lines;
    let i;
    let starting_line;
    let num_of_lines = text_array.length;

    if(num_of_lines < DISPLAY_NUM){
      i = 0;
      starting_line = 1;
      last_lines = "";
    } else {
      i = num_of_lines - DISPLAY_NUM;
      starting_line = num_of_lines - DISPLAY_NUM;
      last_lines = "...\n";
    }

    for(i; i < num_of_lines; i++){
      last_lines = last_lines + text_array[i] + '\n';
    }

    let return_jsx = (
      <SyntaxHighlighter showLineNumbers
          startingLineNumber={starting_line}>
        {last_lines}
      </SyntaxHighlighter>
    )
    return return_jsx
  }

  /*
  * Convert a string into an array where each element is one line of the text
  * and explicitly declare a <newline> at end of the text
  *
  * @param {string} text
  * @return {Array} line-by-line version of text
  * @private
  */
  displayTextToArray(text){
    let lines = text.split('\n');
    let length = lines.length;

    if(lines.pop() === ""){
      lines[length-1] = "<newline>"
    }
    return lines
  }

  /*
  * Sets the state based on text content received to be displayed.
  *
  * @param {string} text
  * @private
  */
  handleText(text){
    let lines =  this.displayTextToArray(text);
    let display = this.getCollapsedText(lines);

    if(lines[lines.length-1] === "<newline>"){
     text += "<newline>"
    }

    this.setState({
      textContent: display,
      numberOfLines: lines.length,
      originalText: text,
      loading: false
     });
  }

  /**
  * Fetch the text attachment.
  *   * Handle UID errors.
  *   * Make a GET request for the .txt attachment file.
  *   * Prepare the display content
  * @public
  */
  getTextAttachment() {
    const paths = window.location.pathname.split('/');

    // Check if dev mode and display test_string
    if ((paths.length >= 2) && (paths[1] === '_dev')) {
      const TEST_TEXT = "test1\ntest2\ntest3\ntest4\ntest5\ntest6\ntest7\n";
      let text = TEST_TEXT;
      this.handleText(text)

    //If not in dev mode
    } else if (paths.length >= 3) {
      axios.get(this.props.src)
      .then(response => {
          let text = response.data
          this.handleText(text)
      })
      .catch(error => this.setState({
                        error: true,
                        loading: false
                      })
        );

    //If some other error with URL
    } else {
      this.setState({
        error: true,
        loading: false
      });
    }
  }

  /*
  * Change the displayed .txt content, when the Expand/Collapse button gets
  * pressed - will only render a scroll bar if there are more
  * than SCROLLBAR_MIN_LIMIT lines in file.
  *
  * (This method is bound to onClick for the Expand/Collapse button)
  */
  updateTextContent = () => {
    let text = this.state.originalText;
    let scrollbar_content;
    let display;

    if(this.state.expandButtonPushed){
      let lines =  this.displayTextToArray(text);
      display = this.getCollapsedText(lines);
      scrollbar_content = null;
    } else {
      if(SCROLLBAR_MIN_LIMIT > this.state.numberOfLines){
        scrollbar_content = null;
      } else {
        scrollbar_content = css(styles.content);
      }

      display = (
        <SyntaxHighlighter showLineNumbers>
          {text}
        </SyntaxHighlighter>
      )
    }

  this.setState( state =>({
      textContent: display,
      expandButtonPushed: !state.expandButtonPushed,
      scrollbar: scrollbar_content
    }));
  }

  render() {
    let button_jsx;
    let content;

    let spinner = (
      <div className={css(styles.spinner)}>
        <FadeLoader
          color={'#123abc'}
          loading={true}
          height={10}
          width={3}
          radius={4}
        />
      </div>
    )

    //Show expand/collapse button only if less than DISPLAY_NUM lines
    if(this.state.numberOfLines < DISPLAY_NUM){
      button_jsx = null;
    } else {
      button_jsx = (
        <button onClick={this.updateTextContent}>
          {this.state.expandButtonPushed? 'Collapse': 'Expand'}
        </button>
       )
    }

    content = (
      <div>
        <div>
          <a href={this.props.src}>
            {this.props.file_name? this.props.file_name: "Test.txt"}
          </a>
        </div>
        <br/>
        <div className={this.state.scrollbar}>
          {this.state.textContent}
        </div>
        <br/>
        <div>
          {button_jsx}
       </div>
      </div>
    )

    return (
      <div>
        {this.state.error? "Error fetching attachment" : null}
        {this.state.loading? spinner: content}
      </div>
    );
  }
}

const styles = StyleSheet.create({
  spinner: {
  'margin-left': '100%',
  },
  content: {
  'overflow-y': 'scroll',
  'height': '55vh',
  }
});

TextAttachment.propTypes = {
  /** Assertion being rendered */
  src: PropTypes.string,
  file_name: PropTypes.string
};

export default TextAttachment;
