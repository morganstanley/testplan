/**
 * This file follows the rules of Jest's "setupFilesAfterEnv".
 * @see https://jestjs.io/docs/en/configuration#setupfilesafterenv-array
 */
import 'expect-puppeteer';
import '@testing-library/jest-dom/extend-expect';
import { configure } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

configure({ adapter: new Adapter() });
