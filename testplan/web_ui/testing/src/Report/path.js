import { generatePath } from "react-router";

const generateSelectionPath = (path, [uid, ...selection]) => {
  return generatePath(path, { uid, selection });
};

export { generateSelectionPath };
