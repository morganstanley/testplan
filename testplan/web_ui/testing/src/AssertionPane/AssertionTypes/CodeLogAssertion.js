import React from "react";
import PropTypes from "prop-types";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { coy } from "react-syntax-highlighter/dist/cjs/styles/prism/coy";

export default function CodeLogAssertion(props) {
  return (
    <SyntaxHighlighter
      language={props.assertion.language}
      style={coy}
      showLineNumbers={true}
    >
      {props.assertion.code}
    </SyntaxHighlighter>
  );
}

CodeLogAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
