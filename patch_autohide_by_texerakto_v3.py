from pathlib import Path
import re
import sys

ROOT = Path("/workspaces/iceraven-browser")
if not ROOT.exists():
    ROOT = Path.cwd()

BASE = ROOT / "app/src/main/java/org/mozilla/fenix/browser/BaseBrowserFragment.kt"

START = "/////////////// Texerakto REPO /////////////////////START////////"
END = "/////////////// Texerakto REPO /////////////////////END///////////"

if not BASE.exists():
    print(f"No encuentro {BASE}")
    sys.exit(1)

text = BASE.read_text(encoding="utf-8")

def add_import_if_missing(text: str, import_line: str) -> str:
    if import_line in text:
        return text
    m = re.search(r"^(package [^\n]+\n)", text, flags=re.MULTILINE)
    if not m:
        raise RuntimeError("No encontré package")
    return text[:m.end()] + import_line + "\n" + text[m.end():]

def replace_once(text: str, pattern: str, replacement: str, desc: str) -> str:
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise RuntimeError(f"No pude aplicar: {desc}")
    return new_text

def insert_before_once(text: str, needle: str, insertion: str, desc: str) -> str:
    idx = text.find(needle)
    if idx == -1:
        raise RuntimeError(f"No pude aplicar: {desc}")
    return text[:idx] + insertion + text[idx:]

text = add_import_if_missing(text, "import kotlinx.coroutines.Job")
text = add_import_if_missing(text, "import kotlinx.coroutines.delay")

if "private var globalAutoHideJob: Job? = null" not in text:
    text = replace_once(
        text,
        r"(protected val hideToolbarFeature = ViewBoundFeatureWrapper<WebAppHideToolbarFeature>\(\)\s*\n)",
        r"\1"
        + f"""
    {START}
    private var globalAutoHideJob: Job? = null
    private var globalToolbarHidden = false
    {END}
""",
        "insertar propiedades de autohide"
    )

if "internal fun onUserInteractionForPersonalHomepageAutoHide()" not in text:
    methods_block = f"""
    {START}
    private fun scheduleGlobalBrowserAutoHide() {{
        globalAutoHideJob?.cancel()
        globalAutoHideJob = viewLifecycleOwner.lifecycleScope.launch {{
            delay(30_000)

            if (!isAdded || view == null || _browserToolbarView == null) return@launch

            expandBrowserView()
            globalToolbarHidden = true
        }}
    }}

    internal fun onUserInteractionForPersonalHomepageAutoHide() {{
        globalAutoHideJob?.cancel()

        if (globalToolbarHidden && _browserToolbarView != null) {{
            collapseBrowserView()
            browserToolbarView.visible()
            browserToolbarView.expand()
            globalToolbarHidden = false
        }}

        if (isAdded && view != null && _browserToolbarView != null) {{
            scheduleGlobalBrowserAutoHide()
        }}
    }}

    private fun stopGlobalBrowserAutoHide() {{
        globalAutoHideJob?.cancel()
    }}
    {END}

"""
    text = insert_before_once(
        text,
        "override fun onAccessibilityStateChanged(enabled: Boolean) {",
        methods_block,
        "insertar métodos de autohide antes de onAccessibilityStateChanged"
    )

if "scheduleGlobalBrowserAutoHide()" not in text.split("override fun onResume()", 1)[-1][:400]:
    text = replace_once(
        text,
        r"(override fun onResume\(\) \{\s*\n\s*super\.onResume\(\)\s*\n\s*val components = requireComponents\s*\n)",
        r"\1"
        + f"""        {START}
        scheduleGlobalBrowserAutoHide()
        {END}
""",
        "arrancar temporizador en onResume"
    )

if "stopGlobalBrowserAutoHide()" not in text.split("override fun onPause()", 1)[-1][:300]:
    text = replace_once(
        text,
        r"(override fun onPause\(\) \{\s*\n\s*super\.onPause\(\)\s*\n)",
        r"\1"
        + f"""        {START}
        stopGlobalBrowserAutoHide()
        {END}
""",
        "parar temporizador en onPause"
    )

if "globalToolbarHidden = false" not in text.split("override fun onDestroyView()", 1)[-1][:500]:
    text = replace_once(
        text,
        r"(override fun onDestroyView\(\) \{\s*\n\s*super\.onDestroyView\(\)\s*\n)",
        r"\1"
        + f"""        {START}
        stopGlobalBrowserAutoHide()
        globalToolbarHidden = false
        {END}
""",
        "limpiar estado en onDestroyView"
    )

if "globalToolbarHidden = false" not in text.split("private fun handleTabSelected", 1)[-1][:250]:
    text = replace_once(
        text,
        r"(private fun handleTabSelected\(selectedTab: TabSessionState, isCustomTabSession: Boolean\) \{\s*\n)",
        r"\1"
        + f"""        {START}
        globalToolbarHidden = false
        scheduleGlobalBrowserAutoHide()
        {END}
""",
        "reiniciar temporizador al cambiar de tab"
    )

BASE.write_text(text, encoding="utf-8")

print("Parche aplicado correctamente en:")
print(BASE)
print()
print("Ahora compila con:")
print("JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 PATH=/usr/lib/jvm/java-17-openjdk-amd64/bin:$PATH ./gradlew :app:compileForkReleaseKotlin --no-daemon --max-workers=2")