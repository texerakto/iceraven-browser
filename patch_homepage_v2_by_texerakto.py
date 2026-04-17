from pathlib import Path
import re
import sys

ROOT = Path("/workspaces/iceraven-browser")
if not ROOT.exists():
    ROOT = Path.cwd()

TARGET = ROOT / "app/src/main/java/org/mozilla/fenix/HomeActivity.kt"

START = "/////////////// Texerakto REPO /////////////////////START////////"
END = "/////////////// Texerakto REPO /////////////////////END///////////"

if not TARGET.exists():
    print(f"No encuentro el archivo: {TARGET}")
    sys.exit(1)

text = TARGET.read_text(encoding="utf-8")

def replace_once(text: str, pattern: str, replacement: str, desc: str) -> str:
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise RuntimeError(f"No pude aplicar: {desc}")
    return new_text

def insert_after_once(text: str, needle: str, insertion: str, desc: str) -> str:
    idx = text.find(needle)
    if idx == -1:
        raise RuntimeError(f"No encontré punto de inserción: {desc}")
    idx_end = idx + len(needle)
    return text[:idx_end] + insertion + text[idx_end:]

# Si ya está aplicado, no repetir
if "shouldOpenPersonalHomepageOnStartup" in text and "openPersonalHomepageOnStartup" in text:
    print("El parche de personal homepage ya parece aplicado. No hago cambios.")
    sys.exit(0)

# 1) Sustituir el bloque de arranque en frío dentro de onCreate
old_block_pattern = r"""
            if \(shouldNavigateToBrowserOnColdStart\(savedInstanceState\)\) \{
                if \(!shouldStartOnHome\(\)\) \{
                    navigateToBrowserOnColdStart\(\)
                \}
                maybeShowSetAsDefaultBrowserPrompt\(\)
            \} else \{
                StartOnHome\.enterHomeScreen\.record\(NoExtras\(\)\)
            \}
"""

new_block = f"""
            {START}
            if (shouldNavigateToBrowserOnColdStart(savedInstanceState)) {{
                when {{
                    shouldOpenPersonalHomepageOnStartup() -> {{
                        openPersonalHomepageOnStartup()
                    }}
                    !shouldStartOnHome() -> {{
                        navigateToBrowserOnColdStart()
                    }}
                }}
                maybeShowSetAsDefaultBrowserPrompt()
            }} else {{
                StartOnHome.enterHomeScreen.record(NoExtras())
            }}
            {END}
"""

text = replace_once(
    text,
    old_block_pattern,
    new_block,
    "reemplazar bloque de arranque en frío",
)

# 2) Insertar los métodos nuevos justo después de shouldStartOnHome(...)
needle = """    @VisibleForTesting
    internal fun shouldStartOnHome(intent: Intent? = this.intent): Boolean {
        return components.strictMode.allowViolation(StrictMode::allowThreadDiskReads) {
            // We only want to open on home when users tap the app,
            // we want to ignore other cases when the app gets open by users clicking on links.
            getSettings().shouldStartOnHome() && intent?.action == ACTION_MAIN
        }
    }
"""

insertion = f"""

    {START}
    @VisibleForTesting
    internal fun shouldOpenPersonalHomepageOnStartup(intent: Intent? = this.intent): Boolean {{
        val settings = settings()
        val homepageUrl = settings.customHomepageUrl.trim()

        return shouldStartOnHome(intent) &&
            !settings.shouldUseDefaultHomepage &&
            homepageUrl.isNotEmpty()
    }}

    @VisibleForTesting
    internal fun openPersonalHomepageOnStartup() {{
        val homepageUrl = settings().customHomepageUrl.trim()

        openToBrowserAndLoad(
            searchTermOrURL = homepageUrl,
            newTab = true,
            from = BrowserDirection.FromGlobal,
        )
    }}
    {END}
"""

text = insert_after_once(
    text,
    needle,
    insertion,
    "insertar métodos shouldOpenPersonalHomepageOnStartup/openPersonalHomepageOnStartup",
)

TARGET.write_text(text, encoding="utf-8")

print("Parche aplicado correctamente en:")
print(TARGET)
print()
print("Comprueba compilación con:")
print("JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 PATH=/usr/lib/jvm/java-17-openjdk-amd64/bin:$PATH ./gradlew :app:compileForkReleaseKotlin --no-daemon --max-workers=2")