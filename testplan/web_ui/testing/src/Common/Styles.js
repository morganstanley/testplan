/**
 * Common aphrodite styles.
 */
import { StyleSheet } from "aphrodite";
import {
  faBug,
  faCheck,
  faExclamationCircle,
  faQuestionCircle,
  faTimes,
  faAngleDoubleRight,
} from "@fortawesome/free-solid-svg-icons";

import {
  RED,
  GREEN,
  ORANGE,
  BLACK,
  LIGHT_GREY,
  MEDIUM_GREY
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
    icon: faCheck,
  },
  failed: {
    color: RED,
    icon: faTimes,
  },
  error: {
    color: RED,
    icon: faBug,
  },
  skipped: {
    color: ORANGE,
    icon: faAngleDoubleRight,
  },
  unstable: {
    color: ORANGE,
    icon: faExclamationCircle,
  },
  unknown: {
    color: BLACK,
    icon: faQuestionCircle,
  },
};

export const navStyles = StyleSheet.create({
  entryName: {
    display: "flex",
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
  navTime: {
    display: "flex",
    flexDirection: "column",
    alignItems: "end",
  },
  navButton: {
    position: "relative",
    display: "block",
    border: "none",
    backgroundColor: LIGHT_GREY,
    cursor: "pointer",
  },
  navButtonInteract: {
    ":hover": {
      backgroundColor: MEDIUM_GREY,
    },
  },
  navButtonInteractFocus: {
    backgroundColor: MEDIUM_GREY,
    outline: "none",
  },
  buttonList: {
    "overflow-y": "auto",
    height: "100%",
  },
  statusIcon: {
    display: "inline-flex",
    width: "1rem",
    justifyContent: "center",
    marginRight: "0.3rem",
    alignSelf: "center",
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
