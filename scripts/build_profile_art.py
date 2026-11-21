"""Build original responsive SVG panels for the profile, without external assets."""
from html import escape

from art import ACCENT, ASSETS, BG, FG, MUTED

FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
MONO = "ui-monospace,Consolas,monospace"


def text(x, y, value, size=28, fill=FG, bold=False, mono=False):
    return (f'<text x="{x}" y="{y}" font-family="{MONO if mono else FONT}" font-size="{size}" '
            f'font-weight="{700 if bold else 400}" fill="{fill}">{escape(value)}</text>')


def panel(width, height, title, content):
    return '\n'.join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        f'<title>{escape(title)}</title>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="20" fill="{BG}" stroke="#40364f" stroke-width="2"/>',
        *content,
        '</svg>',
    ]) + '\n'


def pixel_flower(x, y, scale=1):
    # A small geometric signature built from square pixels, independent of any logo.
    positions = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 3), (3, 2)]
    return ''.join(f'<rect x="{x+a*10*scale}" y="{y+b*10*scale}" width="{7*scale}" height="{7*scale}" fill="{ACCENT}" opacity="{1 if a==b else .55}"/>' for a,b in positions)


def about(mobile=False):
    width, height = (680, 760) if mobile else (1280, 390)
    items = [text(38, 55, 'A LITTLE ABOUT MY WORLD', 19, ACCENT, mono=True),
             pixel_flower(width-82, 28)]
    items += [text(38, 130, 'Curious by nature.', 56, bold=True),
              text(38, 195, 'A builder by practice.', 56, bold=True)]
    lines = ['I like thoughtful interfaces, interesting problems,',
             'and the moment an idea becomes something useful.']
    if mobile:
        lines = ['I like thoughtful interfaces, interesting', 'problems, and the moment an idea', 'becomes something useful.']
    for i, line in enumerate(lines):
        items.append(text(40, 253+i*39, line, 30 if mobile else 26, MUTED))
    if mobile:
        x, y = 40, 421
        items.append('<path d="M40 377H640" stroke="#40364f"/>')
    else:
        x, y = 820, 71
        items.append('<path d="M772 40V350" stroke="#40364f"/>')
    blocks = [
        ('BASED IN', ['Bengaluru, India']),
        ('STUDYING', ['B.Tech Computer Science', 'PW Institute of Innovation', 'Medhavi Skills University']),
        ('OPEN TO', ['Internships & hackathon teams']),
    ]
    for label, lines in blocks:
        items.append(text(x, y, label, 17, ACCENT, mono=True))
        y += 34
        for line in lines:
            items.append(text(x, y, line, 30 if mobile else 24))
            y += 30
        y += 25
    return panel(width, height, 'About Lakshmi Hasini: CS student, builder, and frontend developer in Bengaluru', items)


def toolkit(mobile=False):
    width, height = (680, 950) if mobile else (1280, 410)
    items = [text(38, 53, 'A FEW THINGS IN MY WORKING SET', 19, ACCENT, mono=True)]
    groups = [
        ('Interfaces', ['React · TypeScript', 'JavaScript · HTML · CSS', 'Tailwind CSS · Vite']),
        ('Behind the scenes', ['Node.js · Express', 'MongoDB · MySQL', 'Python · Supabase']),
        ('Core skills', ['C · C++ · Java', 'Data structures · Algorithms', 'Operating systems · Git']),
    ]
    for i, (title, lines) in enumerate(groups):
        x = 40 if mobile else 40+i*412
        y = 118+i*242 if mobile else 122
        items.append(text(x, y, title, 34, bold=True))
        items.append(f'<path d="M{x} {y+20}H{x+(590 if mobile else 365)}" stroke="#40364f"/>')
        for j, line in enumerate(lines):
            items.append(text(x, y+63+j*43, line, 32 if mobile else 26, MUTED))
    y = 861 if mobile else 354
    items.append(f'<rect x="25" y="{y-31}" width="{width-50}" height="{90 if mobile else 62}" rx="12" fill="#241d32"/>')
    if mobile:
        items += [text(43, y, 'EXPLORING THROUGH PROJECTS', 17, ACCENT, mono=True),
                  text(43, y+40, 'AI agents · AWS · Web3 · Algorand', 30)]
    else:
        items += [text(43, y+7, 'EXPLORING', 17, ACCENT, mono=True),
                  text(195, y+7, 'AI agents · AWS · Web3 · Algorand', 26)]
    return panel(width, height, 'Skills: frontend, backend, programming fundamentals, and project explorations', items)


def main():
    ASSETS.mkdir(exist_ok=True)
    for name, builder in [('about', about), ('toolkit', toolkit)]:
        for mobile in [False, True]:
            suffix = '-mobile' if mobile else ''
            (ASSETS / f'{name}{suffix}.svg').write_text(builder(mobile))
    print('Built original introduction and toolkit panels for desktop and mobile.')


if __name__ == '__main__':
    main()
