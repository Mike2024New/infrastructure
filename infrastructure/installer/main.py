from infrastructure.builder.main import build, BuildParameters
from pathlib import Path

ROOT_DIR = Path.cwd()

build_parameters = BuildParameters(
    entry_point_path=Path('script.py'),
    name='installer',
    one_file=True,
    create_resources_symlink=False,
    clear_old_distributive=True,
)
build(parameters=build_parameters)
