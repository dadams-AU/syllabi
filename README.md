# Adams Syllabi Collection

A curated set of LaTeX-formatted syllabi for undergraduate and graduate courses in Public Administration and Public Policy at [Cal State Fullerton](https://fullerton.edu). The repository also ships with **CSUF-compliant, accessibility-ready LaTeX syllabus templates**.

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

## 🔗 Quick Links

- 🌐 **Browse syllabi on the web:** https://syllabi.dadams.io  
- 💻 **This repository:** https://github.com/dadams-AU/syllabi  
- 🧰 **Template (bundled here):** `template/`  
- 🔁 **Upstream template source:** https://github.com/CSUF-MPA/csuf-syllabus (reference)

---

## 📚 Available Syllabi

### 🎓 Undergraduate
- [**POSC 315** · Introduction to Public Policy](https://github.com/dadams-AU/syllabi/tree/main/POSC%20315%20Intro%20Policy)
- [**POSC/CRJU 320** · Introduction to Public Administration](https://github.com/dadams-AU/syllabi/tree/main/CRJU_POSC%20320%20Intro%20PA)

### 🎓 Graduate (MPA)
- [**POSC 509** · Foundations of Public Administration](https://github.com/dadams-AU/syllabi/tree/main/POSC%20509%20MPA%20Foundations)
- [**POSC 521** · Public Administration Theory (MPA Capstone)](https://github.com/dadams-AU/syllabi/tree/main/POSC%20521%20MPA%20Capstone)
- [**POSC 588** · Collaborative Governance](https://github.com/dadams-AU/syllabi/tree/main/POSC%20588%20Collab%20Gov)

---

## ♿ Accessibility (2025 Update)

The template in `template/` is configured for **PDF/UA** accessibility and CSUF compliance:

- **Tagged PDFs** via `tagpdf` and `pdfmanagement-testphase` (compile with **LuaLaTeX**)
- **Semantic structure** using `scrartcl` (KOMA-Script)
- **Accessible sans-serif fonts** (default Roboto; options include Noto Sans, Inter)
- **Proper headings, captions, alt text, and document metadata**
- **High contrast** with no reliance on color alone
- **Logical reading order** for assistive technologies

These practices align with Section 508 and university accessibility standards.

---

## 🗂️ Repository Structure

```
.
├── CNAME
├── LICENSE
├── Images/
├── README.md
├── syllabi.code-workspace
├── template/
│   ├── csuf_template/         # Full, ready-to-use accessible syllabus
│   └── csuf_template_shell/   # Minimal shell for rapid customization
├── CRJU_POSC 320 Intro PA/
├── POSC 315 Intro Policy/
├── POSC 428/
├── POSC 509 MPA Foundations/
├── POSC 521 MPA Capstone/
└── POSC 588 Collab Gov/
````

---

## 🚀 Quick Start

### Option A — Overleaf (fastest)
1. Zip and upload `template/csuf_template/` to Overleaf **or** import from GitHub.
2. In Overleaf: **Menu → Compiler → LuaLaTeX**.
3. Open `csuf_template.tex` and click **Recompile** (first build may take ~3–15s).
4. Edit the course/instructor blocks and export the tagged PDF.

### Option B — Local LaTeX (advanced)
```bash
# Clone this syllabi repo or pull just the template directory
git clone https://github.com/dadams-AU/syllabi.git
cd syllabi/template/csuf_template
lualatex csuf_template.tex
````

**Requirements**

* **LuaLaTeX** (XeLaTeX/PDFLaTeX won’t produce proper tagging)
* TeX distribution: TeX Live 2023+, MacTeX, or MiKTeX
* Packages: `tagpdf`, `pdfmanagement-testphase`, `fontspec`, `tex-gyre`
* `csuf_logo.png` present in the template directory

**Install hints**

* TeX Live:

  ```bash
  tlmgr update --self --all
  tlmgr install tagpdf tex-gyre tex-gyre-math fontspec
  ```
* Ubuntu/Debian:

  ```bash
  sudo apt install texlive-luatex texlive-latex-extra fonts-texgyre
  ```
* Arch/Manjaro:

  ```bash
  sudo pacman -S texlive-latexextra texlive-fontsextra
  ```
* macOS (MacTeX): use TeX Live Utility to add `tagpdf` and `tex-gyre`.

**Sanity checks**

```bash
kpsewhich tagpdf-base.sty
kpsewhich texgyretermes-regular.otf
```

---

## 🧩 Using This Repo

### Browse or copy an existing syllabus

Each course folder includes:

* `syllabus.tex` — LaTeX source
* `syllabus.pdf` — compiled, accessible PDF

### Create a new syllabus from the template

1. Copy `template/csuf_template/` into your course folder.
2. Update the **course block**, **instructor details**, **schedule**, and **policies**.
3. Compile with **LuaLaTeX** to preserve PDF/UA tagging.
4. (Optional) Use `csuf_template_shell/` if you prefer a minimal starting point.

---

## 🧠 Troubleshooting (decision tree)

```
Build failed?
├─ Using LuaLaTeX?
│  ├─ No → Switch compiler to LuaLaTeX
│  └─ Yes → Continue
├─ On Overleaf?
│  ├─ Yes → Packages install automatically; recompile
│  └─ No  → Ensure tagpdf + tex-gyre installed locally
├─ Fonts complaint?
│  ├─ Install tex-gyre + tex-gyre-math
│  └─ Use defaults; fallbacks will render
└─ Still stuck → Try Overleaf import—fastest path to green
```

---

## 🔄 Maintenance

* Syllabi reflect current course policies and schedules.
* Template updates track accessibility best practices.
* Commit history documents changes across semesters.

---

## 📄 License

**Creative Commons BY-NC-SA 4.0**
You may share and adapt with attribution, **no commercial use**, and **share alike**.
See `LICENSE` for details.

---

## 📬 Contact

**David P. Adams, Ph.D.**

Associate Professor of Public Administration

California State University, Fullerton

📧 [dpadams@fullerton.edu](mailto:dpadams@fullerton.edu)

🌐 [https://dadams.io](https://dadams.io)

---

> Contributions: feedback and suggestions are welcome in issues; direct PRs are not currently accepted.
