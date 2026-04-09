import copy
import re
from typing import Any, Dict, List, Optional, Union

from boltons.cacheutils import cachedproperty
from gherkin.ast_builder import AstBuilder
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner


def get_tags(parsed: Any) -> List[str]:
    return [tag["name"][1:] for tag in parsed.get("tags", [])]


class ParsedStore:
    def __init__(self, parsed: Any) -> None:
        super(ParsedStore, self).__init__()
        self._parsed = parsed

    @property
    def parsed(self) -> Any:
        return self._parsed

    def __getitem__(self, item: str) -> Any:
        return self._parsed.__getitem__(item)

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as e:
            raise AttributeError from e


class Feature(ParsedStore):
    def __init__(self, featurefile: str) -> None:
        try:
            with open(featurefile, "r") as f:
                content = f.read()
            parser = Parser(ast_builder=AstBuilder())
            feature = parser.parse(TokenScanner(content)).get("feature", {})
        except:
            print("Error parsing: {}".format(featurefile))
            raise

        if not feature:
            raise TypeError("Not valid feature file {}".format(featurefile))

        super(Feature, self).__init__(feature)
        self.file: str = featurefile
        self.background: Optional["Background"] = None
        self._scenarios: List[Union["Scenario", "ScenarioOutline"]] = []

        self.name: str = feature["name"]  # should be mandatory
        self.description: str = feature.get("description", "")
        self.tags: List[str] = get_tags(feature)

        self.parse_children(feature.get("children", []))

    @cachedproperty
    def scenarios(self) -> List["Scenario"]:
        scenarios: List["Scenario"] = []

        for scen in self._scenarios:
            if isinstance(scen, ScenarioOutline):
                scenarios.extend(scen.scenarios)
            else:
                scenarios.append(scen)

        return scenarios

    def parse_children(self, childrens: Any) -> None:
        for child in childrens:
            if "background" in child:
                self.background = Background(child["background"])
            elif "scenario" in child:
                keyword = child["scenario"]["keyword"]
                if keyword == "Scenario":
                    self._scenarios.append(
                        Scenario(child["scenario"], self.background)
                    )
                elif keyword == "Scenario Outline":
                    self._scenarios.append(
                        ScenarioOutline(child["scenario"], self.background)
                    )
            elif "rule" in child:
                raise RuntimeError(
                    "Rule keyword is not yet supported in Testplan BDD."
                )


class StepContainer:
    @cachedproperty
    def steps(self) -> List["Step"]:
        return self._steps()

    def _steps(self) -> List["Step"]:
        return [Step(step) for step in self.parsed.get("steps", [])]  # type: ignore[attr-defined]


class Scenario(ParsedStore, StepContainer):
    def __init__(
        self, parsed: Dict[str, Any], background: Optional["Background"] = None
    ) -> None:
        super(Scenario, self).__init__(parsed)

        self.name: str = self.parsed["name"]
        self.tags: List[str] = get_tags(parsed)
        self.description: str = self.parsed.get("description", "")
        self.background = background

    def __getitem__(self, item: str) -> Any:
        return self.parsed.__getitem__(item)

    @cachedproperty
    def steps(self) -> List["Step"]:
        steps: List["Step"] = []
        if self.background:
            steps += self.background.steps
        steps += self._steps()
        return steps


class Background(ParsedStore, StepContainer):
    def __init__(self, parsed: Dict[str, Any]) -> None:
        super(Background, self).__init__(parsed)


def parse_cells(row: Dict[str, Any]) -> List[Any]:
    return [cell.get("value") for cell in row.get("cells", [])]


def parse_rows(rows: List[Dict[str, Any]]) -> List[List[Any]]:
    return [parse_cells(row) for row in rows]


class DataTable(ParsedStore):
    def __init__(self, parsed: Dict[str, Any]) -> None:
        super(DataTable, self).__init__(parsed)

        self.data: List[List[Any]] = parse_rows(self.parsed["rows"])


class Example(ParsedStore):
    def __init__(self, parsed: Dict[str, Any]) -> None:
        super(Example, self).__init__(parsed)

        self.name: str = self.parsed["name"]
        self.data: List[List[Any]] = parse_rows(self.parsed["tableBody"])
        self.header: List[Any] = parse_cells(self.parsed["tableHeader"])
        self.description: str = self.parsed.get("description", "")


class ScenarioOutline(ParsedStore, StepContainer):
    def __init__(
        self, parsed: Dict[str, Any], background: Optional["Background"] = None
    ) -> None:
        super(ScenarioOutline, self).__init__(parsed)

        self.name: str = self.parsed["name"]
        self.tags: List[str] = get_tags(parsed)
        self.examples: List[Example] = [
            Example(example) for example in self.parsed["examples"]
        ]
        self.background = background
        self.description: str = self.parsed.get("description", "")

    @cachedproperty
    def scenarios(self) -> List[Scenario]:
        return self.compile_scenarios()

    def compile_scenarios(self) -> List[Scenario]:
        def resolve(
            item: Any,
            data: Dict[str, Any],
            paths: Any = [":"],
            current: str = ":",
        ) -> Any:
            def resolve_text(value: str) -> str:
                regexp = "(<([^>]*)>)"
                result = value
                for marker, name in re.findall(regexp, value):
                    result = result.replace(marker, data.get(name, marker))

                return result

            if current not in paths:
                return copy.deepcopy(item)

            if isinstance(item, dict):
                return {
                    k: resolve(v, data, paths, "{}.{}".format(current, k))
                    for k, v in item.items()
                }
            elif isinstance(item, list):
                return [resolve(i, data, paths, current) for i in item]
            elif isinstance(item, str):
                return resolve_text(item)
            else:
                pass  # TODO: Should not happen, raise an Exception?

        compiled_scenarios: List[Scenario] = []

        for example in self.examples:
            name = (
                "{} ({})".format(self.name, example.name)
                if len(example.name) > 0
                else self.name
            )
            for index, data in enumerate(example.data):
                data_dict = {
                    name: value for name, value in zip(example.header, data)
                }

                tags = copy.copy(self["tags"])
                tags.extend(example["tags"])

                scen_dict = {
                    "name": resolve("{} {}".format(name, index), data_dict),
                    "keyword:": "Scenario ",
                    "steps": [
                        resolve(
                            step,
                            data_dict,
                            ":.text:.dataTable.rows.cells.value:.docString.content",
                        )
                        for step in self["steps"]
                    ],
                    "tags": tags,
                    "description": resolve(
                        "{}\n{}".format(self.description, example.description),
                        data_dict,
                    ),
                }
                compiled_scenarios.append(Scenario(scen_dict, self.background))
        return compiled_scenarios


def get_argument(parsed: Dict[str, Any]) -> Optional[Union[str, DataTable]]:
    if "docString" in parsed:
        return parsed["docString"]["content"]  # type: ignore[no-any-return]

    if "dataTable" in parsed:
        return DataTable(parsed["dataTable"])

    return None


class Step(ParsedStore):
    def __init__(self, parsed: Dict[str, Any]) -> None:
        super(Step, self).__init__(parsed)

        self.text: str = self.parsed["text"]  # This should be there
        self.keyword: str = self.parsed["keyword"]
        self.argument: Optional[Union[str, DataTable]] = get_argument(
            self.parsed
        )

    @property
    def sentence(self) -> str:
        return "{}{}".format(self.keyword, self.text)
