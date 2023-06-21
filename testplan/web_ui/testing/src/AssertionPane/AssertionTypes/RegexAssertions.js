import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { css, StyleSheet } from "aphrodite";
import { hashCode } from "../../Common/utils";

const RegexBasedAssertion = ({ pattern, children }) => {
  return (
    <>
      <div>
        <strong className={css(styles.title)}>Pattern:</strong>
        <SyntaxHighlighter
          language="regex"
          PreTag="span"
          customStyle={{ padding: 0 }}
        >
          {pattern}
        </SyntaxHighlighter>
      </div>
      {children}
    </>
  );
};

export const RegexAssertion = ({ assertion }) => {
  const { pattern, string: assertionString, match_indexes } = assertion;

  let reconstructedString = [];
  let prevIdx = 0;
  const uid = hashCode(JSON.stringify(assertion)).toString();

  match_indexes.forEach((index) => {
    reconstructedString.push(
      <span key={uid + index + "0"}>
        {assertionString.slice(prevIdx, index[0])}
      </span>
    );
    reconstructedString.push(
      <mark className={css(styles.mark)} key={uid + index + "1"}>
        {assertionString.slice(index[0], index[1])}
      </mark>
    );
    prevIdx = index[1];
  });

  reconstructedString.push(
    <span key={uid + prevIdx}>{assertionString.slice(prevIdx)}</span>
  );

  return (
    <RegexBasedAssertion pattern={pattern}>
      <pre className={css(styles.inputText)}>{reconstructedString}</pre>
    </RegexBasedAssertion>
  );
};

export const RegexMatchLineAssertion = ({ assertion }) => {
  const { pattern, string, match_indexes } = assertion;

  const assertionString = string.split("\n");
  const reconstructedString = match_indexes.map((index) => (
    <mark key={index} className={css(styles.mark)}>
      {assertionString[index[0]].slice(index[1], index[2]) + "\n"}
    </mark>
  ));

  return (
    <RegexBasedAssertion pattern={pattern}>
      <pre className={css(styles.inputText)}>{reconstructedString}</pre>
    </RegexBasedAssertion>
  );
};

const styles = StyleSheet.create({
  mark: {
    padding: 0,
    backgroundColor: "rgba(0, 123, 255, .5)",
    lineHeight: "1.1",
  },
  inputText: {
    paddingTop: "1em",
    marginBottom: "0",
  },
  title: {
    paddingRight: "0.5em",
  },
});
