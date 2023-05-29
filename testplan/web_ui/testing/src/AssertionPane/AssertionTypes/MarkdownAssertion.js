import React from "react";
import PropTypes from "prop-types";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import rehypeRaw from "rehype-raw";
import SyntacHighlighterSettings from "./SyntaxHighlighterSettings";

function CodeComponent({ node, inline, className, children, ...props }) {
  const match = /language-(\w+)/.exec(className || "");
  const highlight = !inline && match;
  return highlight ? (
    <SyntaxHighlighter
      language={match[1]}
      {...SyntacHighlighterSettings}
      {...props}
    >
      {String(children).replace(/\n$/, "")}
    </SyntaxHighlighter>
  ) : (
    <code className={className} {...props}>
      {children}
    </code>
  );
}

export default function MarkdownAssertion(props) {
  const rehypePlugins = props.assertion.escape ? [] : [rehypeRaw];
  return (
    <ReactMarkdown
      children={props.assertion.message}
      rehypePlugins={rehypePlugins}
      components={{
        code: (props) => <CodeComponent {...props} />,
      }}
    />
  );
}

MarkdownAssertion.propTypes = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
