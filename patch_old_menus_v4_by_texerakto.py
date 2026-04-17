from pathlib import Path
import sys

REPO_ROOT = Path("/workspaces/iceraven-browser")

SETTINGS_PATH = REPO_ROOT / "app/src/main/java/org/mozilla/fenix/utils/Settings.kt"
BASE_BROWSER_PATH = REPO_ROOT / "app/src/main/java/org/mozilla/fenix/browser/BaseBrowserFragment.kt"
BROWSER_TOOLBAR_VIEW_PATH = REPO_ROOT / "app/src/main/java/org/mozilla/fenix/components/toolbar/BrowserToolbarView.kt"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"[{label}] Se esperaba encontrar exactamente 1 coincidencia, pero hay {count}."
        )
    return text.replace(old, new, 1)


def patch_file(path: Path, old: str, new: str, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"[{label}] No existe el archivo: {path}")

    original = path.read_text(encoding="utf-8")

    if new in original:
        print(f"[{label}] Ya parece estar parcheado: {path}")
        return

    updated = replace_once(original, old, new, label)

    backup_path = path.with_suffix(path.suffix + ".bak")
    if not backup_path.exists():
        backup_path.write_text(original, encoding="utf-8")

    path.write_text(updated, encoding="utf-8")

    print(f"[{label}] Parche aplicado: {path}")
    print(f"[{label}] Backup creado:   {backup_path}")


def main() -> int:
    settings_old = """var shouldUseComposableToolbar by booleanPreference(
        key = appContext.getPreferenceKey(R.string.pref_key_enable_composable_toolbar),
        default = { FxNimbus.features.composableToolbar.value().enabled },
    )"""

    settings_new = """private val composableToolbarPreferenceKey =
        appContext.getPreferenceKey(R.string.pref_key_enable_composable_toolbar)

    /**
     * Fork policy: always use legacy toolbar (disable Compose toolbar).
     */
    var shouldUseComposableToolbar: Boolean
        get() = false
        set(value) {
            preferences.edit {
                putBoolean(composableToolbarPreferenceKey, false)
            }
        }"""

    base_browser_old = """private fun initializeBrowserToolbar(
        activity: HomeActivity,
        store: BrowserStore,
        readerMenuController: DefaultReaderModeController,
    ) = when (activity.settings().shouldUseComposableToolbar) {
        true -> initializeBrowserToolbarComposable(activity, store, readerMenuController)
        false -> initializeBrowserToolbarView(activity, store)
    }"""

    base_browser_new = """private fun initializeBrowserToolbar(
        activity: HomeActivity,
        store: BrowserStore,
        readerMenuController: DefaultReaderModeController,
    ) = initializeBrowserToolbarView(activity, store)"""

    browser_toolbar_view_old = """            if (!isCustomTabSession) {
                toolbar.display.setMenuDismissAction {
                    toolbar.invalidateActions()
                }
            }"""

    browser_toolbar_view_new = """            if (!isCustomTabSession) {
                toolbar.display.setMenuDismissAction {
                    // Fork policy:
                    // Avoid invalidating toolbar actions on menu dismiss.
                    // This helps prevent the modern popup from being rebuilt
                    // and immediately auto-closing.
                }
            }"""

    try:
        patch_file(SETTINGS_PATH, settings_old, settings_new, "Settings.kt")
        patch_file(
            BASE_BROWSER_PATH,
            base_browser_old,
            base_browser_new,
            "BaseBrowserFragment.kt",
        )
        patch_file(
            BROWSER_TOOLBAR_VIEW_PATH,
            browser_toolbar_view_old,
            browser_toolbar_view_new,
            "BrowserToolbarView.kt",
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print("\nListo. Ahora revisa los cambios con:")
    print("  git diff")
    print("\nY compila con:")
    print("  ./gradlew assembleDebug")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())