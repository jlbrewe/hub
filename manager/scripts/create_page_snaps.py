import asyncio
import html
import os
import re
import shutil
from base64 import b64encode

from django.core.exceptions import ViewDoesNotExist
from django.urls import URLPattern, URLResolver
from django.utils.text import slugify
from pyppeteer import launch

from manager.urls import urlpatterns

# Paths to include (additional to those that are autodiscovered from root urlpatterns)
INCLUDE = [
    # Render these templates instead of testing the pages (and getting non-200 responses)
    "stencila/render?template=403.html",
    "stencila/render?template=404.html",
    "stencila/render?template=500.html",
]

# Regex, string pairs for replacing URL parameters
REPLACE = [
    (r"<slug:account>", "biotech-corp"),
    (r"<slug:team>", "first-team"),
    (r"<slug:project>", "first-project"),
]

# Regexes of paths to exclude
EXCLUDE = [
    r"^api/.+",
    r"^debug",
    r"^favicon.ico",
    r"^stencila/admin",
    # Anything which still has a URL parameter
    # in it after REPLACE is applied
    r"\?P<",
    r"<[a-z]+:[a-z]+>",
    # Social auth login pages expected to fail because
    # app tokens not available during development
    r"^me/[a-z]+/login/",
    # These pages are not expected to return 200 responses
    r"^stencila/test/403",
    r"^stencila/test/404",
    r"^stencila/test/500",
]

# Username / password to login as
# Should have OWNER access to the accounts / projects
# specified in REPLACE
USER_PASS = "owner:owner"

# Paths to visit as an anonymous user
ANON = ["me/signin/", "me/signup/"]

# Viewport sizes to take screenshots at
VIEWPORTS = [
    # Mobile
    (360, 640),
    # Desktop
    (1920, 1080),
]


def showPath(path):
    return "index" if (path == "" or path == "/") else path


def run(*args):
    """Create screenshots of pages."""
    asyncio.get_event_loop().run_until_complete(main())


async def main():
    """Take screenshots of each path."""
    shutil.rmtree("snaps")
    os.mkdir("snaps")

    paths = [
        path for (_, path, _) in extract_views_from_urlpatterns(urlpatterns)
    ] + INCLUDE

    for (regex, string) in REPLACE:
        paths = [re.sub(regex, string, path) for path in paths]

    paths = sorted(set(paths))

    results = []
    browser = await launch()

    for idx, path in enumerate(paths):
        ok = True
        for regex in EXCLUDE:
            if re.search(regex, path):
                ok = False
                break
        if ok:
            page = await browser.newPage()

            if path not in ANON:
                header = "Basic " + b64encode(USER_PASS.encode()).decode()
                await page.setExtraHTTPHeaders({"Authorization": header})

            url = "http://localhost:8000/{}".format(path)

            print("{0}/{1} Snapping: {2}".format(idx, len(paths), showPath(path)))
            response = await page.goto(url)
            files = await snap(page, path, debug=response.status != 200)

            results.append([path, url, response.status, files])
        else:
            print("{0}/{1} Skipping: {2}".format(idx, len(paths), showPath(path)))

    await browser.close()

    report(results)


def report(results):
    """Create a HTML report."""
    report = """
    <style>
        body {
            font-family: Consolas, monospace;
            padding: 25px;
        }
        table {
            border-collapse: collapse;
        }
        table, th, td {
            border: 1px solid #eee;
        }
        td {
            padding: 1em;
        }
        img {
            max-width: 500px;
            max-height: 400px;
            margin: 50px;
            box-shadow:
                0 0.7px 2.2px rgba(0, 0, 0, 0.02),
                0 1.6px 5.3px rgba(0, 0, 0, 0.028),
                0 3px 10px rgba(0, 0, 0, 0.035),
                0 5.4px 17.9px rgba(0, 0, 0, 0.042),
                0 10px 33.4px rgba(0, 0, 0, 0.05),
                0 24px 80px rgba(0, 0, 0, 0.07);
        }
    </style>
    <table>"""
    for (path, url, status, files) in results:
        report += """
            <tr>
                <td><a href="{url}" target="_blank">{path}</a></td>
                <td>{status}</td>
                {images}
            </tr>
        """.format(
            url=url,
            path=html.escape(showPath(path)),
            status=status,
            images="".join(
                [
                    '<td><a href="{0}" target="_blank"><img src="{0}" loading="lazy"></td>'.format(
                        file
                    )
                    for file in files
                ]
            ),
        )
    with open("snaps/index.html", "w") as file:
        file.write(report)


async def snap(page, path, debug=False):
    """Take screenshots of a page at various sizes."""
    # Hide debug toolbar
    if not debug:
        await page.addStyleTag({"content": "#djDebug { display: none !important; }"})

    files = []
    for (width, height) in VIEWPORTS:
        file = (
            slugify("{}-{}x{}".format(showPath(path).replace("/", "-"), width, height))
            + ".png"
        )
        await page.setViewport(dict(width=width, height=height, deviceScaleFactor=1,))
        await page.screenshot({"path": os.path.join("snaps", file)})
        files.append(file)

    return files


def extract_views_from_urlpatterns(urlpatterns, base="", namespace=None):
    """
    Return a list of views from a list of urlpatterns.

    Each object in the returned list is a three-tuple:
    (view_func, regex, name).

    This function was extracted from:
    https://github.com/django-extensions/django-extensions/blob/master/django_extensions/management/commands/show_urls.py
    """
    views = []
    for p in urlpatterns:
        if isinstance(p, URLPattern):
            try:
                if not p.name:
                    name = p.name
                elif namespace:
                    name = "{0}:{1}".format(namespace, p.name)
                else:
                    name = p.name
                pattern = str(p.pattern)
                views.append((p.callback, base + pattern, name))
            except ViewDoesNotExist:
                continue
        elif isinstance(p, URLResolver):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            if namespace and p.namespace:
                _namespace = "{0}:{1}".format(namespace, p.namespace)
            else:
                _namespace = p.namespace or namespace
            pattern = str(p.pattern)
            views.extend(
                extract_views_from_urlpatterns(
                    patterns, base + pattern, namespace=_namespace
                )
            )
        elif hasattr(p, "_get_callback"):
            try:
                views.append((p._get_callback(), base + str(p.pattern), p.name))
            except ViewDoesNotExist:
                continue
        elif hasattr(p, "url_patterns") or hasattr(p, "_get_url_patterns"):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            views.extend(
                extract_views_from_urlpatterns(
                    patterns, base + str(p.pattern), namespace=namespace
                )
            )
        else:
            raise TypeError("%s does not appear to be a urlpattern object" % p)
    return views
