import React from "react";
import PropTypes from "prop-types";
import _ from "lodash";
import base64url from "base64url";
import TreeView from "@material-ui/lab/TreeView";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import ChevronRightIcon from "@material-ui/icons/ChevronRight";
import TreeItem from "@material-ui/lab/TreeItem";
import { css, StyleSheet } from "aphrodite";
import Column from "./Column";
import NavEntry from "./NavEntry";
import InteractiveNavEntry from "./InteractiveNavEntry";
import { applyAllFilters } from "./navUtils";
import {
  STATUS,
  MEDIUM_GREY,
  RUNTIME_STATUS,
  NAV_ENTRY_ACTIONS,
} from "../Common/defaults";
import { CATEGORIES } from "../Common/defaults";
import { generatePath } from "react-router";
import { NavLink } from "react-router-dom";
import TagList from "./TagList";
import { makeStyles } from "@material-ui/core/styles";
import { generateURLWithParameters } from "../Common/utils";

const TreeViewNav = (props) => {
  const [expanded, setExpanded] = React.useState(null);

  React.useEffect(() => {
    // Allow multi expanded
    if (expanded !== null || _.isEmpty(props.selected)) {
      return;
    }
    let defaultExpanded = [];
    for (const uid of props.selected[props.selected.length - 1].uids) {
      if (_.isEmpty(defaultExpanded)) {
        defaultExpanded.push(uid);
      } else {
        defaultExpanded.push(
          `${defaultExpanded[defaultExpanded.length - 1]}/${uid}`
        );
      }
    }
    setExpanded(defaultExpanded);
  }, [props.selectedUid, props.selected, expanded]);

  const handleToggle = (event, nodeIds) => {
    setExpanded(nodeIds);
  };

  const handleDoubleClick = (nodeId) => {
    if (expanded.includes(nodeId)) {
      setExpanded(expanded.filter((id) => id !== nodeId));
    } else {
      setExpanded([...expanded, nodeId]);
    }
  };

  return (
    <>
      <Column
        width={props.width}
        handleColumnResizing={props.handleColumnResizing}
      >
        <TreeView
          selected={[
            _.isEmpty(props.selected)
              ? props.selectedUid
              : props.selected[props.selected.length - 1].uids.join("/"),
          ]}
          expanded={expanded}
          className={css(styles.treeView)}
          disableSelection={true}
          defaultCollapseIcon={<ExpandMoreIcon />}
          defaultExpandIcon={<ChevronRightIcon />}
          onNodeToggle={handleToggle}
        >
          {
            <Tree
              interactive={props.interactive}
              entries={props.entries}
              displayEmpty={props.displayEmpty}
              filter={props.filter}
              url={props.url}
              displayTags={props.displayTags}
              displayTime={props.displayTime}
              doubleClickCallback={handleDoubleClick}
              handleClick={props.handleClick}
              envCtrlCallback={props.envCtrlCallback}
            />
          }
        </TreeView>
      </Column>
    </>
  );
};

TreeViewNav.propTypes = {
  /** Nav list entries to be displayed */
  entries: PropTypes.arrayOf(
    PropTypes.shape({
      uid: PropTypes.string,
      name: PropTypes.string,
      description: PropTypes.string,
      status: PropTypes.oneOf(STATUS),
      runtime_status: PropTypes.oneOf(RUNTIME_STATUS),
      action: PropTypes.oneOf(NAV_ENTRY_ACTIONS),
      counter: PropTypes.shape({
        passed: PropTypes.number,
        failed: PropTypes.number,
      }),
    })
  ),
  /** Number of entries in the breadcrumb menu */
  breadcrumbLength: PropTypes.number,
  /** Function to handle Nav list resizing */
  handleColumnResizing: PropTypes.func,
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display empty testcase on navbar */
  displayEmpty: PropTypes.bool,
  /** Flag to display tags on navbar */
  displayTags: PropTypes.bool,
  /** Flag to display execution time on navbar */
  displayTime: PropTypes.bool,
  /** Entry uid to be focused */
  selectedUid: PropTypes.string,

  url: PropTypes.string,
};

export default TreeViewNav;

const Tree = (props) => {
  let entries = filterEntries(props.filter, props.entries, props.displayEmpty);
  return Array.isArray(entries)
    ? entries.map((entry) => (
        <Node
          interactive={props.interactive}
          key={entry.uids ? entry.uids.join("/") : entry.hash || entry.uid}
          displayEmpty
          displayTags={props.displayTags}
          displayTime={props.displayTime}
          entries={props.entries}
          filter={props.filter}
          url={props.url}
          entry={entry}
          doubleClickCallback={props.doubleClickCallback}
          handleClick={props.handleClick}
          envCtrlCallback={props.envCtrlCallback}
        />
      ))
    : null;
};

const filterEntries = (filter, entries, displayEmpty) => {
  let filteredEntries = applyAllFilters(filter, entries, displayEmpty);
  return filteredEntries.map((entry) =>
    filterEntriesOfEntry(entry, filter, displayEmpty)
  );
};

const filterEntriesOfEntry = (entry, filter, displayEmpty) => {
  if (Array.isArray(entry.entries)) {
    let tmp = { entries: filterEntries(filter, entry.entries, displayEmpty) };
    return { ...entry, ...tmp };
  }
  return entry;
};

const Node = (props) => {
  let [reportuid, ...selectionuids] = !props.interactive
    ? props.entry.uids
    : base64url
    ? props.entry.uids.map(base64url)
    : props.entry.uids;
  const linkTo = generateURLWithParameters(
    window.location,
    generatePath(props.url, {
      uid: reportuid,
      selection: selectionuids,
    })
  );
  const tags =
    props.displayTags && props.entry.tags ? (
      <TagList entryName={props.entry.name} tags={props.entry.tags} />
    ) : null;
  const treeViewClasses = getTreeViewStyles();
  const isTestcase = props.entry.category === CATEGORIES["testcase"];
  const nodeId = props.entry.uids
    ? props.entry.uids.join("/")
    : props.entry.uid;
  return (
    <TreeItem
      classes={{
        root: treeViewClasses.root,
        content: treeViewClasses.content,
        iconContainer: treeViewClasses.iconContainer,
        label: treeViewClasses.label,
      }}
      nodeId={nodeId}
      key={props.entry.hash || props.entry.uid}
      onLabelClick={(event) => {
        event.preventDefault();
      }}
      onDoubleClick={(event) => {
        event.stopPropagation();
        if (!isTestcase) {
          props.doubleClickCallback(nodeId);
        }
      }}
      label={
        <NavLink
          className={css(styles.leafNode)}
          key={props.entry.hash || props.entry.uid}
          to={linkTo}
          draggable={false}
        >
          {tags}
          {createNavEntry(props, props.entry)}
        </NavLink>
      }
    >
      {isTestcase ? null : continueTreeBranch(props, props.entry)}
    </TreeItem>
  );
};

const continueTreeBranch = (props, entry) => {
  return Array.isArray(entry.entries)
    ? entry.entries.map((entry) => (
        <Node
          interactive={props.interactive}
          key={entry.uids ? entry.uids.join("/") : entry.hash || entry.uid}
          displayEmpty
          displayTags={props.displayTags}
          displayTime={props.displayTime}
          entries={props.entries}
          filter={props.filter}
          url={props.url}
          entry={entry}
          doubleClickCallback={props.doubleClickCallback}
          handleClick={props.handleClick}
          envCtrlCallback={props.envCtrlCallback}
        />
      ))
    : null;
};

const createNavEntry = (props, entry) => {
  if (props.interactive) {
    return (
      <InteractiveNavEntry
        key={entry.hash || entry.uid}
        name={_.isEmpty(entry.part) ? entry.name : entry.uid}
        description={entry.description}
        status={entry.status}
        runtime_status={entry.runtime_status}
        envStatus={entry.env_status}
        type={entry.category}
        caseCountPassed={entry.counter.passed}
        caseCountFailed={entry.counter.failed + (entry.counter.error || 0)}
        handleClick={(e, action) => props.handleClick(e, entry, action)}
        envCtrlCallback={(e, action) => props.envCtrlCallback(e, entry, action)}
        suiteRelated={entry.suite_related}
        action={entry.action}
      />
    );
  } else {
    return (
      <NavEntry
        name={entry.name}
        description={entry.description}
        status={entry.status}
        type={entry.category}
        caseCountPassed={entry.counter.passed}
        caseCountFailed={entry.counter.failed + (entry.counter.error || 0)}
        executionTime={
          entry.timer && entry.timer.run
            ? new Date(entry.timer.run.end).getTime() -
              new Date(entry.timer.run.start).getTime()
            : null
        }
        displayTime={props.displayTime}
      />
    );
  }
};

const getTreeViewStyles = makeStyles({
  root: {
    "& > .MuiTreeItem-content": {
      paddingLeft: "5px",
      paddingRight: "5px",
    },
    "&.Mui-selected > .MuiTreeItem-content": {
      backgroundColor: MEDIUM_GREY,
    },
    "&.Mui-selected > .MuiTreeItem-content > .MuiTreeItem-label": {
      backgroundColor: MEDIUM_GREY,
    },
    "&.Mui-selected > .MuiTreeItem-content:hover > .MuiTreeItem-label": {
      backgroundColor: MEDIUM_GREY,
    },
    "&:focus > .MuiTreeItem-content .MuiTreeItem-label": {
      backgroundColor: "rgba(0,0,0,0)",
    },
    "&.Mui-selected > .MuiTreeItem-content .MuiTreeItem-label:hover, .MuiTreeItem-root.Mui-selected:focus > .MuiTreeItem-content .MuiTreeItem-label":
      {
        // eslint-disable-line max-len
        backgroundColor: MEDIUM_GREY,
      },
  },

  content: {
    "&:hover": {
      backgroundColor: MEDIUM_GREY,
    },
  },

  iconContainer: {
    cursor: "pointer",
  },

  label: {
    padding: "5px 0px",
    overflow: "hidden",
    "&:hover": {
      backgroundColor: MEDIUM_GREY,
    },
  },
});

const styles = StyleSheet.create({
  treeView: {
    overflowY: "auto",
    overflowX: "hidden",
    height: "100%",
    "::-webkit-scrollbar": {
      width: "6px",
    },
    "::-webkit-scrollbar-thumb": {
      backgroundColor: "rgba(0, 0, 0, 0.2)",
      borderRadius: "3px",
    },
    "::-webkit-scrollbar-thumb:hover": {
      backgroundColor: "rgba(0, 0, 0, 0.4)",
    },
  },

  leafNode: {
    textDecoration: "none",
    color: "#495057",
  },
});
