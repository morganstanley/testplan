"""
This file is base on the difflib from python standard library (version: 2.7.9)
it provides diff (context/unified) functions with more options like GNU diff,
including: --ignore-space-change, --ignore-whitespace, --ignore-blank-lines
Due to the different algorithm, its output might be a slightly difference
compared with that of gnu diff or windiff, but it won't lead to confusing.

Module difflib -- helpers for computing deltas between objects.

Function get_close_matches(word, possibilities, n=3, cutoff=0.6):
    Use SequenceMatcher to return list of the best "good enough" matches.

Function context_diff(a, b):
    For two lists of strings, return a delta in context diff format.

Function diff(a, b):
    Return a delta: the difference between `a` and `b` (lists of strings).

Function unified_diff(a, b):
    For two lists of strings, return a delta in unified diff format.

Class SequenceMatcher:
    A flexible class for comparing pairs of sequences of any type.

Class Differ:
    For producing human-readable deltas from sequences of lines of text.
"""

import os
import re
import heapq
from collections import namedtuple as _namedtuple
from functools import reduce
from datetime import datetime


__all__ = [
    "Match",
    "SequenceMatcher",
    "get_close_matches",
    "Differ",
    "IS_CHARACTER_JUNK",
    "IS_LINE_JUNK",
    "diff",
    "context_diff",
    "unified_diff",
]

Match = _namedtuple("Match", "a b size")


def _calculate_ratio(matches, length):
    if length:
        return 2.0 * matches / length
    return 1.0


class SequenceMatcher:

    """
    SequenceMatcher is a flexible class for comparing pairs of sequences of
    any type, so long as the sequence elements are hashable.  The basic
    algorithm predates, and is a little fancier than, an algorithm
    published in the late 1980's by Ratcliff and Obershelp under the
    hyperbolic name "gestalt pattern matching".  The basic idea is to find
    the longest contiguous matching subsequence that contains no "junk"
    elements (R-O doesn't address junk).  The same idea is then applied
    recursively to the pieces of the sequences to the left and to the right
    of the matching subsequence.  This does not yield minimal edit
    sequences, but does tend to yield matches that "look right" to people.

    SequenceMatcher tries to compute a "human-friendly diff" between two
    sequences.  Unlike e.g. UNIX(tm) diff, the fundamental notion is the
    longest *contiguous* & junk-free matching subsequence.  That's what
    catches peoples' eyes.  The Windows(tm) windiff has another interesting
    notion, pairing up elements that appear uniquely in each sequence.
    That, and the method here, appear to yield more intuitive difference
    reports than does diff.  This method appears to be the least vulnerable
    to synching up on blocks of "junk lines", though (like blank lines in
    ordinary text files, or maybe "<P>" lines in HTML files).  That may be
    because this is the only method of the 3 that has a *concept* of
    "junk" <wink>.

    Example, comparing two strings, and considering blanks to be "junk":

    >>> s = SequenceMatcher(lambda x: x == " ",
    ...                     "private Thread currentThread;",
    ...                     "private volatile Thread currentThread;")
    >>>

    .ratio() returns a float in [0, 1], measuring the "similarity" of the
    sequences.  As a rule of thumb, a .ratio() value over 0.6 means the
    sequences are close matches:

    >>> print(round(s.ratio(), 3))
    0.866
    >>>

    If you're only interested in where the sequences match,
    .get_matching_blocks() is handy:

    >>> for block in s.get_matching_blocks():
    ...     print("a[%d] and b[%d] match for %d elements" % block)
    a[0] and b[0] match for 8 elements
    a[8] and b[17] match for 21 elements
    a[29] and b[38] match for 0 elements

    Note that the last tuple returned by .get_matching_blocks() is always a
    dummy, (len(a), len(b), 0), and this is the only case in which the last
    tuple element (number of elements matched) is 0.

    If you want to know how to change the first sequence into the second,
    use .get_opcodes():

    >>> for opcode in s.get_opcodes():
    ...     print("%6s a[%d:%d] b[%d:%d]" % opcode)
     equal a[0:8] b[0:8]
    insert a[8:8] b[8:17]
     equal a[8:29] b[17:38]

    See the Differ class for a fancy human-friendly file differencer, which
    uses SequenceMatcher both to compare sequences of lines, and to compare
    sequences of characters within similar (near-matching) lines.

    See also function get_close_matches() in this module, which shows how
    simple code building on SequenceMatcher can be used to do useful work.

    Timing:  Basic R-O is cubic time worst case and quadratic time expected
    case.  SequenceMatcher is quadratic time for the worst case and has
    expected-case behavior dependent in a complicated way on how many
    elements the sequences have in common; best case time is linear.

    Methods:

    __init__(isjunk=None, a='', b='')
        Construct a SequenceMatcher.

    set_seqs(a, b)
        Set the two sequences to be compared.

    set_seq1(a)
        Set the first sequence to be compared.

    set_seq2(b)
        Set the second sequence to be compared.

    find_longest_match(alo, ahi, blo, bhi)
        Find longest matching block in a[alo:ahi] and b[blo:bhi].

    get_matching_blocks()
        Return list of triples describing matching subsequences.

    get_opcodes()
        Return list of 5-tuples describing how to turn a into b.

    ratio()
        Return a measure of the sequences' similarity (float in [0,1]).

    quick_ratio()
        Return an upper bound on .ratio() relatively quickly.

    real_quick_ratio()
        Return an upper bound on ratio() very quickly.
    """

    def __init__(self, isjunk=None, a="", b="", autojunk=False):
        """Construct a SequenceMatcher.

        Optional arg isjunk is None (the default), or a one-argument
        function that takes a sequence element and returns true iff the
        element is junk.  None is equivalent to passing "lambda x: 0", i.e.
        no elements are considered to be junk.  For example, pass
            lambda x: x in " \\t"
        if you're comparing lines as sequences of characters, and don't
        want to synch up on blanks or hard tabs.

        Optional arg a is the first of two sequences to be compared.  By
        default, an empty string.  The elements of a must be hashable.  See
        also .set_seqs() and .set_seq1().

        Optional arg b is the second of two sequences to be compared.  By
        default, an empty string.  The elements of b must be hashable. See
        also .set_seqs() and .set_seq2().

        Optional arg autojunk should be set to False to disable the
        "automatic junk heuristic" that treats popular elements as junk
        (see module documentation for more information).
        """

        # Members:
        # a
        #      first sequence
        # b
        #      second sequence; differences are computed as "what do
        #      we need to do to 'a' to change it into 'b'?"
        # b2j
        #      for x in b, b2j[x] is a list of the indices (into b)
        #      at which x appears; junk elements do not appear
        # fullbcount
        #      for x in b, fullbcount[x] == the number of times x
        #      appears in b; only materialized if really needed (used
        #      only for computing quick_ratio())
        # matching_blocks
        #      a list of (i, j, k) triples, where a[i:i+k] == b[j:j+k];
        #      ascending & non-overlapping in i and in j; terminated by
        #      a dummy (len(a), len(b), 0) sentinel
        # opcodes
        #      a list of (tag, i1, i2, j1, j2) tuples, where tag is
        #      one of
        #          'replace'   a[i1:i2] should be replaced by b[j1:j2]
        #          'delete'    a[i1:i2] should be deleted
        #          'insert'    b[j1:j2] should be inserted
        #          'equal'     a[i1:i2] == b[j1:j2]
        # isjunk
        #      a user-supplied function taking a sequence element and
        #      returning true iff the element is "junk" -- this has
        #      subtle but helpful effects on the algorithm, which I'll
        #      get around to writing up someday <0.9 wink>.
        #      DON'T USE!  Only __chain_b uses this.  Use isbjunk.
        # isbjunk
        #      for x in b, isbjunk(x) == isjunk(x) but much faster;
        #      it's really the __contains__ method of a hidden dict.
        #      DOES NOT WORK for x in a!
        # isbpopular
        #      for x in b, isbpopular(x) is true iff b is reasonably long
        #      (at least 200 elements) and x accounts for more than 1 + 1% of
        #      its elements (when autojunk is enabled).
        #      DOES NOT WORK for x in a!

        self.isjunk = isjunk
        self.a = self.b = None
        self.autojunk = autojunk
        self.set_seqs(a, b)

    def set_seqs(self, a, b):
        """Set the two sequences to be compared.

        >>> s = SequenceMatcher()
        >>> s.set_seqs("abcd", "bcde")
        >>> s.ratio()
        0.75
        """

        self.set_seq1(a)
        self.set_seq2(b)

    def set_seq1(self, a):
        """Set the first sequence to be compared.

        The second sequence to be compared is not changed.

        >>> s = SequenceMatcher(None, "abcd", "bcde")
        >>> s.ratio()
        0.75
        >>> s.set_seq1("bcde")
        >>> s.ratio()
        1.0
        >>>

        SequenceMatcher computes and caches detailed information about the
        second sequence, so if you want to compare one sequence S against
        many sequences, use .set_seq2(S) once and call .set_seq1(x)
        repeatedly for each of the other sequences.

        See also set_seqs() and set_seq2().
        """

        if a is self.a:
            return
        self.a = a
        self.a_real_content = (
            self.a.real_content()
            if isinstance(self.a, FuzzyMatchingString)
            else None
        )
        self.matching_blocks = self.opcodes = self._ratio = None

        # cache the data for self.find_longest_match()
        ajunk = (
            {elt for elt in self.a if self.isjunk(elt)}
            if self.isjunk
            else set()
        )
        self.isajunk = ajunk.__contains__

    def set_seq2(self, b):
        """Set the second sequence to be compared.

        The first sequence to be compared is not changed.

        >>> s = SequenceMatcher(None, "abcd", "bcde")
        >>> s.ratio()
        0.75
        >>> s.set_seq2("abcd")
        >>> s.ratio()
        1.0
        >>>

        SequenceMatcher computes and caches detailed information about the
        second sequence, so if you want to compare one sequence S against
        many sequences, use .set_seq2(S) once and call .set_seq1(x)
        repeatedly for each of the other sequences.

        See also set_seqs() and set_seq1().
        """

        if b is self.b:
            return
        self.b = b
        self.b_real_content = (
            self.b.real_content()
            if isinstance(self.b, FuzzyMatchingString)
            else None
        )
        self.matching_blocks = self.opcodes = self._ratio = None
        self.fullbcount = None
        self.__chain_b()

    # For each element x in b, set b2j[x] to a list of the indices in
    # b where x appears; the indices are in increasing order; note that
    # the number of times x appears in b is len(b2j[x]) ...
    # when self.isjunk is defined, junk elements don't show up in this
    # map at all, which stops the central find_longest_match method
    # from starting any matching block at a junk element ...
    # also creates the fast isbjunk function ...
    # b2j also does not contain entries for "popular" elements, meaning
    # elements that account for more than 1 + 1% of the total elements, and
    # when the sequence is reasonably large (>= 200 elements); this can
    # be viewed as an adaptive notion of semi-junk, and yields an enormous
    # speedup when, e.g., comparing program files with hundreds of
    # instances of "return NULL;" ...
    # note that this is only called when b changes; so for cross-product
    # kinds of matches, it's best to call set_seq2 once, then set_seq1
    # repeatedly

    def __chain_b(self):
        # Because isjunk is a user-defined (not C) function, and we test
        # for junk a LOT, it's important to minimize the number of calls.
        # Before the tricks described here, __chain_b was by far the most
        # time-consuming routine in the whole module!  If anyone sees
        # Jim Roskind, thank him again for profile.py -- I never would
        # have guessed that.
        # The first trick is to build b2j ignoring the possibility
        # of junk.  I.e., we don't call isjunk at all yet.  Throwing
        # out the junk later is much cheaper than building b2j "right"
        # from the start.

        b = self.b
        self.b2j = b2j = {}

        for i, elt in enumerate(b):
            indices = b2j.setdefault(elt, [])
            indices.append(i)

        # Purge junk elements
        bjunk = set()
        isjunk = self.isjunk
        if isjunk:
            for elt in list(b2j.keys()):  # using list() since b2j is modified
                if isjunk(elt):
                    bjunk.add(elt)
                    del b2j[elt]

        # Purge popular elements that are not junk
        popular = set()
        n = len(b)
        if self.autojunk and n >= 200:
            ntest = n // 100 + 1
            for elt, idxs in list(b2j.items()):
                if len(idxs) > ntest:
                    popular.add(elt)
                    del b2j[elt]

        # Now for x in b, isjunk(x) == x in junk, but the latter is much faster.
        # Sicne the number of *unique* junk elements is probably small, the
        # memory burden of keeping this set alive is likely trivial compared to
        # the size of b2j.
        self.isbjunk = bjunk.__contains__
        self.isbpopular = popular.__contains__

    def find_longest_match(self, alo, ahi, blo, bhi):
        """Find longest matching block in a[alo:ahi] and b[blo:bhi].

        If isjunk is not defined:

        Return (i,j,k) such that a[i:i+k] is equal to b[j:j+k], where
            alo <= i <= i+k <= ahi
            blo <= j <= j+k <= bhi
        and for all (i',j',k') meeting those conditions,
            k >= k'
            j <= j'
            and if j == j', i <= i'

        In other words, of all maximal matching blocks, return one that
        starts earliest in b, and of all those maximal matching blocks that
        start earliest in b, return the one that starts earliest in a.

        >>> s = SequenceMatcher(None, " abcd", "abcd abcd")
        >>> s.find_longest_match(0, 5, 0, 9)
        Match(a=0, b=4, size=5)

        If isjunk is defined, first the longest matching block is
        determined as above, but with the additional restriction that no
        junk element appears in the block.  Then that block is extended as
        far as possible by matching (only) junk elements on both sides.  So
        the resulting block never matches on junk except as identical junk
        happens to be adjacent to an "interesting" match.

        Here's the same example as before, but considering blanks to be
        junk.  That prevents " abcd" from matching the " abcd" at the tail
        end of the second sequence directly.  Instead only the "abcd" can
        match, and matches the leftmost "abcd" in the second sequence:

        >>> s = SequenceMatcher(lambda x: x==" ", " abcd", "abcd abcd")
        >>> s.find_longest_match(0, 5, 0, 9)
        Match(a=1, b=0, size=4)

        If no blocks match, return (alo, blo, 0).

        >>> s = SequenceMatcher(None, "ab", "c")
        >>> s.find_longest_match(0, 2, 0, 1)
        Match(a=0, b=0, size=0)
        """

        # CAUTION:  stripping common prefix or suffix would be incorrect.
        # E.g.,
        #    ab
        #    acab
        # Longest matching block is "ab", but if common prefix is
        # stripped, it's "a" (tied with "b").  UNIX(tm) diff does so
        # strip, so ends up claiming that ab is changed to acab by
        # inserting "ca" in the middle.  That's minimal but unintuitive:
        # "it's obvious" that someone inserted "ac" at the front.
        # Windiff ends up at the same place as diff, but by pairing up
        # the unique 'b's and then matching the first two 'a's.

        a, b, b2j = self.a, self.b, self.b2j
        isajunk, isbjunk = self.isajunk, self.isbjunk
        besti, bestj, bestsize = alo, blo, 0
        # find longest junk-free match
        # during an iteration of the loop, j2len[j] = length of longest
        # junk-free match ending with a[i-1] and b[j]
        j2len = {}
        for i in range(alo, ahi):
            # look at all instances of a[i] in b; note that because
            # b2j has no junk keys, the loop is skipped if a[i] is junk
            j2lenget = j2len.get
            newj2len = {}
            indices = []
            # TODO: (need improve) time consuming in this loop. For immutable
            # string we could get indices from b2j directly, but we may compare
            # mutable objects here, i.e. instances of FuzzyMatchingString.
            for key, val in b2j.items():
                if a[i] == key:
                    indices = val
                    break
            for j in indices:
                # a[i] matches b[j]
                if j < blo:
                    continue
                if j >= bhi:
                    break
                k = newj2len[j] = j2lenget(j - 1, 0) + 1
                # with condition 'k == bestsize and j-k+1 < bestj', the longest
                # substring starts earliest in b will be selected with priority
                if k > bestsize or k == bestsize and j - k + 1 < bestj:
                    besti, bestj, bestsize = i - k + 1, j - k + 1, k
            j2len = newj2len

        # Extend the best by non-junk and junk elements repeatedly until
        # no element can be appended to the front or back of the best match.
        prev_bestsize = 0
        while prev_bestsize != bestsize:
            prev_bestsize = bestsize

            # Extend the best by non-junk elements on each end.  In particular,
            # "popular" non-junk elements aren't in b2j, which greatly speeds
            # the inner loop above, but also means "the best" match so far
            # doesn't contain any junk *or* popular non-junk elements.
            while (
                besti > alo
                and bestj > blo
                and not isajunk(a[besti - 1])
                and not isbjunk(b[bestj - 1])
                and a[besti - 1] == b[bestj - 1]
            ):
                besti, bestj, bestsize = besti - 1, bestj - 1, bestsize + 1
            while (
                besti + bestsize < ahi
                and bestj + bestsize < bhi
                and not isajunk(a[besti + bestsize])
                and not isbjunk(b[bestj + bestsize])
                and a[besti + bestsize] == b[bestj + bestsize]
            ):
                bestsize += 1

            # Now that we have a wholly interesting match (albeit possibly
            # empty!), we may as well suck up the matching junk on each
            # side of it too.  Can't think of a good reason not to, and it
            # saves post-processing the (possibly considerable) expense of
            # figuring out what to do with it.  In the case of an empty
            # interesting match, this is clearly the right thing to do,
            # because no other kind of match is possible in the regions.
            while (
                besti > alo
                and bestj > blo
                and isajunk(a[besti - 1])
                and isbjunk(b[bestj - 1])
                and a[besti - 1] == b[bestj - 1]
            ):
                besti, bestj, bestsize = besti - 1, bestj - 1, bestsize + 1
            while (
                besti + bestsize < ahi
                and bestj + bestsize < bhi
                and isajunk(a[besti + bestsize])
                and isbjunk(b[bestj + bestsize])
                and a[besti + bestsize] == b[bestj + bestsize]
            ):
                bestsize += 1

        return Match(besti, bestj, bestsize)

    def get_matching_blocks(self):
        """Return list of triples describing matching subsequences.

        Each triple is of the form (i, j, n), and means that
        a[i:i+n] == b[j:j+n].  The triples are monotonically increasing in
        i and in j.  New in Python 2.5, it's also guaranteed that if
        (i, j, n) and (i', j', n') are adjacent triples in the list, and
        the second is not the last triple in the list, then i+n != i' or
        j+n != j'.  IOW, adjacent triples never describe adjacent equal
        blocks.

        The last triple is a dummy, (len(a), len(b), 0), and is the only
        triple with n==0.

        >>> s = SequenceMatcher(None, "abxcd", "abcd")
        >>> s.get_matching_blocks()
        [Match(a=0, b=0, size=2),
         Match(a=3, b=2, size=2),
         Match(a=5, b=4, size=0)]
        """

        if self.matching_blocks is not None:
            return self.matching_blocks
        la, lb = len(self.a), len(self.b)

        # This is most naturally expressed as a recursive algorithm, but
        # at least one user bumped into extreme use cases that exceeded
        # the recursion limit on their box.  So, now we maintain a list
        # ('queue`) of blocks we still need to look at, and append partial
        # results to `matching_blocks` in a loop; the matches are sorted
        # at the end.
        queue = [(0, la, 0, lb)]
        matching_blocks = []
        while queue:
            alo, ahi, blo, bhi = queue.pop()
            i, j, k = x = self.find_longest_match(alo, ahi, blo, bhi)
            # a[alo:i] vs b[blo:j] unknown
            # a[i:i+k] same as b[j:j+k]
            # a[i+k:ahi] vs b[j+k:bhi] unknown
            if k:  # if k is 0, there was no matching block
                matching_blocks.append(x)
                if alo < i and blo < j:
                    queue.append((alo, i, blo, j))
                if i + k < ahi and j + k < bhi:
                    queue.append((i + k, ahi, j + k, bhi))
        matching_blocks.sort()

        # It's possible that we have adjacent equal blocks in the
        # matching_blocks list now.  Starting with 2.5, this code was added
        # to collapse them.
        i1 = j1 = k1 = 0
        non_adjacent = []
        for i2, j2, k2 in matching_blocks:
            # Is this block adjacent to i1, j1, k1?
            if i1 + k1 == i2 and j1 + k1 == j2:
                # Yes, so collapse them -- this just increases the length of
                # the first block by the length of the second, and the first
                # block so lengthened remains the block to compare against.
                k1 += k2
            else:
                # Not adjacent.  Remember the first block (k1==0 means it's
                # the dummy we started with), and make the second block the
                # new block to compare against.
                if k1:
                    non_adjacent.append((i1, j1, k1))
                i1, j1, k1 = i2, j2, k2
        if k1:
            non_adjacent.append((i1, j1, k1))

        non_adjacent.append((la, lb, 0))
        self.matching_blocks = map(Match._make, non_adjacent)
        return self.matching_blocks

    def get_opcodes(self):
        """Return list of 5-tuples describing how to turn a into b.

        Each tuple is of the form (tag, i1, i2, j1, j2).  The first tuple
        has i1 == j1 == 0, and remaining tuples have i1 == the i2 from the
        tuple preceding it, and likewise for j1 == the previous j2.

        The tags are strings, with these meanings:

        'replace':  a[i1:i2] should be replaced by b[j1:j2]
        'delete':   a[i1:i2] should be deleted.
                    Note that j1==j2 in this case.
        'insert':   b[j1:j2] should be inserted at a[i1:i1].
                    Note that i1==i2 in this case.
        'equal':    a[i1:i2] == b[j1:j2]

        >>> a = "qabxcd"
        >>> b = "abycdf"
        >>> s = SequenceMatcher(None, a, b)
        >>> for tag, i1, i2, j1, j2 in s.get_opcodes():
        ...    print("%7s a[%d:%d] (%s) b[%d:%d] (%s)" %
        ...          (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))
         delete a[0:1] (q) b[0:0] ()
          equal a[1:3] (ab) b[0:2] (ab)
        replace a[3:4] (x) b[2:3] (y)
          equal a[4:6] (cd) b[3:5] (cd)
         insert a[6:6] () b[5:6] (f)
        """

        if self.opcodes is not None:
            return self.opcodes

        i = j = 0
        self.opcodes = answer = []
        for ai, bj, size in self.get_matching_blocks():
            # invariant:  we've pumped out correct diffs to change
            # a[:i] into b[:j], and the next matching block is
            # a[ai:ai+size] == b[bj:bj+size].  So we need to pump
            # out a diff to change a[i:ai] into b[j:bj], pump out
            # the matching block, and move (i,j) beyond the match
            tag = ""
            if i < ai and j < bj:
                tag = "replace"
            elif i < ai:
                tag = "delete"
            elif j < bj:
                tag = "insert"
            if tag:
                answer.append((tag, i, ai, j, bj))
            i, j = ai + size, bj + size
            # the list of matching blocks is terminated by a
            # sentinel with size 0
            if size:
                answer.append(("equal", ai, i, bj, j))
        return answer

    def get_grouped_opcodes(self, n=3):
        """Isolate change clusters by eliminating ranges with no changes.

        Return a generator of groups with up to n lines of context.
        Each group is in the same format as returned by get_opcodes().

        >>> from pprint import pprint
        >>> a = map(str, range(1,40))
        >>> b = a[:]
        >>> b[8:8] = ['i']     # Make an insertion
        >>> b[20] += 'x'       # Make a replacement
        >>> b[23:28] = []      # Make a deletion
        >>> b[30] += 'y'       # Make another replacement
        >>> pprint(list(SequenceMatcher(None, a, b).get_grouped_opcodes()))
        [[('equal', 5, 8, 5, 8),
          ('insert', 8, 8, 8, 9),
          ('equal', 8, 11, 9, 12)],
         [('equal', 16, 19, 17, 20),
          ('replace', 19, 20, 20, 21),
          ('equal', 20, 22, 21, 23),
          ('delete', 22, 27, 23, 23),
          ('equal', 27, 30, 23, 26)],
         [('equal', 31, 34, 27, 30),
          ('replace', 34, 35, 30, 31),
          ('equal', 35, 38, 31, 34)]]
        """

        codes = self.get_opcodes()
        if not codes:
            codes = [("equal", 0, 1, 0, 1)]
        # Fixup leading and trailing groups if they show no changes.
        if codes[0][0] == "equal":
            tag, i1, i2, j1, j2 = codes[0]
            codes[0] = tag, max(i1, i2 - n), i2, max(j1, j2 - n), j2
        if codes[-1][0] == "equal":
            tag, i1, i2, j1, j2 = codes[-1]
            codes[-1] = tag, i1, min(i2, i1 + n), j1, min(j2, j1 + n)

        nn = n + n
        group = []
        for tag, i1, i2, j1, j2 in codes:
            # End the current group and start a new one whenever
            # there is a large range with no changes.
            if tag == "equal" and i2 - i1 > nn:
                group.append((tag, i1, min(i2, i1 + n), j1, min(j2, j1 + n)))
                yield group
                group = []
                i1, j1 = max(i1, i2 - n), max(j1, j2 - n)
            group.append((tag, i1, i2, j1, j2))
        if group and not (len(group) == 1 and group[0][0] == "equal"):
            yield group

    def ratio(self):
        """Return a measure of the sequences' similarity (float in [0,1]).

        Where T is the total number of elements in both sequences, and
        M is the number of matches, this is 2.0*M / T.
        Note that this is 1 if the sequences are identical, and 0 if
        they have nothing in common.

        .ratio() is expensive to compute if you haven't already computed
        .get_matching_blocks() or .get_opcodes(), in which case you may
        want to try .quick_ratio() or .real_quick_ratio() first to get an
        upper bound.

        >>> s = SequenceMatcher(None, "abcd", "bcde")
        >>> s.ratio()
        0.75
        >>> s.quick_ratio()
        0.75
        >>> s.real_quick_ratio()
        1.0
        """

        if self._ratio:
            return self._ratio
        a = self.a if self.a_real_content is None else self.a_real_content
        b = self.b if self.b_real_content is None else self.b_real_content
        # compute the similar ratio and cache it
        matches = reduce(
            lambda count, triple: count + triple[-1],
            SequenceMatcher(self.isjunk, a, b).get_matching_blocks(),
            0,
        )
        self._ratio = _calculate_ratio(matches, len(a) + len(b))
        return self._ratio

    def quick_ratio(self):
        """Return an upper bound on ratio() relatively quickly.

        This isn't defined beyond that it is an upper bound on .ratio(), and
        is faster to compute.
        """

        a = self.a if self.a_real_content is None else self.a_real_content
        b = self.b if self.b_real_content is None else self.b_real_content
        # viewing a and b as multisets, set matches to the cardinality
        # of their intersection; this counts the number of matches
        # without regard to order, so is clearly an upper bound
        if self.fullbcount is None:
            self.fullbcount = fullbcount = {}
            for elt in b:
                fullbcount[elt] = fullbcount.get(elt, 0) + 1
        fullbcount = self.fullbcount
        # avail[x] is the number of times x appears in 'b' less the
        # number of times we've seen it in 'a' so far ... kinda
        avail = {}
        availhas, matches = avail.__contains__, 0
        for elt in a:
            if availhas(elt):
                numb = avail[elt]
            else:
                numb = fullbcount.get(elt, 0)
            avail[elt] = numb - 1
            if numb > 0:
                matches = matches + 1
        return _calculate_ratio(matches, len(a) + len(b))

    def real_quick_ratio(self):
        """Return an upper bound on ratio() very quickly.

        This isn't defined beyond that it is an upper bound on .ratio(), and
        is faster to compute than either .ratio() or .quick_ratio().
        """

        la = len(
            self.a if self.a_real_content is None else self.a_real_content
        )
        lb = len(
            self.b if self.b_real_content is None else self.b_real_content
        )
        # can't have more matches than the number of elements in the
        # shorter sequence
        return _calculate_ratio(min(la, lb), la + lb)


def get_close_matches(word, possibilities, n=3, cutoff=0.6):
    """Use SequenceMatcher to return list of the best "good enough" matches.

    word is a sequence for which close matches are desired (typically a
    string).

    possibilities is a list of sequences against which to match word
    (typically a list of strings).

    Optional arg n (default 3) is the maximum number of close matches to
    return.  n must be > 0.

    Optional arg cutoff (default 0.6) is a float in [0, 1].  Possibilities
    that don't score at least that similar to word are ignored.

    The best (no more than n) matches among the possibilities are returned
    in a list, sorted by similarity score, most similar first.

    >>> get_close_matches("appel", ["ape", "apple", "peach", "puppy"])
    ['apple', 'ape']
    >>> import keyword as _keyword
    >>> get_close_matches("wheel", _keyword.kwlist)
    ['while']
    >>> get_close_matches("apple", _keyword.kwlist)
    []
    >>> get_close_matches("accept", _keyword.kwlist)
    ['except']
    """

    if not n > 0:
        raise ValueError("n must be > 0: %r" % (n,))
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result = []
    s = SequenceMatcher()
    s.set_seq2(word)
    for x in possibilities:
        s.set_seq1(x)
        if (
            s.real_quick_ratio() >= cutoff
            and s.quick_ratio() >= cutoff
            and s.ratio() >= cutoff
        ):
            result.append((s.ratio(), x))

    # Move the best scorers to head of list
    result = heapq.nlargest(n, result)
    # Strip scores for the best n matches
    return [x for score, x in result]


class FuzzyMatchingString(str):
    """
    Inherits built-in str, but two strings can be considered equal when
    their content in accord with the rules defined.
    """

    def __new__(cls, value, *args, **kwargs):
        return super(FuzzyMatchingString, cls).__new__(cls, value)

    def __init__(self, value, *args, **kwargs):
        raise NotImplementedError("FuzzyMatchingString: Not implemented!")

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.real_content() == other.real_content()
        else:
            return self.real_content() == str(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def real_content(self):
        return None


class SpaceIgnoredString(FuzzyMatchingString):
    """
    Inherits FuzzyMatchingString, ingores whitespace and space change
    when compared with other strings.
    """

    def __init__(
        self, value, ignore_space_change=False, ignore_whitespaces=False
    ):
        self.ignore_space_change = ignore_space_change
        self.ignore_whitespaces = ignore_whitespaces

    def real_content(self):
        if self.ignore_whitespaces:
            return re.sub(r"\s+", "", self)
        elif self.ignore_space_change:
            # gnu diff ignores all whitespace (include line-feed) in the
            # right side when compare with -b or --ignore-space-change,
            # just simulatethat behavior
            return re.sub(r"\s+", " ", self).rstrip()
        else:
            return str(self)


class Differ:
    r"""
    Differ is a class for comparing sequences of lines of text, and
    producing human-readable differences or deltas.  Differ uses
    SequenceMatcher both to compare sequences of lines, and to compare
    sequences of characters within similar (near-matching) lines.

    Use get_opcodes() and get_merged_opcodes() to get a list of 5-tuples
    describing how to turn a into b. The former can give detailed
    transformation steps, especially the 'replace' operation for similar
    lines will be recorded, it is userful for ndiff (not implemented in
    this file), the latter gives concise transformation steps by merging
    adjacent op items if they can be merged. get_grouped_opcodes() is used
    for context_diff() and unified_diff().

    Example: Comparing two texts.

    >>> a = ['aaa\n', 'bbb\n', 'c\n', 'cc\n', 'ccc\n', '\n', 'ddd\n',
    ... 'eee\n', 'ggg\n']
    >>> b = ['aaaa\n', 'bbbb\n', 'c\n', 'cc\n', 'ccc\n', 'dddd\n', 'hhh\n',
    ... 'fff\n', '\n', 'ggg\n']
    >>> d = Differ()
    >>> for op in d.get_opcodes(a, b): print(op)
    ...
    ('replace', 0, 1, 0, 1)
    ('replace', 1, 2, 1, 2)
    ('equal', 2, 5, 2, 5)
    ('delete', 5, 6, 5, 5)
    ('replace', 6, 7, 5, 6)
    ('replace', 7, 8, 6, 9)
    ('equal', 8, 9, 9, 10)
    >>> for op in d.get_merged_opcodes(a, b): print(op)
    ...
    ('replace', 0, 2, 0, 2)
    ('equal', 2, 5, 2, 5)
    ('replace', 5, 8, 5, 9)
    ('equal', 8, 9, 9, 10)
    >>> for op in d.get_grouped_opcodes(a, b, 1): print(op)
    ...
    [('replace', 0, 2, 0, 2), ('equal', 2, 3, 2, 3)]
    [('equal', 4, 5, 4, 5), ('replace', 5, 8, 5, 9), ('equal', 8, 9, 9, 10)]

    Note that when instantiating a Differ object we may pass functions to
    filter out line and character 'junk'.  See Differ.__init__ for details.
    """

    def __init__(
        self,
        linejunk=None,
        charjunk=None,
        ignore_space_change=False,
        ignore_whitespaces=False,
        ignore_blank_lines=False,
    ):
        """
        Construct a text differencer, with optional filters.

        The two optional keyword parameters are for filter functions:

        - `linejunk`: A function that should accept a single string argument,
          and return true iff the string is junk. The module-level function
          `IS_LINE_JUNK` may be used to filter out lines without visible
          characters, except for at most one splat ('#').  It is recommended
          to leave linejunk None; as of Python 2.3, the underlying
          SequenceMatcher class has grown an adaptive notion of "noise" lines
          that's better than any static definition the author has ever been
          able to craft.

        - `charjunk`: A function that should accept a string of length 1. The
          module-level function `IS_CHARACTER_JUNK` may be used to filter out
          whitespace characters (a blank or tab; **note**: bad idea to include
          newline in this!).  Use of IS_CHARACTER_JUNK is recommended.

        - `ignore_space_change`: refer to gnu diff option -b

        - `ignore_whitespaces`: refer to gnu diff option -w

        - `ignore_blank_lines`: refer to gnu diff option -B
        """

        self.linejunk = linejunk
        self.charjunk = charjunk
        self.ignore_space_change = ignore_space_change
        self.ignore_whitespaces = ignore_whitespaces
        self.ignore_blank_lines = ignore_blank_lines

    def get_opcodes(self, a, b):
        r"""
        Compare two sequences of lines; generate the resulting delta.

        Each sequence must contain individual single-line strings ending with
        newlines. Such sequences can be obtained from the `readlines()` method
        of file-like objects. The delta generated also consists of newline-
        terminated strings, ready to be printed as-is via the writeline()
        method of a file-like object.

        Example:

        >>> for op in Differ().get_opcodes('one\ntwo\nthree\n',
        ...                                'ore\nthree\nemu\n'):
        ...    print(op)
        ...
        ('replace', 0, 2, 0, 1)
        ('equal', 2, 3, 1, 2)
        ('insert', 3, 3, 2, 3)
        """

        assert all(str(i) != "" for i in a) and all(str(j) != "" for j in b)
        if self.ignore_space_change or self.ignore_whitespaces:
            new_a, new_b = [], []
            for i in a:
                new_a.append(
                    SpaceIgnoredString(
                        i, self.ignore_space_change, self.ignore_whitespaces
                    )
                )
            for j in b:
                new_b.append(
                    SpaceIgnoredString(
                        j, self.ignore_space_change, self.ignore_whitespaces
                    )
                )
            a, b = new_a, new_b

        cruncher = SequenceMatcher(self.linejunk, a, b)
        for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
            if tag == "replace":
                # `_fancy_replace` can give us a more specific result, for
                # example, it can recognize completely equal lines among
                # a block of line junks. it is also useful when we want to
                # show exact difference line by line like what ndiff does.
                g = self._fancy_replace(a, alo, ahi, b, blo, bhi)
            elif tag in ("equal", "delete", "insert"):
                g = ((tag, alo, ahi, blo, bhi),)
            else:
                raise ValueError("unknown tag %r" % (tag,))

            for tag, alo, ahi, blo, bhi in g:
                yield (tag, alo, ahi, blo, bhi)

    def get_merged_opcodes(self, a, b):
        r"""
        Similar like get_opcodes(), but the adjacent items might be merge
        as one, for example:

        ('equal', 2, 9, 0, 7)
        ('equal', 9, 11, 7, 9)
        ('replace', 11, 12, 9, 10)
        ('replace', 12, 13, 10, 11)
        ('replace', 13, 14, 11, 12)
        will be merged as:
        ('equal', 2, 11, 0, 9)
        ('replace', 11, 14, 9, 12)

        Another example:

        ('delete', 11, 12, 10, 10)
        ('replace', 12, 13, 10, 11)
        will be merged as:
        ('replace', 11, 13, 10, 11)
        """

        g = self._merge_opcodes(self.get_opcodes(a, b))
        if self.ignore_blank_lines:
            g = self._merge_opcodes(self._verify_blank_lines(a, b, g))

        for tag, alo, ahi, blo, bhi in g:
            yield (tag, alo, ahi, blo, bhi)

    def get_grouped_opcodes(self, a, b, n=3):
        """Isolate change clusters by eliminating ranges with no changes.

        Return a generator of groups with up to n lines of context.
        Each group is in the same format as returned by get_opcodes().

        >>> from pprint import pprint
        >>> a = map(str, range(1,40))
        >>> b = a[:]
        >>> b[8:8] = ['i']     # Make an insertion
        >>> b[20] += 'x'       # Make a replacement
        >>> b[23:28] = []      # Make a deletion
        >>> b[30] += 'y'       # Make another replacement
        >>> pprint(list(SequenceMatcher(None,a,b).get_grouped_opcodes()))
        [[('equal', 5, 8, 5, 8),
          ('insert', 8, 8, 8, 9),
          ('equal', 8, 11, 9, 12)],
         [('equal', 16, 19, 17, 20),
          ('replace', 19, 20, 20, 21),
          ('equal', 20, 22, 21, 23),
          ('delete', 22, 27, 23, 23),
          ('equal', 27, 30, 23, 26)],
         [('equal', 31, 34, 27, 30),
          ('replace', 34, 35, 30, 31),
          ('equal', 35, 38, 31, 34)]]
        """

        def _is_blank_block(code):
            "Check if the opcode represents blank lines"
            return code[0] == "equal" and (
                code[1] == code[2] or code[3] == code[4]
            )

        def _check_adjacent_blank_block(codes, i):
            """Make change to the nearest opcode of blank lines if there are
            no more than `n` lines between them."""
            if i >= 0 and i < len(codes) and _is_blank_block(codes[i]):
                # code[i-1][0] or code[i+1][0] MUST BE 'equal' if it exists
                if (
                    i < len(codes) - 2
                    and codes[i + 1][2] - codes[i + 1][1] < n
                    and codes[i + 2][0] != "equal"
                    or i > 1
                    and codes[i - 1][2] - codes[i - 1][1] < n
                    and codes[i - 2][0] != "equal"
                ):
                    tag, i1, i2, j1, j2 = codes[i]
                    codes[i] = (
                        "insert" if i1 == i2 else "delete",
                        i1,
                        i2,
                        j1,
                        j2,
                    )
                    _check_adjacent_blank_block(codes, i - 2)
                    _check_adjacent_blank_block(codes, i + 2)

        g = self._merge_opcodes(self.get_opcodes(a, b))
        if self.ignore_blank_lines:
            g = self._verify_blank_lines(a, b, g)
        codes = list(g)

        # Block composed of blank lines already changed its tag to 'equal',
        # but in a unified or context diff, we might have to output them.
        if self.ignore_blank_lines:
            for i in range(len(codes)):
                _check_adjacent_blank_block(codes, i)
            codes = list(self._merge_opcodes(codes))

        if not codes:
            codes = [("equal", 0, 1, 0, 1)]
        # Fixup leading and trailing groups if they show no changes.
        if codes[0][0] == "equal":
            tag, i1, i2, j1, j2 = codes[0]
            codes[0] = (tag, max(i1, i2 - n), i2, max(j1, j2 - n), j2)
        if codes[-1][0] == "equal":
            tag, i1, i2, j1, j2 = codes[-1]
            codes[-1] = (tag, i1, min(i2, i1 + n), j1, min(j2, j1 + n))

        nn = n + n
        group = []
        for tag, i1, i2, j1, j2 in codes:
            # End the current group and start a new one whenever
            # there is a large range with no changes.
            if tag == "equal" and i2 - i1 > nn:
                group.append((tag, i1, min(i2, i1 + n), j1, min(j2, j1 + n)))
                yield group
                group = []
                i1, j1 = max(i1, i2 - n), max(j1, j2 - n)
            group.append((tag, i1, i2, j1, j2))

        if group and not (len(group) == 1 and group[0][0] == "equal"):
            yield group

    def _merge_opcodes(self, generator):
        "Algorithm for merging opcode"
        prev_tag = ""
        prev_alo, prev_ahi, prev_blo, prev_bhi = 0, 0, 0, 0

        for tag, alo, ahi, blo, bhi in generator:
            assert prev_ahi == alo and prev_bhi == blo
            if prev_tag == tag or not prev_tag:
                prev_tag, prev_ahi, prev_bhi = tag, ahi, bhi
            elif tag == "equal" or prev_tag == "equal":
                yield (prev_tag, prev_alo, prev_ahi, prev_blo, prev_bhi)
                prev_tag = tag
                prev_alo, prev_ahi, prev_blo, prev_bhi = alo, ahi, blo, bhi
            else:
                prev_tag, prev_ahi, prev_bhi = "replace", ahi, bhi

        if prev_tag:
            yield (prev_tag, prev_alo, prev_ahi, prev_blo, prev_bhi)

    def _verify_blank_lines(self, a, b, g):
        "Modify tag if all lines in a deletion or insertion block are blank"
        for tag, alo, ahi, blo, bhi in g:
            if (
                tag == "delete"
                and all(
                    str(a[i]) in ("\n", "\r\n", "\r") for i in range(alo, ahi)
                )
                or tag == "insert"
                and all(
                    str(b[j]) in ("\n", "\r\n", "\r") for j in range(blo, bhi)
                )
            ):
                yield ("equal", alo, ahi, blo, bhi)
            else:
                yield (tag, alo, ahi, blo, bhi)

    def _fancy_replace(self, a, alo, ahi, b, blo, bhi):
        r"""
        When replacing one block of lines with another, search the blocks
        for *similar* lines; the best-matching pair (if any) is used as a
        synch point, and intraline difference marking is done on the
        similar pair. Lots of work, but often worth it.

        Example:

        >>> for op in Differ()._fancy_replace('abcDefghiJkl\n', 3, 12,
        ...                                  'abcdefGhijkl\n', 3, 12):
        ...     print(op)
        ...
        ('replace', 3, 4, 3, 4)
        ('equal', 4, 5, 4, 5)
        ('equal', 5, 6, 5, 6)
        ('replace', 6, 7, 6, 7)
        ('equal', 7, 8, 7, 8)
        ('equal', 8, 9, 8, 9)
        ('replace', 9, 10, 9, 10)
        ('equal', 10, 11, 10, 11)
        ('equal', 11, 12, 11, 12)
        """

        # don't synch up unless the lines have a similarity score of at
        # least cutoff; best_ratio tracks the best score seen so far

        best_ratio, junk_line_best_ratio, cutoff = 0.74, 0.74, 0.75
        best_i, best_j, junk_line_best_i, junk_line_best_j = -1, -1, -1, -1
        cruncher = SequenceMatcher(self.charjunk)
        eqi, eqj = None, None  # 1st indices of equal lines (if any)

        # search for the pair that matches best without being identical
        # (identical lines must be junk lines, & we don't want to synch up
        # on junk -- unless we have to)
        for j in range(blo, bhi):
            bj = b[j]
            cruncher.set_seq2(bj)
            for i in range(alo, ahi):
                ai = a[i]
                if ai == bj:
                    # here, at least ai or bj MUST BE link junks
                    if eqi is None:
                        eqi, eqj = i, j
                    continue
                cruncher.set_seq1(ai)
                # computing similarity is expensive, so use the quick
                # upper bounds first -- have seen this speed up messy
                # compares by a factor of 3.
                # note that ratio() is only expensive to compute the first
                # time it's called on a sequence pair; the expensive part
                # of the computation is cached by cruncher
                if (
                    cruncher.real_quick_ratio() > best_ratio
                    and cruncher.quick_ratio() > best_ratio
                    and cruncher.ratio() > best_ratio
                ):
                    # junk line should not be considered as very similar to
                    # normal line or other junk line unless there's no other
                    # similar normal lines found
                    if self.linejunk and (
                        self.linejunk(ai) or self.linejunk(bj)
                    ):
                        if cruncher.ratio() > junk_line_best_ratio:
                            junk_line_best_ratio = cruncher.ratio()
                            junk_line_best_i, junk_line_best_j = i, j
                    else:
                        best_ratio, best_i, best_j = cruncher.ratio(), i, j

        # priority: normal lines (pretty close) > line junks (identical)
        #                                       > line junks (pretty close)
        if best_ratio < cutoff:
            # no non-identical "pretty close" pair
            if eqi is None:
                # no identical pair either -- treat it as a straight replace
                if junk_line_best_ratio < cutoff:
                    # even no non-identical "pretty close" line junks found
                    # treat it as a straight replace
                    yield ("replace", alo, ahi, blo, bhi)
                    return
                else:
                    # at least we can find junk lines that are pretty close
                    best_i, best_j = junk_line_best_i, junk_line_best_j
                    best_ratio = junk_line_best_ratio
            else:
                # no close pair, but an identical pair -- synch up on that
                best_i, best_j, best_ratio = eqi, eqj, 1.0
        else:
            # there's a close pair, so forget the identical pair (if any)
            eqi = None

        # a[best_i] very similar to b[best_j]; eqi is None if they're not
        # identical

        # pump out diffs from before the synch point
        for opcode in self._fancy_helper(a, alo, best_i, b, blo, best_j):
            yield opcode

        # generate op code on the synch pair
        if eqi is None:
            # the synch pair is similar
            yield ("replace", best_i, best_i + 1, best_j, best_j + 1)
        else:
            # the synch pair is identical
            yield ("equal", best_i, best_i + 1, best_j, best_j + 1)

        # pump out diffs from after the synch point
        for opcode in self._fancy_helper(
            a, best_i + 1, ahi, b, best_j + 1, bhi
        ):
            yield opcode

    def _fancy_helper(self, a, alo, ahi, b, blo, bhi):
        g = []
        if alo < ahi:
            if blo < bhi:
                g = self._fancy_replace(a, alo, ahi, b, blo, bhi)
            else:
                g = [("delete", alo, ahi, blo, bhi)]
        elif blo < bhi:
            g = [("insert", alo, ahi, blo, bhi)]

        for opcode in g:
            yield opcode


# With respect to junk, an earlier version of ndiff simply refused to
# *start* a match with a junk element.  The result was cases like this:
#     before: private Thread currentThread;
#     after:  private volatile Thread currentThread;
# If you consider whitespace to be junk, the longest contiguous match
# not starting with junk is "e Thread currentThread".  So ndiff reported
# that "e volatil" was inserted between the 't' and the 'e' in "private".
# While an accurate view, to people that's absurd.  The current version
# looks for matching blocks that are entirely junk-free, then extends the
# longest one of those as far as possible but only with matching junk.
# So now "currentThread" is matched, then extended to suck up the
# preceding blank; then "private" is matched, and extended to suck up the
# following blank; then "Thread" is matched; and finally ndiff reports
# that "volatile " was inserted before "Thread".  The only quibble
# remaining is that perhaps it was really the case that " volatile"
# was inserted after "private".  I can live with that <wink>.


def IS_LINE_JUNK(line, pat=re.compile(r"\s*#?\s*$").match):
    r"""
    Return 1 for ignorable line: iff `line` is blank or contains a single '#'.

    Examples:

    >>> IS_LINE_JUNK('\n')
    True
    >>> IS_LINE_JUNK('  #   \n')
    True
    >>> IS_LINE_JUNK('hello\n')
    False
    """

    return pat(line) is not None


def IS_CHARACTER_JUNK(ch, ws=" \t"):
    r"""
    Return 1 for ignorable character: iff `ch` is a space or tab.

    Examples:

    >>> IS_CHARACTER_JUNK(' ')
    True
    >>> IS_CHARACTER_JUNK('\t')
    True
    >>> IS_CHARACTER_JUNK('\n')
    False
    >>> IS_CHARACTER_JUNK('x')
    False
    """

    return ch in ws


########################################################################
###  Diff
########################################################################


def diff(
    a,
    b,
    ignore_space_change=False,
    ignore_whitespaces=False,
    ignore_blank_lines=False,
    unified=False,
    context=False,
):
    r"""
    Compare two blocks of text or two sequences of lines and generate delta
    as a normal/unified/context diff. Lines that only contain whitespaces
    have lower priority to get matched.

    If a or b is a string, then is will be split as list of strings which
    are separated by '\n', '\r\n' or '\r', while keep the line terminator.

    By default, the function generates the delta as a normal diff, but you
    can specify a unified diff or context diff. And you can directly set the
    parameter unified or context to a positive integer, that means the number
    of context lines, which defaults to three.

    - `ignore_space_change`: refer to gnu diff option -b
    - `ignore_whitespaces`: refer to gnu diff option -w
    - `ignore_blank_lines`: refer to gnu diff option -B
    - `unified`: if True, output in unified format, default False
    - `context`: if True, output in context format, default False
    """

    a = a.splitlines(True) if isinstance(a, str) else a
    b = b.splitlines(True) if isinstance(b, str) else b
    assert isinstance(a, list) and isinstance(b, list)

    if unified:
        n = 3 if isinstance(unified, bool) else int(unified)
        assert n > 0
        g = unified_diff(
            a,
            b,
            n,
            ignore_space_change,
            ignore_whitespaces,
            ignore_blank_lines,
        )
    elif context:
        n = 3 if isinstance(context, int) else int(context)
        assert n > 0
        g = context_diff(
            a,
            b,
            n,
            ignore_space_change,
            ignore_whitespaces,
            ignore_blank_lines,
        )
    else:
        g = _diff(
            a, b, ignore_space_change, ignore_whitespaces, ignore_blank_lines
        )

    return g


########################################################################
###  Basic Diff
########################################################################


def _dump_line(prefix, content):
    "Add a prefix in front, also add line break at tail if there is not one"
    if not content.endswith("\n"):
        yield prefix + content + os.linesep
        yield "\\ No newline at end of file" + os.linesep
    else:
        yield prefix + content


def _diff(
    a,
    b,
    ignore_space_change=False,
    ignore_whitespaces=False,
    ignore_blank_lines=False,
):
    r"""
    Compare `a` and `b` (lists of strings); return a delta of gnu diff style.

    - `ignore_space_change`: refer to gnu diff option -b
    - `ignore_whitespaces`: refer to gnu diff option -w
    - `ignore_blank_lines`: refer to gnu diff option -B

    Example:

    >>> difference = _diff('one\ntwo\nthree\n'.splitlines(True),
                           'ore\nthree\nemu\n'.splitlines(True))
    >>> print(''.join(difference))
    1,2c1
    < one
    < two
    ---
    > ore
    3a3
    > emu
    """

    for tag, alo, ahi, blo, bhi in Differ(
        linejunk=IS_LINE_JUNK,
        charjunk=None,
        ignore_space_change=ignore_space_change,
        ignore_whitespaces=ignore_whitespaces,
        ignore_blank_lines=ignore_blank_lines,
    ).get_merged_opcodes(a, b):
        if tag == "replace":
            head_a = (
                "{},{}".format(alo + 1, ahi) if ahi - alo > 1 else str(alo + 1)
            )
            head_b = (
                "{},{}".format(blo + 1, bhi) if bhi - blo > 1 else str(blo + 1)
            )
            yield "{}c{}{}".format(head_a, head_b, os.linesep)
            for line in a[alo:ahi]:
                for text in _dump_line("< ", line):
                    yield text
            yield "---" + os.linesep
            for line in b[blo:bhi]:
                for text in _dump_line("> ", line):
                    yield text
        elif tag == "delete":
            head_a = (
                "{},{}".format(alo + 1, ahi) if ahi - alo > 1 else str(alo + 1)
            )
            yield "{}d{}{}".format(head_a, bhi, os.linesep)
            for line in a[alo:ahi]:
                for text in _dump_line("< ", line):
                    yield text
        elif tag == "insert":
            head_b = (
                "{},{}".format(blo + 1, bhi) if bhi - blo > 1 else str(blo + 1)
            )
            yield "{}a{}{}".format(alo, head_b, os.linesep)
            for line in b[blo:bhi]:
                for text in _dump_line("> ", line):
                    yield text


########################################################################
###  Unified Diff
########################################################################


def _format_range_unified(start, stop):
    'Convert range to the "ed" format'
    # Per the diff spec at http://www.unix.org/single_unix_specification/
    beginning = start + 1  # lines start numbering with one
    length = stop - start
    if length == 1:
        return "{}".format(beginning)
    if not length:
        beginning -= 1  # empty ranges begin at line just before the range
    return "{},{}".format(beginning, length)


def unified_diff(
    a,
    b,
    n=3,
    ignore_space_change=False,
    ignore_whitespaces=False,
    ignore_blank_lines=False,
):
    r"""
    Compare two sequences of lines; generate the delta as a unified diff.

    Unified diffs are a compact way of showing line changes and a few
    lines of context.  The number of context lines is set by 'n' which
    defaults to three.

    By default, the diff control lines (those with ---, +++, or @@) are
    created with a trailing newline.  This is helpful so that inputs
    created from file.readlines() result in diffs that are suitable for
    file.writelines() since both the inputs and outputs have trailing
    newlines.

    The unidiff format normally has a header for filenames and modification
    times. Here, "a.text" and "b.text" are displayed instead of file names,
    and current UTC time instead of the modification time.

    - `ignore_space_change`: refer to gnu diff option -b
    - `ignore_whitespaces`: refer to gnu diff option -w
    - `ignore_blank_lines`: refer to gnu diff option -B

    Example:

    >>> difference = unified_diff('one\ntwo\nthree\n'.splitlines(True),
                                  'ore\nthree\nemu\n'.splitlines(True))
    >>> print(''.join(difference))
    --- a.text    2018-08-28 11:36:46 UTC
    +++ b.text    2018-08-28 11:36:46 UTC
    @@ -1,3 +1,3 @@
    -one
    -two
    +ore
     three
    +emu
    """

    started = False
    for group in Differ(
        linejunk=IS_LINE_JUNK,
        charjunk=None,
        ignore_space_change=ignore_space_change,
        ignore_whitespaces=ignore_whitespaces,
        ignore_blank_lines=ignore_blank_lines,
    ).get_grouped_opcodes(a, b, n):
        if not started:
            started = True
            utc_time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            fromdate = todate = "\t{}".format(utc_time_str)
            yield "--- {}{}{}".format("a.text", fromdate, os.linesep)
            yield "+++ {}{}{}".format("b.text", todate, os.linesep)

        first, last = group[0], group[-1]
        file1_range = _format_range_unified(first[1], last[2])
        file2_range = _format_range_unified(first[3], last[4])
        yield "@@ -{} +{} @@{}".format(file1_range, file2_range, os.linesep)

        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                for line in a[i1:i2]:
                    for text in _dump_line(" ", line):
                        yield text
                continue
            if tag in ("replace", "delete"):
                for line in a[i1:i2]:
                    for text in _dump_line("-", line):
                        yield text
            if tag in ("replace", "insert"):
                for line in b[j1:j2]:
                    for text in _dump_line("+", line):
                        yield text


########################################################################
###  Context Diff
########################################################################


def _format_range_context(start, stop):
    'Convert range to the "ed" format'
    # Per the diff spec at http://www.unix.org/single_unix_specification/
    beginning = start + 1  # lines start numbering with one
    length = stop - start
    if not length:
        beginning -= 1  # empty ranges begin at line just before the range
    if length <= 1:
        return "{}".format(beginning)
    return "{},{}".format(beginning, beginning + length - 1)


# See http://www.unix.org/single_unix_specification/
def context_diff(
    a,
    b,
    n=3,
    ignore_space_change=False,
    ignore_whitespaces=False,
    ignore_blank_lines=False,
):
    r"""
    Compare two sequences of lines; generate the delta as a context diff.

    Context diffs are a compact way of showing line changes and a few
    lines of context.  The number of context lines is set by 'n' which
    defaults to three.

    By default, the diff control lines (those with *** or ---) are
    created with a trailing newline.  This is helpful so that inputs
    created from file.readlines() result in diffs that are suitable for
    file.writelines() since both the inputs and outputs have trailing
    newlines.

    The context diff format normally has a header for filenames and
    modification times. Here, "a.text" and "b.text" are displayed instead of
    file names, and current UTC time instead of the modification time.

    - `ignore_space_change`: refer to gnu diff option -b
    - `ignore_whitespaces`: refer to gnu diff option -w
    - `ignore_blank_lines`: refer to gnu diff option -B

    Example:

    >>> difference = context_diff('one\ntwo\nthree\n'.splitlines(True),
                                  'ore\nthree\nemu\n'.splitlines(True))
    >>> print(''.join(difference))
    --- a.text    2018-08-28 11:40:17 UTC
    +++ b.text    2018-08-28 11:40:17 UTC
    ***************
    *** 1,3 ****
    ! one
    ! two
      three
    --- 1,3 ----
    ! ore
      three
    + emu
    """

    prefix = dict(insert="+ ", delete="- ", replace="! ", equal="  ")
    started = False
    for group in Differ(
        linejunk=IS_LINE_JUNK,
        charjunk=None,
        ignore_space_change=ignore_space_change,
        ignore_whitespaces=ignore_whitespaces,
        ignore_blank_lines=ignore_blank_lines,
    ).get_grouped_opcodes(a, b, n):
        if not started:
            started = True
            utc_time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            fromdate = todate = "\t{}".format(utc_time_str)
            yield "--- {}{}{}".format("a.text", fromdate, os.linesep)
            yield "+++ {}{}{}".format("b.text", todate, os.linesep)

        first, last = group[0], group[-1]
        yield "***************" + os.linesep

        file1_range = _format_range_context(first[1], last[2])
        yield "*** {} ****{}".format(file1_range, os.linesep)

        if any(tag in ("replace", "delete") for tag, _, _, _, _ in group):
            for tag, i1, i2, _, _ in group:
                if tag != "insert":
                    for line in a[i1:i2]:
                        for text in _dump_line(prefix[tag], line):
                            yield text

        file2_range = _format_range_context(first[3], last[4])
        yield "--- {} ----{}".format(file2_range, os.linesep)

        if any(tag in ("replace", "insert") for tag, _, _, _, _ in group):
            for tag, _, _, j1, j2 in group:
                if tag != "delete":
                    for line in b[j1:j2]:
                        for text in _dump_line(prefix[tag], line):
                            yield text
