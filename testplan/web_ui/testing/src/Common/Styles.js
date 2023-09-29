/**
 * Common aphrodite styles.
 */
import { StyleSheet } from "aphrodite";
import { RED, GREEN, ORANGE, BLACK } from "../Common/defaults";

export const unselectable = {
  "moz-user-select": "-moz-none",
  "khtml-user-select": "none",
  "webkit-user-select": "none",
  "ms-user-select": "none",
  "user-select": "none",
};

export const statusStyles = {
  passed: {
    color: GREEN,
    fontStyle: "normal",
  },
  failed: {
    color: RED,
    fontStyle: "normal",
  },
  error: {
    color: RED,
    fontStyle: "normal",
  },
  skipped: {
    color: ORANGE,
    fontStyle: "normal",
  },
  unstable: {
    color: ORANGE,
    fontStyle: "normal",
  },
  unknown: {
    color: BLACK,
    fontStyle: "normal",
  },
};

export default StyleSheet.create({
  unselectable: unselectable,
});
