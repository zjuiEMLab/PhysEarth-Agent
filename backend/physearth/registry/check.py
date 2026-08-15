"""Validate a model card before relying on it: python -m physearth.models.check <dir>"""

import sys
from pathlib import Path

import yaml

from physearth import registry
from physearth.registry import contract


def main(argv):
    if len(argv) != 2:
        print("usage: python -m physearth.models.check <model directory>")
        return 2

    directory = Path(argv[1])
    card_path = directory / "model_card.yaml"
    if not card_path.is_file():
        print("no model_card.yaml in %s" % directory)
        return 1

    try:
        card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print("the card is not valid YAML: %s" % exc)
        return 1

    problems = contract.validate_card(card)
    if problems:
        print("%d problem(s) in %s:" % (len(problems), card_path))
        for problem in problems:
            print("  - %s" % problem)
        return 1

    print("card is valid: %s v%s (tier %s)" % (card["name"], card["version"], card["tier"]))
    try:
        model = registry._load_directory(directory, "check")
    except contract.DeclarationError as exc:
        print("the card is valid but the adapter could not be loaded: %s" % exc)
        return 1

    print("adapter loaded: %s" % card["entrypoint"])
    print("parameters: %d, outputs: %s" % (len(card["parameters"]), ", ".join(card["outputs"])))
    if model.tier == "local":
        print("tier is local, so this model is registered but not run here")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
