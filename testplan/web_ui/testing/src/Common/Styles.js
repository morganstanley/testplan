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

export const navStyles = StyleSheet.create({
  entryName: {
    overflow: "hidden",
    "text-overflow": "ellipsis",
    "white-space": "nowrap",
    fontSize: "small",
    fontWeight: 500,
    marginLeft: "3px",
    flex: "auto",
    marginRight: "3px",
    userSelect: "text",
  },
  entryIcons: {
    display: "flex",
    flexShrink: 0,
    "align-items": "center",
    marginLeft: "auto",
  },
  entryIcon: {
    fontSize: "x-small",
    margin: "0em 0.5em 0em 0.5em",
  },
  entryButton: {
    textDecoration: "none",
    position: "relative",
    display: "inline-block",
    height: "2.4em",
    width: "2.4em",
    cursor: "pointer",
    color: "black",
    padding: "0.7em 0em 0.7em 0em",
    transition: "all 0.3s ease-out 0s",
  },
  inactiveEntryButton: {
    textDecoration: "none",
    position: "relative",
    display: "inline-block",
    height: "2.4em",
    width: "2.4em",
    cursor: "pointer",
    color: BLACK,
    padding: "0.7em 0em 0.7em 0em",
    transition: "all 0.3s ease-out 0s !important",
  },
  environmentToggle: {
    padding: "0.65em 0em 0.65em 0em",
  },
  busyEnvironmentToggle: {
    color: "orange",
  },
  badge: {
    opacity: 0.5,
  },
  passedBadge: {
    backgroundColor: GREEN,
  },
  failedBadge: {
    backgroundColor: RED,
  },
  errorBadge: {
    backgroundColor: RED,
  },
  unstableBadge: {
    backgroundColor: ORANGE,
  },
  unknownBadge: {
    backgroundColor: BLACK,
  },
  ...statusStyles,
});

export default StyleSheet.create({
  unselectable: unselectable,
});
