SEARCH = terms:TERM_WITH_FREE_TEXT* free_text:WSENTENCE? _ {	
	let split = terms.reduce((c,a) => ({
    	free_text: c.free_text + a.free_text,
        terms: [...c.terms, a.term]
    }), {free_text: "", terms: []})
    return [...split.terms, {type: "free-text", search:split.free_text + (free_text || "")}]
}

TERM_WITH_FREE_TEXT = free_text:WSENTENCE? term:SEARCH_TERM {return {free_text: free_text || "" ,term} }

WSENTENCE =w:_ sentence:SENTENCE {return w+sentence}

SEARCH_TERM = OR_TERM2/OR_TERM1/TERM

OR_TERM2 = _ "{" terms:TERM* _ "}" { return { type:"OR", search: terms} }

OR_TERM1 = t1:TERM t:OR_TERM+ { return {type:"OR", search: [t1, ...t]} }

OR_TERM = _ "OR" _ t:TERM { return t}

TERM = type:KEYWORDS search:(SEARCH_TEXT_GROUP/SEARCH_TEXT_L) { return {type,search} }

SEARCH_TEXT_GROUP = "(" search_texts:WSEARCH_TEXT* _ ")" {return search_texts}

WSEARCH_TEXT = _ text:(SEARCH_TEXT) {return text}
SEARCH_TEXT_L = text:SEARCH_TEXT {return [text]}
SEARCH_TEXT = text:(EXACT_SEARCH/WORD) { return text}

EXACT_SEARCH = DOUBLE_QUOTE letters:[^\"]* DOUBLE_QUOTE { return letters.join("")}

SENTENCE = word:WORD words:WWORD* {return word + words.join("")} 
WWORD = ws:_ word:WORD {return ws+word}
WORD = !KEYWORDS str:[^ \t\n\r\"(){}]+ {return str.join("")}

KEYWORDS = _ kw:(TEST_W/SUITE_W/CASE_W/TAG_W/RE_W) ":" {return kw}
TEST_W = ("multitest"/"mt") {return "test"}
SUITE_W = ("testsuite"/"s") {return "suite"}
CASE_W = ("testcase"/"c") {return "case" }
TAG_W = "tag"
RE_W = ("regexp"/"re") {return "regexp"}

DOUBLE_QUOTE = "\""

_ "whitespace"
  = ws:[ \t\n\r]* {return ws.join("")}