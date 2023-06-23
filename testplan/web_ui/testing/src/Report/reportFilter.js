import _ from "lodash";

const name_filter = (level, entry, filter) => {
  // TODO: use a more structured form for name_type_index
  const names = _(entry.name_type_index)
    .filter((name) => name.endsWith(`|${level}`))
    .map((name) => name.split("|")[0])
    .invokeMap(String.prototype.toLowerCase)
    .value();
  return _(names).some((name) =>
    _(filter).every((search_name) => name.includes(search_name.toLowerCase()))
  );
};

const tag_filter = (entry, filter) => {
  //flatten the string: list map to the form the search is coming
  const tags = _(entry.tags_index)
    .flatMap((tags, name) =>
      tags.map((tag) => (name === "simple" ? tag : `${name}=${tag}`))
    )
    .invokeMap(String.prototype.toLowerCase)
    .value();
  return _(filter).every((tag) => tags.includes(tag.toLowerCase()));
};

const regexp_filter = (entry, filter) => {
  if (filter === "") {
    return true;
  }

  const regexp = new RegExp(filter);

  const names = (entry.name_type_index)
    .map((name_type) => name_type.split("|")[0]);

  return names.some((name) => name.match(regexp));
};

const free_text_filter = (entry, filter) => {
  if (filter === "") return true;

  const names = _(entry.name_type_index)
    .map((name_type) => name_type.split("|")[0])
    .invokeMap(String.prototype.toLowerCase)
    .value();

  const tags = _(entry.tags_index)
    .flatMapDeep((value, key) =>
      key === "simple"
        ? value
        : [
            key,
            value,
            _(value)
              .map((v) => `${key}=${v}`)
              .value(),
          ]
    )
    .invokeMap(String.prototype.toLowerCase)
    .uniq()
    .value();

  // we search for words from free text search
  // word separated by space or ','
  // tags/tag names must match fully
  // name is enough to contain the word
  return _(filter)
    .words(/[^, ]+/g)
    .invokeMap(String.prototype.toLowerCase)
    .map(
      (word) =>
        _(names)
          .map((name) => name.includes(word))
          .some() || tags.includes(word)
    )
    .some();
};

const or_filter = (entry, filters) => {
  return _(filters).some((filter) => processFilter(entry, filter));
};

const filter_processors = {
  "free-text": free_text_filter,
  regexp: regexp_filter,
  tag: tag_filter,
  test: _.partial(name_filter, "multitest"),
  suite: _.partial(name_filter, "testsuite"),
  case: _.partial(name_filter, "testcase"),
  OR: or_filter,
};

const stop_at = ["testcase"];

const processFilter = (entry, filter) => {
  if (filter_processors[filter.type]) {
    return filter_processors[filter.type](entry, filter.search);
  }
  return true;
};

const filterEntries = (entries, filters) => {
  return _(entries)
    .filter((entry) =>
      _(filters).every((filter) => processFilter(entry, filter))
    )
    .map((entry) => ({
      ...entry,
      entries: stop_at.includes(entry.category)
        ? entry.entries
        : filterEntries(entry.entries, filters),
    }))
    .filter(
      (entry) => stop_at.includes(entry.category) || entry.entries.length > 0
    )
    .value();
};

export { filterEntries };
