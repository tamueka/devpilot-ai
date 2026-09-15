from types import SimpleNamespace
from app.services.unit_test_service import (
    _clean_generated_code,
    _get_suggested_filename,
)


def create_document(
    filename: str,
    extension: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        filename=filename,
        extension=extension,
    )


def test_clean_generated_code_without_markdown() -> None:
    content = (
        "describe('hello', () => {\n"
        "  expect(true).toBe(true);\n"
        "});"
    )

    result = _clean_generated_code(
        content,
    )
    assert result == content


def test_clean_generated_code_removes_typescript_fence() -> None:
    content = (
        "```typescript\n"
        "describe('hello', () => {\n"
        "  expect(true).toBe(true);\n"
        "});\n"
        "```"
    )
    
    result = _clean_generated_code(
        content,
    )

    assert result == (
        "describe('hello', () => {\n"
        "  expect(true).toBe(true);\n"
        "});"
    )


def test_clean_generated_code_removes_python_fence() -> None:
    content = (
        "```python\n"
        "def test_example():\n"
        "    assert True\n"
        "```"
    )

    result = _clean_generated_code(
        content,
    )

    assert result == (
        "def test_example():\n"
        "    assert True"
    )


def test_typescript_test_filename() -> None:
    document = create_document(
        filename="user.service.ts",
        extension=".ts",
    )

    result = _get_suggested_filename(
        document,
    )

    assert result == "user.service.spec.ts"


def test_javascript_test_filename() -> None:
    document = create_document(
        filename="calculator.js",
        extension=".js",
    )

    result = _get_suggested_filename(
        document,
    )

    assert result == "calculator.test.js"


def test_python_test_filename() -> None:
    document = create_document(
        filename="calculator.py",
        extension=".py",
    )

    result = _get_suggested_filename(
        document,
    )

    assert result == "test_calculator.py"


def test_java_test_filename() -> None:
    document = create_document(
        filename="Calculator.java",
        extension=".java",
    )

    result = _get_suggested_filename(
        document,
    )

    assert result == "CalculatorTest.java"


def test_csharp_test_filename() -> None:
    document = create_document(
        filename="Calculator.cs",
        extension=".cs",
    )

    result = _get_suggested_filename(
        document,
    )

    assert result == "CalculatorTests.cs"


def test_go_test_filename() -> None:
    document = create_document(
        filename="calculator.go",
        extension=".go",
    )

    result = _get_suggested_filename(
        document,
    )

    assert result == "calculator_test.go"