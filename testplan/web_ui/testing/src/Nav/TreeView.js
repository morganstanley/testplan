import React, { useContext, useEffect } from "react";
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
import {
  generateURLWithParameters,
  calcExecutionTime,
} from "../Common/utils";

const SelectionContext = React.createContext(null);

const selectionToExpandIds = (selection) => {
  if (selection.length < 2) {
    return [];
  }
  const uids = _.nth(selection, -2).uids;
  const expansion = _.map(uids, (value, i, c) =>
    _.join(c.slice(0, i + 1), "/")
  );
  return expansion;
};

const TreeViewNav = (props) => {
  const [expanded, setExpanded] = React.useState(null);
  const [lastSelection, setLastSelection] = React.useState([]);
  const [selectedElement, setSelectedElement] = React.useState(null);
  const [transitionFinished, setTransitionFinished] = React.useState(true);

  React.useEffect(() => {
    const newSelection = !_.isEqualWith(
      lastSelection,
      props.selected,
      (s1, s2) => {
        if (s1.uid && s2.uid) {
          return s1.uid === s2.uid;
        }
      }
    );

    if (newSelection) {
      const expansion = selectionToExpandIds(props.selected);
      const newExpanded = _.union(expanded, expansion);
      if (!expanded || newExpanded.length > expanded.length) {
        // some transition will start to reveal the new selection
        setTransitionFinished(false);
        setExpanded(newExpanded);
      }
      setLastSelection(props.selected);
    }
  }, [lastSelection, props.selected, expanded, selectedElement]);

  const transitionFinishedCallback = (isAppearing) => {
    setTransitionFinished(true);
  };

  React.useEffect(() => {
    if (selectedElement && transitionFinished) {
      selectedElement.scrollIntoView({ block: "nearest" });
    }
  }, [selectedElement, transitionFinished]);

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
        <SelectionContext.Provider
          value={{ setSelectedElement, transitionFinishedCallback }}
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
                displaySkipped={props.displaySkipped}
                filter={props.filter}
                url={props.url}
                displayTags={props.displayTags}
                displayTime={props.displayTime}
                doubleClickCallback={handleDoubleClick}
                handleClick={props.handleClick}
                envCtrlCallback={props.envCtrlCallback}
                selected={props.selected}
              />
            }
          </TreeView>
        </SelectionContext.Provider>
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
  /** Function to handle Nav list resizing */
  handleColumnResizing: PropTypes.func,
  /** Entity filter */
  filter: PropTypes.string,
  /** Flag to display empty testcase on navbar */
  displayEmpty: PropTypes.bool,
  /** Flag to display skipped testcase on navbar */
  displaySkipped: PropTypes.bool,
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
  let entries = filterEntries(
    props.filter,
    props.entries,
    props.displayEmpty,
    props.displaySkipped
  );
  return Array.isArray(entries)
    ? entries.map((entry) => (
        <Node
          interactive={props.interactive}
          key={entry.uids ? entry.uids.join("/") : entry.hash || entry.uid}
          displayTags={props.displayTags}
          displayTime={props.displayTime}
          entries={props.entries}
          filter={props.filter}
          url={props.url}
          entry={entry}
          doubleClickCallback={props.doubleClickCallback}
          handleClick={props.handleClick}
          envCtrlCallback={props.envCtrlCallback}
          selected={props.selected}
        />
      ))
    : null;
};

const filterEntries = (filter, entries, displayEmpty, displaySkipped) => {
  let filteredEntries = applyAllFilters(
    filter,
    entries,
    displayEmpty,
    displaySkipped
  );
  return filteredEntries.map((entry) =>
    filterEntriesOfEntry(entry, filter, displayEmpty, displaySkipped)
  );
};

const filterEntriesOfEntry = (entry, filter, displayEmpty, displaySkipped) => {
  if (Array.isArray(entry.entries)) {
    let tmp = {
      entries: filterEntries(
        filter,
        entry.entries,
        displayEmpty,
        displaySkipped
      ),
    };
    return { ...entry, ...tmp };
  }
  return entry;
};

const Node = (props) => {
  const ref = React.createRef();
  const { setSelectedElement, transitionFinishedCallback } =
    useContext(SelectionContext);

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

  const isSelected = props.selected.at(-1).uid === props.entry.uid;

  useEffect(() => {
    if (isSelected) {
      const element = ref.current.firstElementChild;
      setSelectedElement(element);
    }
  });

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
      ref={ref}
      TransitionProps={{
        onEntered: transitionFinishedCallback,
      }}
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
          displayTags={props.displayTags}
          displayTime={props.displayTime}
          entries={props.entries}
          filter={props.filter}
          url={props.url}
          entry={entry}
          doubleClickCallback={props.doubleClickCallback}
          handleClick={props.handleClick}
          envCtrlCallback={props.envCtrlCallback}
          selected={props.selected}
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
        executionTime={calcExecutionTime(entry)}
        displayTime={props.displayTime}
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
        executionTime={calcExecutionTime(entry)}
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
