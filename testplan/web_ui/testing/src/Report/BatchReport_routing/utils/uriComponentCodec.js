import _escapeRegExp from 'lodash/escapeRegExp';

/**
 * The keys here are characters that have special meaning in a URL,
 * and unfortunately React Router can't be relied upon to consistently
 * serialize (search "react router URL encode slashes in route"), and
 * doesn't provide a super-easy way to DIY the serialization.
 *
 * We use a `Map` since we need '%' to be serialized first, and `Map`
 * maintains order.
 */
const originalToPctEscapedMap = new Map(
  [
    '%', '?', '#', ':', '/', '@', ']', '[', '!', '$', '&', "'", '(', ')', '=',
    ';', '+', '*', ',',
  ].map(c => [c, `%${c.charCodeAt(0).toString(16)}`])
);

/**
 * _THIS IS A WORK-IN-PROGRESS AND IS NOT ENABLED / AVAILABLE AT THE MOMENT._
 *
 * So while we're DIY-ing part of the routes' URL encoding, we can make the
 * URL itself OPTIONALLY better resemble what the user sees on the page. This
 * is safe because (as-of March 2020) since there seem to be no restrictions
 * on characters in the fragment portion of the URL in Chrome. Since we're
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
  [ ']', '\uff3d' ],  // "］" => http://unicode.scarfboy.com/?s=U%2bff3d
  [ '[', '\uff3b' ],  // "[" => http://unicode.scarfboy.com/?s=U%2bff3b
  [ '!', '\uff01' ],  // "！" => http://unicode.scarfboy.com/?s=U%2bff01
  [ '$', '\uff04' ],  // "＄" => http://unicode.scarfboy.com/?s=U%2bff04
  [ '&', '\uff06' ],  // "＆" => http://unicode.scarfboy.com/?s=U%2bff06
  [ "'", '\u2019' ],  // "’" => http://unicode.scarfboy.com/?s=U%2b2019
  [ '(', '\uff08' ],  // "（" => http://unicode.scarfboy.com/?s=U%2bff08
  [ ')', '\uff09' ],  // "）" => http://unicode.scarfboy.com/?s=U%2bff09
  [ '=', '\ufe66' ],  // "﹦" => http://unicode.scarfboy.com/?s=U%2bfe66
  [ ';', '\uff1b' ],  // "；" => http://unicode.scarfboy.com/?s=ff1b
  [ '+', '\uff0b' ],  // "＋" => http://unicode.scarfboy.com/?s=U%2bff0b
  [ '*', '\uff0a' ],  // "＊" => http://unicode.scarfboy.com/?s=U%2bff0a
  [ ',', '\ufe50' ],  // "﹐" => http://unicode.scarfboy.com/?s=U%2bfe50
]);

/**
 * Invert a map
 * @template {any} T
 * @template {any} U
 * @param {Map<T, U>} origMap - The map to invert
 * @returns {Map<U, T>}
 */
const invertMap = origMap => new Map(
  Array.from(origMap).map(([newVal, newKey]) => [ newKey, newVal ])
);

const pctEscapedToOriginalMap = invertMap(originalToPctEscapedMap);
const lookalikeToOriginalMap = invertMap(originalToLookalikeMap);

const mkTranslator = (charmapDefault, charmapAlt) =>
  (uriComponent, useLookalikes = false) => (
    [ ...(useLookalikes ? charmapAlt : charmapDefault) ]
      .reduce(
        (prevStr, [oldChar, newChar]) =>
          prevStr.replace(RegExp(_escapeRegExp(oldChar), 'g'), newChar),
        uriComponent
      )
  );

export default {
  /**
   * @function uriComponentCodec.encode
   * @desc Apply custom URL encodings to a string.
   * @param {string} uriComponent -
   *     The string to encode
   * @ignore @param {boolean} [useLookalikes=false] -
   *     Replace characters with lookalike unicode characters
   * @return {string} - `uriComponent` with URL-unsafe characters replaced
   */
  encode: mkTranslator(originalToPctEscapedMap, originalToLookalikeMap),
  /**
   * @function uriComponentCodec.decode
   * @desc Unapply custom URL encodings to a string.
   * @param {string} uriComponent -
   *     The string to decode
   * @ignore @param {boolean} [useLookalikes=false] -
   *     Undo replacement of characters with lookalike unicode characters
   * @return {string} - `uriComponent` with URL-unsafe characters restored
   */
  decode: mkTranslator(pctEscapedToOriginalMap, lookalikeToOriginalMap),
};
