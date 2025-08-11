# maktabkhooneh-dl

Download videos from Maktabkhooneh courses you have access to.

---

## Requirements

- Python 3.10 or higher
- Install dependencies using:

```bash
  pip install -r requirements.txt
```
- Obtain your `sessionid` cookie after logging into `Maktabkhooneh`.

- Find the course `slug` you want to download.

- Create and run a `main.py` script as shown below.

## Usage Example

- Create a `main.py` file with the following content:

```python
import asyncio
from mkdl import MaktabDownloader

async def main():
    downloader = MaktabDownloader(max_concurrent=4)
    course_slugs = ['slug1', 'slug2']
    for slug in course_slugs:
        await downloader.run(f"https://maktabkhooneh.org/course/{slug}/")

if __name__ == "__main__":
    asyncio.run(main())
```

- Run the script:

```bash
python main.py
```

## How to Find Your `sessionid`

1. Log in to `maktabkhooneh.org`.
2. Open `Developer Tools` in your browser (F12 or right-click -> Inspect)
3. Navigate to the `Network` tab and reload the page.
4. Click the `first request` in the list.
5. Find the `Cookie` section under the `request headers`.
6. Copy the `sessionid=...` value.
7. Set it as an `environment variable`:
```bash
export MK_COOKIE="sessionid=your_session_id"
```

For Windows PowerShell:

```powershell
setx MK_COOKIE "sessionid=your_session_id"
```

| Parameter        | Type    | Default | Description                                            |
| ---------------- | ------- | ------- | ------------------------------------------------------ |
| `max_concurrent` | Integer | 4       | Maximum number of concurrent downloads allowed.        |
| `sample_bytes`   | Integer | 0       | If >0, downloads only the first N bytes (for testing). |


## Notes and Tips

- Ensure your `sessionid` cookie is valid and not expired.
- Adjust `max_concurrent` based on your internet speed and system capability.
- Downloads are saved to `download/<course_slug>/` folder.
- Only download courses you have access to.
- Use `Ctrl+C` to gracefully stop the downloader.

## FAQ

Q: I get "Cookie is not set" error. What should I do?
A: Make sure you have set the MK_COOKIE environment variable correctly before running the script.

Q: Can I download multiple courses at once?
A: Yes, just add their slugs to the course_slugs list.

Q: Is this safe?
A: The tool uses your session cookie and only accesses content you have permission to view. Do not share your cookie with others.

## License
This project is licensed under the MIT License.

## Contact
For issues or feature requests, please open an issue on the repository or contact the maintainer.