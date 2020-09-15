import React from 'react';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { coy } from "react-syntax-highlighter/dist/cjs/styles/prism/coy";

function CodeComponent(props) {
  return (
    <SyntaxHighlighter language={props.language} style={coy}>
      {props.value}
    </SyntaxHighlighter>
  );
}

export default function MarkdownAssertion(props) {
  return (
    <ReactMarkdown
      source={props.assertion.message}
      escapeHtml={props.assertion.escape}
      renderers={{
        code: CodeComponent
      }}
    />
  );
};


MarkdownAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
