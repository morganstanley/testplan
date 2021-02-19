import 'react-app-polyfill/stable';
import { configure } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import enableHooks from 'jest-react-hooks-shallow';

configure({ adapter: new Adapter() });
enableHooks(jest);