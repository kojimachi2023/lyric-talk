---
applyTo: "**/**"
---

# Code quality and Testing Instructions

<principles>

In this project, we use [pytest](https://github.com/pytest-dev/pytest/) installed in the uv environment and [ruff](https://docs.astral.sh/ruff/) installed in the uv environment for testing and linting/formatting respectively.

Write test frequently to ensure code quality and reliability. Follow best practices for writing tests, such as using descriptive names, testing edge cases, and maintaining isolation between tests.
Run the linter/formatter commands in the terminal to ensure consistent code style across the project. DO NOT EDIT FILES MANUALLY, and always use the linter/formatter commands.

Check <testing> and <linting_and_formatting> sections for more details.

</principles>

<testing>

You can run the tests by following command:

```bash
uv run pytest # run test
```

You can check options of pytest used in this project in [pyproject.toml](../pyproject.toml) file under the section `[tool.pytest.ini_options]`.

</testing>

<linting_and_formatting>

You can lint and format the code by following command:

```bash
uv run ruff check .          # lint the code
uv run ruff check . --fix    # format the code
```

</linting_and_formatting>
