import re
from urllib.parse import urlparse, unquote

def sanitize_name(name):
    return re.sub(r'[\/:*?"<>|]', ' ', name).strip()[:150]

def decode_html_entities(text):
    if not text:
        return text
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#39;|&apos;', "'", text)
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    text = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), text)
    return text

def extract_slug(course_url, expected_origin="https://maktabkhooneh.org"):
    u = urlparse(course_url)
    if u.netloc != urlparse(expected_origin).netloc:
        raise ValueError("Unexpected origin")
    parts = [p for p in u.path.split("/") if p]
    if "course" not in parts:
        raise ValueError("No course in URL")
    idx = parts.index("course")
    return parts[idx+1]
