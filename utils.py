import pathlib
from uuid import uuid4

def file_generate_name(original_file_name):
    name = pathlib.Path(original_file_name)
    extension = name.suffix
    file_name = name.stem
    return f"original/{file_name}-{uuid4().hex}{extension}"