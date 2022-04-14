/**
 * Common aphrodite styles.
 */
import {StyleSheet} from 'aphrodite';
import {
  RED,
  GREEN,
  ORANGE,
  BLACK,
} from "../Common/defaults";

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
  },
  failed: {
    color: RED,
  },
  error: {
    color: RED,
  },
  skipped: {
    color: ORANGE,
  },
  unstable: {
    color: ORANGE,
  },
  unknown: {
    color: BLACK,
  },
};

export default StyleSheet.create({
  unselectable: unselectable
});
