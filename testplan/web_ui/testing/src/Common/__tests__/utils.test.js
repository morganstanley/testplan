import React from 'react';

import {NAV_ENTRY_DISPLAY_DATA} from "../defaults";
import {getNavEntryDisplayData} from '../utils';

describe('Common/utils', () => {

  describe('getNavEntryDisplayData', () => {

    it('returns an empty object when given an empty object.', () => {
      const displayData = getNavEntryDisplayData({});

      for (const attribute of NAV_ENTRY_DISPLAY_DATA) {
        expect(displayData.hasOwnProperty(attribute)).toBeFalsy();
      }
    });

    it('returns an object with the expected keys when given an object with them.', () => {
      let index = 0;
      let entry = {};
      for (const attribute of NAV_ENTRY_DISPLAY_DATA) {
        entry[attribute] = index;
        index++;
      }
      entry['unknown'] = index;

      const displayData = getNavEntryDisplayData(entry);
      for (const attribute of NAV_ENTRY_DISPLAY_DATA) {
        expect(displayData[attribute]).toEqual(entry[attribute]);
      }
    })

  });

});
