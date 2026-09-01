from __future__ import annotations

import re
from urllib.parse import urljoin

import markdown
from bs4 import BeautifulSoup, NavigableString


MARKDOWN_EXTENSIONS = [
    "extra",
    "sane_lists",
    "tables",
    "footnotes",
]


def markdown_to_html(markdown_text: str, base_url: str) -> str:
    """Render a Markdown fragment and normalise links and action checkboxes."""
    # DirectorHelp source uses one leading box per line. Standard Markdown treats
    # adjacent plain lines as one paragraph, so make the list structure explicit
    # before rendering rather than trying to recover it from the resulting prose.
    markdown_text = re.sub(r"(?m)^(\s*)☐\s+", r"\1- ☐ ", markdown_text)
    html = markdown.markdown(
        markdown_text,
        extensions=MARKDOWN_EXTENSIONS,
        output_format="xhtml",
    )
    soup = BeautifulSoup(html, "html.parser")

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith("/"):
            anchor["href"] = urljoin(base_url, href.lstrip("/"))
        if anchor["href"].startswith(("http://", "https://")):
            anchor["rel"] = "noopener"

    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        if not heading.get("id"):
            slug = re.sub(r"[^a-z0-9]+", "-", heading.get_text(" ", strip=True).lower()).strip("-")
            heading["id"] = slug or "section"

    for item in soup.find_all(["p", "li"]):
        text = item.get_text("", strip=False)
        if not text.lstrip().startswith("☐"):
            continue
        item["class"] = list(item.get("class", [])) + ["action-item"]
        if item.name == "li" and item.parent is not None:
            parent_classes = list(item.parent.get("class", []))
            if "checklist" not in parent_classes:
                parent_classes.append("checklist")
            item.parent["class"] = parent_classes
        for child in item.contents:
            if isinstance(child, NavigableString) and "☐" in child:
                before, after = str(child).split("☐", 1)
                replacement = []
                if before:
                    replacement.append(NavigableString(before))
                checkbox = soup.new_tag("span")
                checkbox["class"] = "checkbox"
                checkbox["aria-hidden"] = "true"
                replacement.append(checkbox)
                replacement.append(NavigableString(after.lstrip()))
                child.replace_with(*replacement)
                break

    return "".join(str(child) for child in soup.contents)
