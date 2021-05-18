import React, { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import Avatar from "@material-ui/core/Avatar";
import Button from "@material-ui/core/Button";
import Grow from "@material-ui/core/Grow";
import Paper from "@material-ui/core/Paper";
import Popper from "@material-ui/core/Popper";
import MenuItem from "@material-ui/core/MenuItem";
import MenuList from "@material-ui/core/MenuList";
import ClickAwayListener from "@material-ui/core/ClickAwayListener";
import { makeStyles } from "@material-ui/core/styles";
import { Link, useHistory } from "react-router-dom";
import { generatePath } from "react-router";
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHome } from "@fortawesome/free-solid-svg-icons";
import {
  LIGHT_GREY,
  MEDIUM_GREY,
  BLACK,
  STATUS,
  RUNTIME_STATUS,
  CATEGORY_ICONS,
} from "../Common/defaults";
import { statusStyles } from "../Common/Styles";

library.add(faHome);

const useStyles = makeStyles({
  navBreadcrumbs: {
    top: "2.5em",
    borderTop: "solid 1px rgba(0, 0, 0, 0.1)",
    borderBottom: "solid 1px rgba(0, 0, 0, 0.1)",
    zIndex: 300,
    position: "fixed",
    display: "block",
    height: "34px",
    width: "100%",
    backgroundColor: LIGHT_GREY,
  },
  breadcrumbContainer: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    height: "32px",
    width: "100%",
    display: "flex",
    overflow: "hidden",
  },
  homeIcon: {
    color: BLACK,
  },
  breadcrumbMenu: {
    height: "32px",
    fontSize: "small",
    paddingLeft: "30px",
    textDecoration: "none",
    textTransform: "none",
    borderRadius: 0,
    "&:before": {
      content: "' '",
      display: "block",
      width: 0,
      height: 0,
      borderTop: "20px solid transparent",
      borderBottom: "20px solid transparent",
      borderLeft: `12px solid ${LIGHT_GREY}`,
      position: "absolute",
      top: "50%",
      marginTop: "-20px",
      left: "100%",
      zIndex: 500,
    },
    "&:after": {
      content: "' '",
      display: "block",
      width: 0,
      height: 0,
      borderTop: "20px solid transparent",
      borderBottom: "20px solid transparent",
      borderLeft: `12px solid ${MEDIUM_GREY}`,
      position: "absolute",
      top: "50%",
      marginTop: "-20px",
      marginLeft: "1px",
      left: "100%",
      zIndex: 475,
    },
    "&:hover": {
      backgroundColor: MEDIUM_GREY,
      transition: "none",
    },
    "&:hover:before": {
      borderLeftColor: MEDIUM_GREY,
      transition: "none",
    },
  },
  breadcrumbMenuButton: {
    backgroundColor: LIGHT_GREY,
  },
  breadcrumbName: {
    display: "-webkit-box",
    maxWidth: "70vh",
    overflow: "hidden",
    textOverflow: "ellipsis",
    wordBreak: "break-all",
    "-webkit-line-clamp": 1,
    "-webkit-box-orient": "vertical",
  },
  link: {
    textDecoration: "none",
    "&:hover": {
      textDecoration: "none",
    },
    display: "inherit",
    width: "100%",
  },
  avatar: {
    height: "20px",
    width: "20px",
    lineHeight: "20px",
    fontSize: "10px",
    display: "inline-block",
    marginRight: "10px",
    textAlign: "center",
  },
  ...statusStyles,
});

/**
 * Render a horizontal menu of all the currently selected entries.
 */
const NavBreadcrumbs = (props) => {
  const classes = useStyles();
  const [nextOpenItem, setNextOpenItem] = useState(null);

  let breadcrumbMenus;
  if (props.entries.length > 0) {
    breadcrumbMenus = [
      <li key="breadcrumbMenuHome">
        <Link
          to={generatePath(props.url, {
            uid: props.uidEncoder
              ? props.uidEncoder(props.entries[0].uids[0])
              : props.entries[0].uids[0],
          })}
          className={classes.link}
        >
          <Button
            className={
              `${classes.breadcrumbMenu} ${classes.breadcrumbMenuButton}`
            }
            disableRipple={true}
            style={{ paddingLeft: "10px" }}
          >
            <FontAwesomeIcon
              key="breadcrumbMenuHomeIcon"
              icon="home"
              title="Home"
              className={classes.homeIcon}
            />
          </Button>
        </Link>
      </li>,
    ];
    props.entries.forEach((entry, index, selected) => {
      breadcrumbMenus.push(
        <li
          key={`breadcrumbMenu${entry.category}`}
          className={classes.breadcrumbList}
        >
          <BreadcrumbMenu
            current={entry}
            key={entry.hash || entry.uid}
            uidEncoder={props.uidEncoder}
            url={props.url}
            isOpen={nextOpenItem === entry.uid}
            handleNextOpenItem={setNextOpenItem}
            nextSelectedUid={
              selected.length > index + 1 ? selected[index + 1].uid : null
            }
          />
        </li>
      );
    });
  }

  return (
    <div className={classes.navBreadcrumbs}>
      <ul className={classes.breadcrumbContainer}>{breadcrumbMenus}</ul>
    </div>
  );
};

const MenuEntry = (props) => {
  const classes = useStyles();

  return (
    <>
      <Avatar className={classes.avatar}>
        {CATEGORY_ICONS[props.category]}
      </Avatar>
      <span className={`${classes[props.status]} ${classes.breadcrumbName}`}>
        {props.name}
      </span>
      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
      <span className={classes.passed}>{props.counter.passed}</span>
      <span className={classes.unknown}>/</span>
      <span className={classes.failed}>
        {props.counter.failed + (props.counter.error || 0)}
      </span>
    </>
  );
};

const BreadcrumbMenu = (props) => {
  const [open, setOpen] = React.useState(false);
  const prevOpen = useRef(open);
  const anchorRef = useRef(null);
  const classes = useStyles();
  const history = useHistory();

  const handleToggle = () => {
    setOpen((prevOpen) => !prevOpen);
  };

  const handleClose = (event) => {
    if (anchorRef.current && anchorRef.current.contains(event.target)) {
      return;
    }
    setOpen(false);
  };

  const handleOnClickMenu = (url) => {
    return () => {
      if (open) {
        history.push(url);
      }
      handleToggle();
    };
  };

  const handleOnClickItem = (url, uid) => {
    return () => {
      history.push(url);
      props.handleNextOpenItem(uid);
      handleToggle();
    };
  };

  useEffect(() => {
    if (prevOpen.current === true && open === false) {
      anchorRef.current.focus();
    }
    prevOpen.current = open;
  }, [open]);

  useEffect(() => {
    if (props.isOpen) {
      handleToggle();
    }
  }, [props.isOpen]);

  const menuId = `breadcrumbMenu${props.current.category}`;

  const menuButton = (
    <Button
      ref={anchorRef}
      aria-controls={open ? menuId : undefined}
      aria-haspopup="true"
      onClick={handleOnClickMenu(
        generatePath(props.url, {
          uid: props.uidEncoder
            ? props.uidEncoder(props.current.uids[0])
            : props.current.uids[0],
          selection: props.uidEncoder
            ? props.current.uids.slice(1).map(props.uidEncoder)
            : props.current.uids.slice(1),
        })
      )}
      disableRipple={true}
      className={`${classes.breadcrumbMenu} ${classes.breadcrumbMenuButton} ${
        classes[props.current.status]
      }`}
    >
      <MenuEntry {...props.current} />
    </Button>
  );

  let menuPopper = null;

  if (props.current.category !== "testcase" && props.current.entries) {
    menuPopper = (
      <Popper
        open={open}
        anchorEl={anchorRef.current}
        placement="bottom-start"
        role={undefined}
        transition
        disablePortal
      >
        {({ TransitionProps }) => (
          <Grow
            {...TransitionProps}
            style={{ transformOrigin: "center bottom" }}
          >
            <Paper style={{ maxHeight: "50vh", overflow: "auto" }}>
              <ClickAwayListener onClickAway={handleClose}>
                <MenuList
                  key={props.current.hash | props.current.uid}
                  autoFocusItem={open}
                  variant="selectedMenu"
                  id={menuId}
                >
                  {props.current.entries.map((option) => {
                    const toLink = generatePath(props.url, {
                      uid: props.uidEncoder
                        ? props.uidEncoder(option.uids[0])
                        : option.uids[0],
                      selection: props.uidEncoder
                        ? option.uids.slice(1).map(props.uidEncoder)
                        : option.uids.slice(1),
                    });
                    return (
                      <MenuItem
                        key={option.hash | option.uid}
                        className={classes.breadcrumbMenu}
                        onClick={handleOnClickItem(toLink, option.uid)}
                        selected={props.nextSelectedUid === option.uid}
                        style={
                          props.nextSelectedUid === option.uid
                            ? { backgroundColor: MEDIUM_GREY }
                            : null
                        }
                      >
                        <MenuEntry {...option} />
                      </MenuItem>
                    );
                  })}
                </MenuList>
              </ClickAwayListener>
            </Paper>
          </Grow>
        )}
      </Popper>
    );
  }

  return (
    <>
      {menuButton}
      {menuPopper}
    </>
  );
};

NavBreadcrumbs.propTypes = {
  /** Nav breadcrumb entries to be displayed */
  entries: PropTypes.arrayOf(
    PropTypes.shape({
      uid: PropTypes.string,
      name: PropTypes.string,
      description: PropTypes.string,
      status: PropTypes.oneOf(STATUS),
      runtime_status: PropTypes.oneOf(RUNTIME_STATUS),
      counter: PropTypes.shape({
        passed: PropTypes.number,
        failed: PropTypes.number,
      }),
    })
  ),
  report: PropTypes.object,
  /** Function to handle Nav entries being clicked (selected) */
  handleNavClick: PropTypes.func,
};

export default NavBreadcrumbs;
