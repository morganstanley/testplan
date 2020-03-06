/** @jest-environment jsdom */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

describe('REACT_APP_API_BASE_URL', () => {
  
  beforeAll(() => {
    window._origOrigin = window.origin;
    window.origin = 'http://fake-origin:8901';
  });
  
  afterAll(() => {
    window.origin =  window._origOrigin;
    delete window._origOrigin;
  });
  
  it('Is defined', () => {
    expect(typeof API_BASE_URL).toEqual('string');
  });
  
  it('Is the correct format', () => {
    let numErrs = 0;
    try {
      // first test if the variable is a full URI e.g. http://1.2.3.4:8080/api
      new URL(API_BASE_URL);
    } catch(err1) {
      numErrs++;
      // if it's not a full URI it could still be a path intended to be 
      // relative to the current origin e.g. just /api
      try {
        new URL(API_BASE_URL, window.location.origin);
      } catch(err2) { numErrs++; }
    }
    expect(numErrs).toBeLessThan(2);
  });
  
});
