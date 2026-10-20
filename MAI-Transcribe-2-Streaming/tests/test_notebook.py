import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "demo.ipynb"


class StreamingNotebookTests(unittest.TestCase):
    def test_notebook_is_clean_standalone_and_explicit_about_preview(self):
        notebook = nbformat.read(NOTEBOOK, as_version=4)
        nbformat.validate(notebook)
        self.assertNotIn("widgets", notebook.metadata)
        self.assertNotIn("data:audio", NOTEBOOK.read_text())
        self.assertIn("Experimental", notebook.cells[0].source)
        for cell in notebook.cells:
            self.assertFalse(cell.get("attachments"))
            if cell.cell_type == "code":
                self.assertIsNone(cell.execution_count)
                self.assertEqual(cell.outputs, [])
                compile(cell.source, str(NOTEBOOK), "exec")
                for token in ("SPEECH_KEY", "AUDIO_PATH", "baseline", "requests.post", "RUN_"):
                    self.assertNotIn(token, cell.source)
        for name in (
            "README.md", "information.md", "demo-instructions.md", ".env.example",
            "requirements.txt", "live_captions.py", "live_captions.js",
        ):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_notebook_runs_without_recordings_or_network_and_handles_rerun(self):
        notebook = copy.deepcopy(nbformat.read(NOTEBOOK, as_version=4))
        setup = nbformat.v4.new_code_cell(
            "import sys\n"
            f"sys.path.insert(0, {str(ROOT)!r})\n"
            "import live_captions\n"
            "def forbid_network(*args, **kwargs):\n"
            "    raise AssertionError('Rendering must not contact Azure')\n"
            "live_captions.NoRedirectConnect = forbid_network\n"
            "live_captions.auth_headers = forbid_network\n"
            "live_captions.AzureCliCredential = forbid_network\n"
        )
        notebook.cells.insert(0, setup)
        display_cell = next(c for c in notebook.cells if c.id == "live-captions")
        notebook.cells.append(nbformat.v4.new_code_cell(
            "assert captions._task is None\n"
            "assert captions.transcript == ''\n"
            "previous = captions\n"
        ))
        repeated = nbformat.v4.new_code_cell(display_cell.source)
        notebook.cells.append(repeated)
        notebook.cells.append(nbformat.v4.new_code_cell(
            "assert previous.comm is None\n"
            "assert captions is not previous\n"
            "assert captions._task is None\n"
            "captions.close()\n"
        ))
        with tempfile.TemporaryDirectory() as directory:
            from ipykernel.kernelspec import install
            prefix = Path(directory) / "kernel"
            install(prefix=str(prefix), kernel_name="streaming-offline-test")
            with patch.dict("os.environ", {
                "JUPYTER_PATH": str(prefix / "share" / "jupyter"),
            }):
                NotebookClient(
                    notebook, timeout=60, kernel_name="streaming-offline-test",
                    resources={"metadata": {"path": directory}},
                ).execute()


if __name__ == "__main__":
    unittest.main()
