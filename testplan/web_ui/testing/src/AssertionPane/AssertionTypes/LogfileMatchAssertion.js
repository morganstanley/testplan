import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { css, StyleSheet } from "aphrodite";

const LogfileMatchEntry = ({ pattern, timeout, startPos, endPos, matched }) => {
  const info = matched
    ? `Match between ${startPos} and ${endPos} found in ${timeout} seconds.`
    : `No match from ${startPos} found in ${timeout} seconds, search ended at ${endPos}`;

  return (
    <>
      <div>
        <span className={css(styles.infoText)}>{info}</span>
      </div>
      <div>
        <strong className={css(styles.title)}>Regex:</strong>
        <SyntaxHighlighter
          language="regex"
          PreTag="span"
          customStyle={{ padding: 0 }}
        >
          {pattern}
        </SyntaxHighlighter>
      </div>
      {matched ? (
        <div>
          <strong className={css(styles.title)}>Log Line:</strong>
          <span className={css(styles.inputText)}>{matched}</span>
        </div>
      ) : null}
    </>
  );
};

export const LogfileMatchAssertion = ({ assertion }) => {
  const { results, failure } = assertion;

  let entries;
  if (failure) {
    entries = results.concat([failure]);
  } else {
    entries = results;
  }

  return entries.map((entry) => {
    const {
      pattern,
      timeout,
      start_pos: startPos,
      end_pos: endPos,
      matched,
    } = entry;
    return (
      <LogfileMatchEntry
        pattern={pattern}
        timeout={timeout}
        startPos={startPos}
        endPos={endPos}
        matched={matched}
      />
    );
  });
};

const styles = StyleSheet.create({
  infoText: {
    padding: 0,
    lineHeight: "1.1",
    fontWeight: "bold",
  },
  inputText: {
    paddingTop: "1em",
    marginBottom: "0",
  },
  title: {
    paddingRight: "0.5em",
  },
});
