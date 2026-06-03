import os
import subprocess
import shutil
from typing import Optional


def convert_to_pdf(input_path: str, output_dir: str) -> Optional[str]:
    os.makedirs(output_dir, exist_ok=True)

    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".pdf":
        output_path = os.path.join(output_dir, os.path.basename(input_path))
        shutil.copy2(input_path, output_path)
        return output_path

    try:
        result = subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, input_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}.pdf")
            if os.path.exists(output_path):
                return output_path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None
