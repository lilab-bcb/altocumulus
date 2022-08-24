import json

from alto.commands import upload


def test_upload_directory(tmp_path):
    output_json = str(tmp_path / "test.json")
    upload.main(["-b", "gs://foo", "--dry-run", "-o", output_json, "alto/tests/test.json"])
    with open(output_json, "r") as f:
        reformatted_input = json.load(f)
    assert reformatted_input["foo"] == "gs://foo/test_sample"
