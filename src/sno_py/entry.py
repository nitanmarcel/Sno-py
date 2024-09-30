from sno_py.snoedit import SnoEdit


async def run(path, encoding) -> None:
    editor = SnoEdit()
    await editor.create_file_buffer(path, encoding)
    try:
        await editor.run()
    except KeyboardInterrupt:
        pass
