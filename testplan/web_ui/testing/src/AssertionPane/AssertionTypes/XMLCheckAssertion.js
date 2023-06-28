import React from "react";
import { css, StyleSheet } from "aphrodite";

const XMLCheckAssertion = ({ assertion }) => {
  const { xpath, xml } = assertion;

  return (
    <>
      <div>
        <strong className={css(styles.titl)}>Expected XPath:</strong>
        <span>{xpath}</span>
      </div>
      <pre className={css(styles.inputText)}>{xml.replace(/ {12}/g, "")}</pre>
    </>
  );
};
const styles = StyleSheet.create({
  inputText: {
    paddingTop: "1em",
    marginBottom: "0",
  },
  title: {
    paddingRight: "0.5em",
  },
});

export default XMLCheckAssertion;
