import {sortFlattenedJSON} from '../dictAssertionUtils';

describe('dictAssertionUtils', () => {
  it('sortFlattenedJSON used to sort the data of dict-like assertions', () => {
    let flattenedDict = [
      [0,"foo","Failed","",""],
      [1,"alpha","Failed","",""],
      [1,"","Passed",["int","1"],["int","1"]],
      [1,"","Passed",["int","2"],["int","2"]],
      [1,"","Failed",["int","3"],[null,null]],
      [1,"beta","Failed","",""],
      [2,"color","Failed",["str","red"],["str","blue"]]
    ];

    let expectedByChar = [
      [0,"foo","Failed","",""],
      [1,"alpha","Failed","",""],
      [1,"","Passed",["int","1"],["int","1"]],
      [1,"","Passed",["int","2"],["int","2"]],
      [1,"","Failed",["int","3"],[null,null]],
      [1,"beta","Failed","",""],
      [2,"color","Failed",["str","red"],["str","blue"]]
    ];

    let expectedByCharReverse = [
      [0,"foo","Failed","",""],
      [1,"beta","Failed","",""],
      [2,"color","Failed",["str","red"],["str","blue"]],
      [1,"alpha","Failed","",""],
      [1,"","Passed",["int","1"],["int","1"]],
      [1,"","Passed",["int","2"],["int","2"]],
      [1,"","Failed",["int","3"],[null,null]]
    ];

    let expectedByStatus = [
      [0,"foo","Failed","",""],
      [1,"alpha","Failed","",""],
      [1,"","Failed",["int","3"],[null,null]],
      [1,"","Passed",["int","1"],["int","1"]],
      [1,"","Passed",["int","2"],["int","2"]],
      [1,"beta","Failed","",""],
      [2,"color","Failed",["str","red"],["str","blue"]]
    ];

    expect(sortFlattenedJSON(flattenedDict, 0, false, false))
    .toEqual(expectedByChar);
    expect(sortFlattenedJSON(flattenedDict, 0, true, false))
    .toEqual(expectedByCharReverse);
    expect(sortFlattenedJSON(flattenedDict, 0, false, true))
    .toEqual(expectedByStatus);
  });
});