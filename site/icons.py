"""The icons the site shows beside a mark, a state or a result: Lucide icons (https://lucide.dev, ISC licence,
copyright Lucide Contributors), each drawn on a 24 by 24 grid with a 2 wide round stroke. Which state uses which icon is
STATES in rules.py; this file only holds the drawings and turns them into CSS and SVG."""
from urllib.parse import quote

LUCIDE = {
    'circle-check': '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    'info': '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    'circle-alert': '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
    'triangle-alert': '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    'toggle-left': '<rect width="20" height="12" x="2" y="6" rx="6" ry="6"/><circle cx="8" cy="12" r="2"/>',
    'mouse-pointer-click': '<path d="m9 9 5 12 1.8-5.2L21 14Z"/><path d="M7.2 2.2 8 5.1"/><path d="m5.1 8-2.9-.8"/><path d="M14 4.1 12 6"/><path d="m6 12-1.9 2"/>',
    'circle-help': '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    'eye-off': ('<path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/>'
                '<path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/>'
                '<path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/>'),
    'ban': '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
    'circle-minus': '<circle cx="12" cy="12" r="10"/><path d="M8 12h8"/>',
    'shield-alert': ('<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
                     '<path d="M12 8v4"/><path d="M12 16h.01"/>'),
    'circle-slash': '<circle cx="12" cy="12" r="10"/><line x1="9" x2="15" y1="15" y2="9"/>',
}
STROKE = 'fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'


def svg(name, colour='#000'):
    """One icon as a standalone SVG document."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" {STROKE} stroke="{colour}">'
            f'{LUCIDE[name]}</svg>')


def mask_url(name):
    """One icon as a CSS url() for a mask, so it takes the colour of the text it sits in."""
    return 'url("data:image/svg+xml,' + quote(svg(name), safe=" =:/'.,-") + '")'


def group(name, x, y, size, colour):
    """One icon placed inside another SVG (the score badges), size by size pixels at x, y."""
    return f'<g transform="translate({x} {y}) scale({size / 24:.4f})" {STROKE} stroke="{colour}">{LUCIDE[name]}</g>'
