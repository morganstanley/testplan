import React from "react";
import { globalExpandStatus } from "./utils";

export const defaultAssertionStatus = {
  globalExpand: {
    status: globalExpandStatus(),
    time: 0,
  },
  assertions: {},
  updateGlobalExpand: () => {},
  updateAssertionStatus: () => {},
};


export const AssertionContext = React.createContext(defaultAssertionStatus);