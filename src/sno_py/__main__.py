import asyncio
import argparse

from sno_py.entry import run

async def main(file, encoding) -> None:
    await run(file, encoding)

def entry() -> None:
    parser = argparse.ArgumentParser(description="My personal vi-like text editor.")
    parser.add_argument('file', help="Path to the input file")
    parser.add_argument('-e', '--encoding', help="Set encoding")

    args = parser.parse_args()
    asyncio.run(main(args.file, args.encoding))

if __name__ == "__main__":
    entry()