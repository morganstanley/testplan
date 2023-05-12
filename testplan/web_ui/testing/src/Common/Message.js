import React, { Component } from "react";
import PropTypes from "prop-types";
import { StyleSheet, css } from "aphrodite";

import { MEDIUM_GREY } from "./defaults";

/**
 * Displayed a message in the center of the container.
 */
class Message extends Component {
  render() {
    const paneStyle = {
      paddingLeft: this.props.left,
      paddingTop: "4.5em",
    };
    const Tag = this.props.tag || "h1";
    return (
      <div style={paneStyle}>
        <Tag className={css(styles.message)}>{this.props.message}</Tag>
      </div>
    );
  }
}

Message.propTypes = {
  /** Message to be displayed */
  message: PropTypes.string,
  /** How far left the container should be placed */
  left: PropTypes.string,
};

const styles = StyleSheet.create({
  message: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    textAlign: "center",
    minHeight: "100vh",
    color: MEDIUM_GREY,
  },
});

export default Message;
