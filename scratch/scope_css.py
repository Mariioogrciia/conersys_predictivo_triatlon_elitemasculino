import re
import os

out_dir = r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\frontend\app"

for name in ["landing", "dashboard"]:
    fpath = os.path.join(out_dir, f"{name}.css")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace body {...} with .body-wrapper {...}
    # Wait, the best is to just replace 'body {' or 'body{' with f'.{name}-page {'
    content = re.sub(r'\bbody\s*{', f'.{name}-page {{', content)
    content = re.sub(r'html,body\s*{', f'.{name}-page {{', content)
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

print("CSS bodies scoped!")
