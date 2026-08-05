"""Generate compact pill/chip badges with reliable embedded logos.

Shields.io no longer embeds several brand logos (LinkedIn, Oracle, Power BI,
Tableau). This script fetches Simple Icons when available and falls back to
hand-authored SVG paths so every badge used in the README has a visible icon.
"""

from __future__ import annotations

import base64
import os
import re
import ssl
import urllib.request

from design_tokens import layout, token

ssl._create_default_https_context = ssl._create_unverified_context

SURFACE = token("pill_surface")
LOGO_COLOR = token("accent")
TEXT_COLOR = token("on_surface_bright")
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif"

# Hand-authored Simple Icons-compatible paths (viewBox 0 0 24 24) for logos
# that fail CDN/Shields lookups.
FALLBACK_PATHS = {
    "linkedin": (
        "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 "
        "0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 "
        "1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 "
        "7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 "
        "2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 "
        "2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 "
        "0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 "
        "24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 "
        "22.222 0h.003z"
    ),
    "oracle": (
        "M16.412 4.412h-8.82a7.588 7.588 0 0 0-.008 15.176h8.828a7.588 "
        "7.588 0 0 0 0-15.176zm-.193 12.502H7.786a4.915 4.915 0 0 1 "
        "0-9.828h8.433a4.914 4.914 0 1 1 0 9.828z"
    ),
    "powerbi": (
        "M10.54 0h2.92v24h-2.92zm-5.46 6.55h2.92V24H5.08zM0 12.36h2.92V24H0zm"
        "16.36-6.55h2.92V24h-2.92zm5.46 3.27H24V24h-2.18z"
    ),
    "tableau": (
        "M11.39 0v2.92h-2.9v1.95h2.9v2.91h1.96V4.87h2.9V2.92h-2.9V0zm-7.1 "
        "4.87v2.91H1.37v1.96h2.92v2.91h1.95V9.74h2.91V7.78H6.24V4.87zm14.22 "
        "0v2.91h-2.92v1.96h2.92v2.91h1.95V9.74H24V7.78h-2.91V4.87zm-7.12 "
        "4.88v2.91h-2.9v1.95h2.9v2.92h1.96v-2.92h2.9v-1.95h-2.9V9.75zm-7.1 "
        "4.87v2.91H1.37v1.96h2.92V24h1.95v-2.91h2.91v-1.96H6.24v-2.91zm14.22 "
        "0V24h1.95v-2.91H24v-1.96h-2.91v-2.91z"
    ),
    "sql": (
        "M12 3c4.97 0 9 1.57 9 3.5v11c0 1.93-4.03 3.5-9 3.5s-9-1.57-9-3.5v-11C3 "
        "4.57 7.03 3 12 3zm0 2c-3.79 0-6.12.87-6.83 1.5C5.88 7.13 8.21 8 12 "
        "8s6.12-.87 6.83-1.5C18.12 5.87 15.79 5 12 5zM5 9.25v3.25c.62.66 3.02 "
        "1.5 7 1.5s6.38-.84 7-1.5V9.25C17.4 9.73 15.02 10 12 10s-5.4-.27-7-"
        ".75zm0 6v2.25c.62.66 3.02 1.5 7 1.5s6.38-.84 7-1.5v-2.25c-1.6.48-"
        "3.98.75-7 .75s-5.4-.27-7-.75z"
    ),
    "windows": (
        "M0 3.449L9.75 2.1v9.451H0zm10.949-1.508L24 0v11.4H10.949zM0 12.6h9.75"
        "v9.451L0 20.699zM10.949 12.6H24V24l-12.9-1.801z"
    ),
}

SOCIAL_BADGES = {
    "portfolio": ("Portfolio", "vercel"),
    "email": ("Email", "gmail"),
    "linkedin": ("LinkedIn", "linkedin"),
    "github": ("GitHub", "github"),
    "leetcode": ("LeetCode", "leetcode"),
    "npm": ("NPM", "npm"),
    "sponsors": ("Sponsors", "githubsponsors"),
}

TECH_BADGES = {
    "javascript": ("JavaScript", "javascript"),
    "typescript": ("TypeScript", "typescript"),
    "python": ("Python", "python"),
    "java": ("Java", "openjdk"),
    "react": ("React", "react"),
    "nextjs": ("Next.js", "nextdotjs"),
    "tailwind": ("Tailwind CSS", "tailwindcss"),
    "html": ("HTML5", "html5"),
    "css": ("CSS3", "css3"),
    "bootstrap": ("Bootstrap", "bootstrap"),
    "nodejs": ("Node.js", "nodedotjs"),
    "express": ("Express", "express"),
    "postgresql": ("PostgreSQL", "postgresql"),
    "mongodb": ("MongoDB", "mongodb"),
    "mysql": ("MySQL", "mysql"),
    "redis": ("Redis", "redis"),
    "prisma": ("Prisma", "prisma"),
    "docker": ("Docker", "docker"),
    "aws": ("AWS", "amazonaws"),
    "githubactions": ("GitHub Actions", "githubactions"),
    "linux": ("Linux", "linux"),
    "nginx": ("Nginx", "nginx"),
    "openai": ("OpenAI", "openai"),
    "gemini": ("Google Gemini", "googlegemini"),
    "git": ("Git", "git"),
    "postman": ("Postman", "postman"),
    "vscode": ("VS Code", "visualstudiocode"),
    "fastify": ("Fastify", "fastify"),
    "kotlin": ("Kotlin", "kotlin"),
}

META_BADGES = {
    "company": ("COMPANY", "CodeMyFYP"),
    "role": ("ROLE", "Software Engineer & Founder"),
    "focus": ("FOCUS", "AI & Full Stack"),
}


def _path_to_data_uri(path_d: str, fill: str) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{fill}">'
        f'<path d="{path_d}"/></svg>'
    )
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def _colorize_svg(svg: str, fill: str) -> str:
    svg = re.sub(r'\sfill="[^"]*"', "", svg)
    svg = svg.replace("<svg", f'<svg fill="{fill}"', 1)
    return svg


def _fetch_simple_icon(slug: str) -> str | None:
    urls = [
        f"https://cdn.jsdelivr.net/npm/simple-icons@v13/icons/{slug}.svg",
        f"https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/{slug}.svg",
        f"https://cdn.simpleicons.org/{slug}/{token_param_safe()}",
    ]
    for url in urls:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                raw = response.read().decode()
            if "<svg" not in raw:
                continue
            colored = _colorize_svg(raw, LOGO_COLOR)
            b64 = base64.b64encode(colored.encode()).decode()
            return f"data:image/svg+xml;base64,{b64}"
        except Exception:
            continue
    return None


def token_param_safe() -> str:
    return LOGO_COLOR.lstrip("#")


def resolve_logo(slug: str | None) -> str | None:
    if not slug:
        return None
    if slug in FALLBACK_PATHS:
        # Prefer CDN, but always have a working fallback.
        href = _fetch_simple_icon(slug)
        if href:
            return href
        return _path_to_data_uri(FALLBACK_PATHS[slug], LOGO_COLOR)
    return _fetch_simple_icon(slug) or (
        _path_to_data_uri(FALLBACK_PATHS[slug], LOGO_COLOR)
        if slug in FALLBACK_PATHS
        else None
    )


def _text_width(label: str, font_size: int) -> int:
    return int(len(label) * font_size * 0.58) + 8


def pill_badge(label: str, logo_href: str | None, *, chip: bool = False) -> str:
    height = layout("chip_height") if chip else layout("pill_height")
    radius = height // 2
    font_size = 11 if chip else 12
    icon_size = 14 if chip else 16
    icon_x = 10 if chip else 12
    text_x = (icon_x + icon_size + 6) if logo_href else 14
    text_width = _text_width(label, font_size)
    width = text_x + text_width + 12

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{label}">',
        f"<title>{label}</title>",
        f'<rect width="{width}" height="{height}" rx="{radius}" fill="{SURFACE}"/>',
    ]
    if logo_href:
        icon_y = (height - icon_size) / 2
        parts.append(
            f'<image x="{icon_x}" y="{icon_y}" width="{icon_size}" height="{icon_size}" '
            f'href="{logo_href}"/>'
        )
    parts.append(
        f'<text x="{text_x}" y="50%" dy="0.35em" fill="{TEXT_COLOR}" '
        f'font-family="{FONT}" font-size="{font_size}" font-weight="600">{label}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def meta_badge(key: str, value: str) -> str:
    """Two-tone meta chip (COMPANY / ROLE / FOCUS)."""
    height = 28
    key_w = _text_width(key, 11) + 20
    value_w = _text_width(value, 11) + 20
    width = key_w + value_w
    safe_key = _xml_escape(key)
    safe_value = _xml_escape(value)
    label = f"{safe_key}: {safe_value}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{label}">'
        f"<title>{label}</title>"
        f'<rect width="{width}" height="{height}" rx="14" fill="{SURFACE}"/>'
        f'<rect x="0" y="0" width="{key_w}" height="{height}" rx="14" fill="#161D2B"/>'
        f'<rect x="{key_w - 14}" y="0" width="14" height="{height}" fill="#161D2B"/>'
        f'<text x="{key_w / 2:.0f}" y="50%" dy="0.35em" text-anchor="middle" '
        f'fill="{token("on_surface_variant")}" font-family="{FONT}" font-size="11" '
        f'font-weight="600" letter-spacing="0.5">{safe_key}</text>'
        f'<text x="{key_w + value_w / 2:.0f}" y="50%" dy="0.35em" text-anchor="middle" '
        f'fill="{token("primary")}" font-family="{FONT}" font-size="11" '
        f'font-weight="700">{safe_value}</text>'
        f"</svg>"
    )


def generate_badges(badge_map: dict, *, chip: bool = False) -> None:
    os.makedirs("assets/badges", exist_ok=True)
    for name, (label, slug) in badge_map.items():
        print(f"Generating {'chip' if chip else 'pill'} {name}...")
        href = resolve_logo(slug)
        if href is None and slug:
            print(f"  WARNING: no logo for {slug}; text-only badge")
        svg = pill_badge(label, href, chip=chip)
        with open(f"assets/badges/badge-{name}.svg", "w", encoding="utf-8") as f:
            f.write(svg)


def generate_meta() -> None:
    os.makedirs("assets/badges", exist_ok=True)
    for name, (key, value) in META_BADGES.items():
        print(f"Generating meta {name}...")
        with open(f"assets/badges/badge-{name}.svg", "w", encoding="utf-8") as f:
            f.write(meta_badge(key, value))


if __name__ == "__main__":
    generate_badges(SOCIAL_BADGES, chip=False)
    generate_badges(TECH_BADGES, chip=True)
    generate_meta()
    # Validate critical icons
    critical = ["linkedin", "github", "portfolio", "email", "python", "typescript", "react", "nextjs"]
    for name in critical:
        path = f"assets/badges/badge-{name}.svg"
        with open(path, encoding="utf-8") as f:
            content = f.read()
        ok = "<image" in content or name in META_BADGES
        print(f"validate {name}: {'OK' if ok else 'BROKEN'}")
# Commit 5: Standardize font metrics
# Commit 6: SQL fallback path
