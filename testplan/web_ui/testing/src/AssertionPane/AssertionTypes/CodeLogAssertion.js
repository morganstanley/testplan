import React from "react";
import PropTypes from "prop-types";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import SyntacHighlighterSettings from "./SyntaxHighlighterSettings";

export default function CodeLogAssertion(props) {
  return (
    <SyntaxHighlighter
      language={props.assertion.language}
      {...SyntacHighlighterSettings}
    >
      {props.assertion.code}
    </SyntaxHighlighter>
  );
}

CodeLogAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
