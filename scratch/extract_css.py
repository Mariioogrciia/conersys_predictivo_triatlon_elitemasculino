import re
import os

html_files = {
    "landing": r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\chatbot\templates\index.html",
    "dashboard": r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\chatbot\templates\dashboard.html"
}

out_dir = r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\frontend\app"

for name, fpath in html_files.items():
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
        styles = re.findall(r"<style>(.*?)</style>", content, re.DOTALL)
        out_path = os.path.join(out_dir, f"{name}.css")
        with open(out_path, "w", encoding="utf-8") as out:
            out.write("\n".join(styles))
        print(f"Written {out_path}")

# Empty out globals.css to just import fonts or leave it clean
with open(os.path.join(out_dir, "globals.css"), "w", encoding="utf-8") as f:
    f.write("/* Global styles handled by landing.css and dashboard.css for now */\n")
