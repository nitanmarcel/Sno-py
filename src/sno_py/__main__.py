import argparse
import asyncio
import sys

import uvloop

from sno_py.entry import run


async def main(file, encoding) -> None:
    await run(file, encoding)


def entry() -> None:
    parser = argparse.ArgumentParser(description="My personal vi-like text editor.")
    parser.add_argument("file", help="Path to the input file")
    parser.add_argument("-e", "--encoding", help="Set encoding")

    args = parser.parse_args()
    if sys.version_info >= (3, 11):
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(main(args.file, args.encoding))
    else:
        uvloop.install()
        asyncio.run(main(args.file, args.encoding))


if __name__ == "__main__":
    entry()
