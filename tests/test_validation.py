import pytest
from claude_github_assistant.git_service import _ref
from claude_github_assistant.github_service import _branch, _page

@pytest.mark.parametrize("value",["main","feature/fix","release/3.6.1"])
def test_valid_refs(value): _ref(value)

@pytest.mark.parametrize("value",["-c","../main","bad ref","main..x","x:y"])
def test_invalid_refs(value):
    with pytest.raises(ValueError): _ref(value)

def test_branch_validation():
    _branch("feature/dependency-fix")
    with pytest.raises(ValueError): _branch("-f")

@pytest.mark.parametrize("n",[1,20,100])
def test_valid_page_size(n): _page(n)

@pytest.mark.parametrize("n",[0,101])
def test_invalid_page_size(n):
    with pytest.raises(ValueError): _page(n)
