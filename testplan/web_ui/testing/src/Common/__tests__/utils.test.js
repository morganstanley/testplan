import React from "react";

import { NAV_ENTRY_DISPLAY_DATA } from "../defaults";
import {
  formatSeconds,
  formatMilliseconds,
  getNavEntryDisplayData,
} from "../utils";

describe("Common/utils", () => {
  describe("getNavEntryDisplayData", () => {
    it("returns an empty object when given an empty object.", () => {
      const displayData = getNavEntryDisplayData({});

      for (const attribute of NAV_ENTRY_DISPLAY_DATA) {
        expect(displayData.hasOwnProperty(attribute)).toBeFalsy();
      }
    });

    it("returns an object with the expected keys when given an object with them.", () => {
      let index = 0;
      let entry = {};
      for (const attribute of NAV_ENTRY_DISPLAY_DATA) {
        entry[attribute] = index;
        index++;
      }
      entry["unknown"] = index;

      const displayData = getNavEntryDisplayData(entry);
      for (const attribute of NAV_ENTRY_DISPLAY_DATA) {
        expect(displayData[attribute]).toEqual(entry[attribute]);
      }
    });
  });

  describe("formatMilliseconds and formatSeconds", () => {
    it("returns s.SSS if the input is just less than a second", () => {
      const ms = 999;
      var millisecondsFormatted = formatMilliseconds(ms);
      var secondsFormatted = formatSeconds(ms / 1000);
      expect(millisecondsFormatted).toEqual("0.999s");
      expect(secondsFormatted).toEqual("0.999s");
    });

    it("returns s.SSS if the input is whole seconds and zero milliseconds", () => {
      const ms = 0;
      const s = 59000;
      const millisecondsInput = s + ms;
      var millisecondsFormatted = formatMilliseconds(millisecondsInput);
      var secondsFormatted = formatSeconds(millisecondsInput / 1000);
      expect(millisecondsFormatted).toEqual("59.000s");
      expect(secondsFormatted).toEqual("59.000s");
    });

    it("returns s.SSS if the input is just less than a minute", () => {
      const ms = 999;
      const s = 59000;
      const millisecondsInput = s + ms;
      var millisecondsFormatted = formatMilliseconds(millisecondsInput);
      var secondsFormatted = formatSeconds(millisecondsInput / 1000);
      expect(millisecondsFormatted).toEqual("59.999s");
      expect(secondsFormatted).toEqual("59.999s");
    });

    it("returns m s.SSS if the input is less than an hour", () => {
      const ms = 999;
      const s = 59000;
      const m = 3540000;
      const millisecondsInput = m + s + ms;
      var millisecondsFormatted = formatMilliseconds(millisecondsInput);
      var secondsFormatted = formatSeconds(millisecondsInput / 1000);
      expect(millisecondsFormatted).toEqual("59m 59.999s");
      expect(secondsFormatted).toEqual("59m 59.999s");
    });

    it("returns h m s.SSS if the input is at least an hour", () => {
      const ms = 999;
      const s = 59000;
      const m = 3540000;
      const h = 32400000;
      const millisecondsInput = h + m + s + ms;
      var millisecondsFormatted = formatMilliseconds(millisecondsInput);
      var secondsFormatted = formatSeconds(millisecondsInput / 1000);
      expect(millisecondsFormatted).toEqual("9h 59m 59.999s");
      expect(secondsFormatted).toEqual("9h 59m 59.999s");
    });

    it("returns h m s.SSS if the input is at least an hour and zero minutes", () => {
      const ms = 999;
      const s = 59000;
      const m = 0;
      const h = 212400000;
      const millisecondsInput = h + m + s + ms;
      var millisecondsFormatted = formatMilliseconds(millisecondsInput);
      var secondsFormatted = formatSeconds(millisecondsInput / 1000);
      expect(millisecondsFormatted).toEqual("59h 0m 59.999s");
      expect(secondsFormatted).toEqual("59h 0m 59.999s");
    });
  });
});
