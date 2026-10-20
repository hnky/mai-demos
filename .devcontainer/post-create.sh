#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Keep Linux dependencies separate from a mounted checkout's local .venv.
venv_dir="${HOME}/.venvs/mai-demos"
if [[ ! -x "${venv_dir}/bin/python" ]]; then
    python3 -m venv "${venv_dir}"
fi

"${venv_dir}/bin/python" -m pip install -r MAI-Transcribe-2/requirements.txt
"${venv_dir}/bin/python" -m ipykernel install --user \
    --name mai-demos --display-name "Python (MAI demos)"
mkdir -p MAI-Transcribe-2/samples
