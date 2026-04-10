from scripts.trigger_repos import _repo_branch, _repo_name


def test_repo_name_supports_string_and_object():
    assert _repo_name('matrix-hub') == 'matrix-hub'
    assert _repo_name({'name': 'matrix-ai'}) == 'matrix-ai'


def test_repo_branch_falls_back_to_default():
    assert _repo_branch('matrix-hub', 'main') == 'main'
    assert _repo_branch({'name': 'matrix-ai', 'branch': 'develop'}, 'main') == 'develop'
