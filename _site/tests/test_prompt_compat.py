import importlib.util
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "gitbook_compat.py"
SPEC = importlib.util.spec_from_file_location("gitbook_compat_prompt_test", HOOK)
compat = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(compat)


def test_prompt_fence_receives_a_non_empty_filename():
    source = '''{% prompt description="Check these variables" %}
```markdown
Do the work.
```
{% endprompt %}'''

    rendered = compat._PROMPT_RE.sub(compat._prompt, source)

    assert '???+ note "📝 Check these variables"' in rendered
    assert '```markdown title="Check these variables"' in rendered


def test_existing_prompt_fence_title_is_preserved():
    source = '''{% prompt description="Outer title" %}
```text title="Existing title"
Do the work.
```
{% endprompt %}'''

    rendered = compat._PROMPT_RE.sub(compat._prompt, source)

    assert rendered.count('title="Existing title"') == 1
    assert 'title="Outer title"' not in rendered
