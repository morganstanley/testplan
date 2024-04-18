import React, { Component } from "react";
import PropTypes from "prop-types";
import { StyleSheet, css } from "aphrodite";

import { MEDIUM_GREY } from "./defaults";

/**
 * Displayed a message in the center of the container.
 */
class Message extends Component {
  render() {
    const Tag = this.props.tag || "h1";
    return <Tag className={css(styles.message)}>{this.props.message}</Tag>;
  }
}

Message.propTypes = {
  /** Message to be displayed */
  message: PropTypes.string,
  /** WHat the text need to wrapped to, default h1 */
  tag: PropTypes.string,
};

const styles = StyleSheet.create({
  message: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    textAlign: "center",
    flex: 1,
    color: MEDIUM_GREY,
  },
});

export default Message;
