.DEFAULT_GOAL := help

.PHONY: help fix check tsc test validate schema detect-table compile

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Code Quality:"
	@echo "  fix          Lint and format"
	@echo "  check        Lint and format check"
	@echo "  tsc          TypeScript type-check only"
	@echo "  test         Run the unit tests"
	@echo ""
	@echo "Package:"
	@echo "  validate     Validate serverk.yml and the package contents"
	@echo "  schema       Write the serverk.yml JSON Schema for editor tooling"
	@echo "  detect-table Write image/detect.json, the table the launcher reads"
	@echo "  compile      Compile the bot package"

# --- Code Quality ---

fix:
	bun run fix

check:
	bun run check

tsc:
	bun run tsc

test:
	bun run test

# --- Package ---

validate:
	bun run validate

schema:
	bun run schema

detect-table:
	bun run detect-table

compile:
	bun run compile
