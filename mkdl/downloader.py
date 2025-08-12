import os
import asyncio
import aiohttp
from pathlib import Path
from tqdm import tqdm

from .exceptions import MaktabDownloaderError, NotAuthenticatedError
from .logger import logInfo, logSuccess, logWarn, logError, paintGreen, paintRed, paintCyan
from .utils import sanitize_name, decode_html_entities, extract_slug, unquote

class MaktabDownloader:
    ORIGIN = "https://maktabkhooneh.org"
    FAILED_LOG_FILE = "failed_downloads.log"

    def __init__(self, cookie=None, max_concurrent=3, verbose=False):
        self.cookie = cookie or self._get_cookie_from_env()
        if self.cookie == "PUT_YOUR_COOKIE_HERE":
            raise MaktabDownloaderError("Cookie is not set. Set MK_COOKIE or MK_COOKIE_FILE environment variable.")
        self.max_concurrent = max_concurrent
        self.verbose = verbose

        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue()
        self.session = None
        self.failed_tasks = []

    def _get_cookie_from_env(self):
        cookie = os.getenv("MK_COOKIE", "").strip()
        if cookie:
            return cookie
        cookie_file = os.getenv("MK_COOKIE_FILE", "").strip()
        if cookie_file and os.path.exists(cookie_file):
            return Path(cookie_file).read_text().strip()
        return "PUT_YOUR_COOKIE_HERE"

    def _common_headers(self, referer=None):
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,fa;q=0.8",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": "Mozilla/5.0",
            "cookie": self.cookie
        }
        if referer:
            headers["referer"] = referer
        return headers

    @staticmethod
    def format_bytes(n):
        units = ['B','KB','MB','GB','TB']
        i = 0
        while n >= 1024 and i < len(units)-1:
            n /= 1024
            i += 1
        return f"{n:.1f} {units[i]}"

    def extract_video_sources(self, html):
        import re
        urls = re.findall(r'<source[^>]+src=["\']([^"\']+)["\']', html, re.I)
        urls = [decode_html_entities(unquote(u)) for u in urls if "/videos/" in u]
        return list(dict.fromkeys(urls))

    async def fetch_json(self, url, referer=None):
        headers = self._common_headers(referer)
        async with self.session.get(url, headers=headers, timeout=30) as r:
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status} for {url}")
            return await r.json()

    async def fetch_core_data(self):
        return await self.fetch_json(f"{self.ORIGIN}/api/v1/general/core-data/?profile=1")

    async def fetch_chapters(self, slug):
        return await self.fetch_json(f"{self.ORIGIN}/api/v1/courses/{slug}/chapters/")

    async def fetch_lecture_html(self, url):
        headers = self._common_headers(url)
        async with self.session.get(url, headers=headers, timeout=30) as r:
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status} for lecture page {url}")
            return await r.text()

    async def download_file(self, url, filepath, referer=None, sample_bytes=0, position=0):
        headers = self._common_headers(referer)
        if sample_bytes > 0:
            headers["range"] = f"bytes=0-{sample_bytes-1}"

        async with self.session.get(url, headers=headers) as r:
            if r.status not in (200, 206):
                raise RuntimeError(f"Download failed with status {r.status}")

            total = int(r.headers.get("content-length", 0))
            if sample_bytes > 0:
                total = min(total, sample_bytes)

            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            progress = tqdm(total=total, unit="B", unit_scale=True,
                            desc=filepath.name, position=position, leave=True)

            with open(filepath, "wb") as f:
                async for chunk in r.content.iter_chunked(1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    progress.update(len(chunk))
                    if sample_bytes > 0 and f.tell() >= sample_bytes:
                        break
            progress.close()

    async def download_worker(self, name, queue, sample_bytes=0, position=0):
        async with self.semaphore:
            while True:
                lec_url, filepath, referer, chapter_title = await queue.get()
                try:
                    if filepath.exists() and filepath.stat().st_size > 0:
                        logInfo(f"[{name}] Skipping existing file {filepath.name}")
                        queue.task_done()
                        continue

                    html = await self.fetch_lecture_html(lec_url)
                    videos = self.extract_video_sources(html)
                    if not videos:
                        logWarn(f"[{name}] No video sources found for {filepath.name}")
                        self.failed_tasks.append((lec_url, filepath, referer, chapter_title))
                        queue.task_done()
                        continue
                    best_url = videos[0]
                    logInfo(f"[{name}] Downloading {filepath.name}")
                    await self.download_file(best_url, filepath, referer, sample_bytes, position)
                    logSuccess(f"[{name}] Downloaded {filepath.name}")
                except Exception as e:
                    logError(f"[{name}] Failed {filepath.name}: {e}")
                    self.failed_tasks.append((lec_url, filepath, referer, chapter_title))
                finally:
                    queue.task_done()

    async def worker_loop(self, name, queue, sample_bytes, position):
        while True:
            await self.download_worker(name, queue, sample_bytes, position)

    def print_profile_summary(self, core):
        is_auth = core.get("auth", {}).get("details", {}).get("is_authenticated", False)
        email = core.get("auth", {}).get("details", {}).get("email", "-")
        uid = core.get("auth", {}).get("details", {}).get("user_id", "-")
        status = paintGreen("Authenticated") if is_auth else paintRed("NOT authenticated")
        print(f"🔐 Auth check: {status}")
        print(f"👤 User: {paintCyan(email)} | user_id: {paintCyan(uid)}")
        return is_auth

    async def run(self, course_url, output_dir=None, sample_bytes=0):
        slug = extract_slug(course_url, self.ORIGIN)
        display_name = sanitize_name(unquote(slug))
        out_dir = Path(output_dir) if output_dir else Path("download") / display_name
        out_dir.mkdir(parents=True, exist_ok=True)

        connector = aiohttp.TCPConnector(limit_per_host=self.max_concurrent)
        async with aiohttp.ClientSession(connector=connector) as session:
            self.session = session

            core = await self.fetch_core_data()
            if not self.print_profile_summary(core):
                raise NotAuthenticatedError("Not logged in or invalid cookie")

            chapters_data = await self.fetch_chapters(slug)
            chapters = chapters_data.get("chapters", [])

            for ch in chapters:
                ch_title = sanitize_name(ch.get("title") or ch.get("slug") or "chapter")
                units = ch.get("unit_set") or []
                chapter_dir = out_dir / ch_title
                chapter_dir.mkdir(parents=True, exist_ok=True)
                for unit in units:
                    if not unit.get("status"):
                        continue
                    if unit.get("type") != "lecture":
                        continue
                    lec_url = f"{self.ORIGIN}/course/{slug}/{ch['slug']}-ch{ch['id']}/{unit['slug']}/"
                    fname = sanitize_name(f"{unit.get('title','lecture')}.mp4")
                    fpath = chapter_dir / fname
                    await self.queue.put((lec_url, fpath, lec_url, ch_title))

            workers = [
                asyncio.create_task(
                    self.worker_loop(f"Worker-{i+1}", self.queue, sample_bytes, i)
                ) for i in range(self.max_concurrent)
            ]

            
            await self.queue.join()

            retry_count = 0
            max_retries = 3
            while self.failed_tasks and retry_count < max_retries:
                retry_count += 1
                logWarn(f"Retrying failed downloads, attempt {retry_count}/{max_retries} ...")
                for task in self.failed_tasks:
                    await self.queue.put(task)
                self.failed_tasks.clear()
                await self.queue.join()

            if self.failed_tasks:
                logError("Some files failed to download after retries. See failed_downloads.log")
                with open(self.FAILED_LOG_FILE, "w", encoding="utf-8") as f:
                    for lec_url, filepath, _, ch_title in self.failed_tasks:
                        f.write(f"{lec_url}\t{filepath}\t{ch_title}\n")

            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

        logSuccess("All done!")
