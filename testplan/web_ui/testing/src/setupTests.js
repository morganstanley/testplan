import "react-app-polyfill/stable";
import "jest-canvas-mock";
import { configure } from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import enableHooks from "jest-react-hooks-shallow";

configure({ adapter: new Adapter() });
enableHooks(jest);

// Fix the issue: https://github.com/plotly/react-plotly.js/issues/115
if (typeof window !== "undefined") {
  window.URL.createObjectURL = function () {};
}
