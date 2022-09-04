from alto.utils.io_utils import get_workflow_imports


def test_imports(tmp_path):
    test_wdl = str(tmp_path / "test.wdl")
    with open(test_wdl, "wt") as f:
        f.write("version 1.0\n")

        f.write('import "https://raw.githubusercontent.com/foo.wdl" as utils\n')
        f.write('import "local.wdl"\n')
    workflow_imports = get_workflow_imports(test_wdl)
    assert len(workflow_imports) == 2
    assert workflow_imports[0] == "https://raw.githubusercontent.com/foo.wdl"
    assert workflow_imports[1] == "local.wdl"
