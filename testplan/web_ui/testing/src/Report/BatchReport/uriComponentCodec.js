/**
 * The keys here are characters that have special meaning in a URL,
 * and unfortunately React Router can't be relied upon to consistently
 * serialize (search "react router URL encode slashes in route"), and
 * doesn't provide a super-easy way to DIY the serialization.
 *
 * We use a map since we need '%' to be serialized first, and `Map`
 * maintains order.
 */
const originalToPctEscapedMap = new Map([
  [ '%', '%25' ],
  [ '?', '%3f' ],
  [ '#', '%23' ],
  [ ':', '%3a' ],
  [ '/', '%2f' ],
  [ '@', '%40' ],
  [ ']', '%5d' ],
  [ '[', '%5b' ],
  [ '!', '%21' ],
  [ '$', '%24' ],
  [ '&', '%26' ],
  [ "'", '%27' ],
  [ '(', '%28' ],
  [ ')', '%29' ],
  [ '=', '%3d' ],
  [ ';', '%3b' ],
  [ '+', '%2b' ],
  [ '*', '%2a' ],
  [ ',', '%2c' ],
]);

/**
 * _THIS IS A WORK-IN-PROGRESS AND IS NOT ENABLED / AVAILABLE AT THE MOMENT._
 *
 * So while we're DIY-ing part of the routes' URL encoding, we can make the
 * URL itself OPTIONALLY better resemble what the user sees on the page. This
 * is safe because (as-of March 2020) since there seem to be no restrictions
 * on characters in the fragment portion of the URL in Chrome and since we're
 * inside a HashRouter, we're always in the fragment portion (though it may
 * not be technically permitted, see https://superuser.com/a/425351 & the
 * linked RFC).
 */
const originalToLookalikeMap = new Map([
  [ '?', '\uff1f' ],  // "？" => http://unicode.scarfboy.com/?s=U%2bff1f
  [ '#', '\uff03' ],  // "＃" => http://unicode.scarfboy.com/?s=U%2bff03
  [ '%', '\ufe6a' ],  // "﹪" => http://unicode.scarfboy.com/?s=U%2bfe6a
  [ ':', '\ufe55' ],  // "﹕" => http://unicode.scarfboy.com/?s=U%2bfe55
  [ '/', '\u2215' ],  // "∕" => http://unicode.scarfboy.com/?s=U%2b2215
  [ '@', '\ufe6b' ],  // "﹫" => http://unicode.scarfboy.com/?s=U%2bfe6b
  // TODO: find lookalikes for the rest
  [ ']', '' ],  // "" =>
  [ '[', '' ],  // "[" =>
  [ '!', '' ],  // "" =>
  [ '$', '' ],  // "" =>
  [ '&', '' ],  // "" =>
  [ "'", '' ],  // "" =>
  [ '(', '' ],  // "" =>
  [ ')', '' ],  // "" =>
  [ '=', '' ],  // "" =>
  [ ';', '' ],  // "" =>
  [ '+', '' ],  // "" =>
  [ '*', '' ],  // "" =>
  [ ',', '' ],  // "" =>
]);

const invertMap = origMap => new Map([
  [ ...origMap ].map(([newVal, newKey]) => [ newKey, newVal ])
]);

const pctEscapedToOriginalMap = invertMap(originalToPctEscapedMap);
const lookalikeToOriginalMap = invertMap(originalToLookalikeMap);

const mkTranslator = (charmapDefault/*, charmapAlt*/) =>
  (uriComponent/*, useLookalikes = false*/) => (
    [ ...(/* useLookalikes ? charmapAlt : */ charmapDefault) ]
      .reduce(
        (prevStr, [oldChar, newChar]) =>
          prevStr.replace(RegExp(oldChar, 'g'), newChar),
        uriComponent
      )
  );

const uriComponentCodec = {
  /**
   * @function uriComponentCodec.encode
   * @desc Apply custom URL encodings to a string.
   * @param {string} uriComponent -
   *     The string to encode
   * @ignore @param {boolean} [useLookalikes=false] -
   *     Replace characters with lookalike unicode characters
   * @return {string} - `uriComponent` with URL-unsafe characters replaced
   */
  encode: mkTranslator(originalToPctEscapedMap/*,originalToLookalikeMap*/),
  /**
   * @function uriComponentCodec.decode
   * @desc Unapply custom URL encodings to a string.
   * @param {string} uriComponent -
   *     The string to decode
   * @ignore @param {boolean} [useLookalikes=false] -
   *     Undo replacement of characters with lookalike unicode characters
   * @return {string} - `uriComponent` with URL-unsafe characters restored
   */
  decode: mkTranslator(pctEscapedToOriginalMap/*,lookalikeToOriginalMap*/),
};

export default uriComponentCodec;
