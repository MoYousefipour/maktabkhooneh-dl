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

# How to find sessionid

To find Session id, sign in `maktabkhoone.org` then use `Inspect element -> Network` and reload your site. Click on first item that appears and under `cookie` section, you can find you `sessionid`. Copy all charecters include `sessionid=`. the set it to you system with code below.

```terminal
export MK_COOKIE="sessionid=your_session_id";
```