import uriComponentCodec from '../uriComponentCodec';
import { reverseMap } from '../../../../__tests__/fixtures/testUtils';

const
  reserved2PctEncodedMap = new Map([
    [ 'Dow is down 70%', 'Dow is down 70%25' ],
    [ 'è stato bene?', 'è stato bene%3f' ],
    [ '#woke', '%23woke' ],
    [ 'buy:5', 'buy%3a5' ],
    [ 'In / Out', 'In %2f Out' ],
    [ '@realDonaldTrump', '%40realDonaldTrump' ],
    [ '>=]', '>%3d%5d' ],
    [ '<:-[', '<%3a-%5b' ],
    [ 'help!', 'help%21' ],
    [ '$20', '%2420' ],
    [ '&ref', '%26ref' ],
    [ "'ciao'", '%27ciao%27' ],
    [ '(secret)', '%28secret%29' ],
    [ '1=="1"', '1%3d%3d"1"' ],
    [ 'end;', 'end%3b' ],
    [ '+3', '%2b3' ],
    [ '*ptr', '%2aptr' ],
    [ 'first,second', 'first%2csecond' ],
  ]),
  pctEncoded2ReservedMap = reverseMap(reserved2PctEncodedMap),
  reserved2UnicodeEncodedMap = new Map([
    [ 'Dow is down 70%', 'Dow is down 70\ufe6a' ],
    [ 'è stato bene?', 'è stato bene\uff1f' ],
    [ '#woke', '\uff03woke' ],
    [ 'buy:5', 'buy\ufe555' ],
    [ 'In / Out', 'In \u2215 Out' ],
    [ '@realDonaldTrump', '\ufe6brealDonaldTrump' ],
    [ '>=]', '>\ufe66\uff3d' ],
    [ '<:-[', '<\ufe55-\uff3b' ],
    [ 'help!', 'help\uff01' ],
    [ '$20', '\uff0420' ],
    [ '&ref', '\uff06ref' ],
    [ "'ciao'", '\u2019ciao\u2019' ],
    [ '(secret)', '\uff08secret\uff09' ],
    [ '1=="1"', '1\ufe66\ufe66"1"' ],
    [ 'end;', 'end\uff1b' ],
    [ '+3', '\uff0b3' ],
    [ '*ptr', '\uff0aptr' ],
    [ 'first,second', 'first\ufe50second' ],
  ]),
  unicodeEncoded2ReservedMap = reverseMap(reserved2UnicodeEncodedMap);

describe('uriComponentCodec', () => {

  it('checks that the mock component map fixtures are reversible', () => {
    // ensure that the maps above are 1-1 reversible
    expect(reserved2PctEncodedMap.size)
      .toBe(pctEncoded2ReservedMap.size);
    expect(reserved2UnicodeEncodedMap.size)
      .toBe(unicodeEncoded2ReservedMap.size);
  });

  it.each(Array.from(reserved2PctEncodedMap))(
    '(%#) correctly encodes "%s" to "%s"',
    (raw, encoded) => {
        expect(uriComponentCodec.encode(raw)).toBe(encoded);
    },
  );

  it.each(Array.from(pctEncoded2ReservedMap))(
    '(%#) correctly decodes "%s" to "%s"',
    (encoded, raw) => {
      expect(uriComponentCodec.decode(encoded)).toBe(raw);
    },
  );

  it.each(Array.from(reserved2UnicodeEncodedMap))(
    '(%#) correctly encodes "%s" to "%s"',
    (raw, encoded) => {
      expect(uriComponentCodec.encode(raw, true)).toBe(encoded);
    },
  );

  it.each(Array.from(unicodeEncoded2ReservedMap))(
    '(%#) correctly decodes "%s" to "%s"',
    (encoded, raw) => {
      expect(uriComponentCodec.decode(encoded, true)).toBe(raw);
    },
  );

});
