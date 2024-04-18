import "react-app-polyfill/stable";
import "jest-canvas-mock";
import { configure } from "enzyme";
import Adapter from "@wojtekmaj/enzyme-adapter-react-17";
import enableHooks from "jest-react-hooks-shallow";

configure({ adapter: new Adapter() });

// We use a hack to have hooks for shallow rendering, but only wherever we need
// https://github.com/mikeborozdin/jest-react-hooks-shallow#usage-with-mount
enableHooks(jest, { dontMockByDefault: true });

// Fix the issue: https://github.com/plotly/react-plotly.js/issues/115
if (typeof window !== "undefined") {
  window.URL.createObjectURL = function () {};
}
