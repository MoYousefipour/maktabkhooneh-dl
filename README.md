# maktabkhooneh-dl
Download Videos from Maktabkhoone that you have access to them.



# Things You need
- Installing `requirments` from `requirments.txt`.
- find your `sessionid` from `maktabkhoone` as you authenticated and store it as enviromment variable with `export` command.
- Find `slug` name of your course that have accessed.
- Make `main.py` file like the example and run the `main.py`.


```python

import asyncio
from mkdl import MaktabDownloader

async def main():
    downloader = MaktabDownloader(max_concurrent=4)
    l=['slug1','slug2']
    for item in l:
        await downloader.run(f"https://maktabkhooneh.org/course/{item}/")

if __name__ == "__main__":
    asyncio.run(main())


```