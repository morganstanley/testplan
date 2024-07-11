import { atomWithStorage } from "jotai/utils";

export const useTreeViewPreference = atomWithStorage("useTreeView", true);
export const displayTimeInfoPreference = atomWithStorage(
  "displayTimeInfo",
  false
);
export const displayPathPreference = atomWithStorage("displayPath", false);
export const timeInfoUTCPreference = atomWithStorage("UTCTime", false);
export const hideEmptyTestcasesPreference = atomWithStorage(
  "hideEmptyTestcases",
  false
);
export const hideSkippedTestcasesPreference = atomWithStorage(
  "hideSkippedTestcases",
  false
);
export const showStatusIconsPreference = atomWithStorage(
  "showStatusIcons",
  true
);
