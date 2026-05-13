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


def write_backup_once(path: Path, original: str) -> None:
    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")


def patch_file(path: Path, old: str, new: str, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"[{label}] No existe el archivo: {path}")

    original = path.read_text(encoding="utf-8")

    if new in original:
        print(f"[{label}] Ya parece estar parcheado.")
        return

    updated = replace_once(original, old, new, label)
    write_backup_once(path, original)
    path.write_text(updated, encoding="utf-8")

    print(f"[{label}] Parche aplicado.")


def patch_browser_toolbar_view_safely() -> None:
    path = BROWSER_TOOLBAR_VIEW_PATH

    if not path.exists():
        raise FileNotFoundError(f"[BrowserToolbarView.kt] No existe: {path}")

    original = path.read_text(encoding="utf-8")

    old_block = """            if (!isCustomTabSession) {
                toolbar.display.setMenuDismissAction {
                    toolbar.invalidateActions()
                }
            }"""

    new_block = """            if (!isCustomTabSession) {
                toolbar.display.setMenuDismissAction {
                    // Fork policy:
                    // Avoid invalidating toolbar actions on menu dismiss.
                    // This works around Android 8 popup auto-dismiss behavior.
                }
            }"""

    if new_block in original:
        print("[BrowserToolbarView.kt / Android 8 menu dismiss workaround] Ya parece estar parcheado.")
        return

    if "toolbar.display.setMenuDismissAction" in original and "toolbar.invalidateActions()" not in original:
        print("[BrowserToolbarView.kt / Android 8 menu dismiss workaround] Ya parece estar parcheado.")
        return

    patch_file(
        path,
        old_block,
        new_block,
        "BrowserToolbarView.kt / Android 8 menu dismiss workaround",
    )


def main() -> int:
    settings_old_composable = """var shouldUseComposableToolbar by booleanPreference(
        key = appContext.getPreferenceKey(R.string.pref_key_enable_composable_toolbar),
        default = { FxNimbus.features.composableToolbar.value().enabled },
    )"""

    settings_new_composable = """private val composableToolbarPreferenceKey =
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

    settings_old_bottom = """var shouldUseBottomToolbar by booleanPreference(
        key = appContext.getPreferenceKey(R.string.pref_key_toolbar_bottom),
        default = true,
        persistDefaultIfNotExists = true,
    )"""

    settings_new_bottom = """private val bottomToolbarPreferenceKey =
        appContext.getPreferenceKey(R.string.pref_key_toolbar_bottom)

    /**
     * Fork policy: always keep the browser toolbar at the bottom.
     */
    var shouldUseBottomToolbar: Boolean
        get() = true
        set(value) {
            preferences.edit {
                putBoolean(bottomToolbarPreferenceKey, true)
            }
        }"""

    settings_old_toolbar_position = """val toolbarPosition: ToolbarPosition
        get() = if (isTabStripEnabled) {
            ToolbarPosition.TOP
        } else if (shouldUseBottomToolbar) {
            ToolbarPosition.BOTTOM
        } else {
            ToolbarPosition.TOP
        }"""

    settings_new_toolbar_position = """val toolbarPosition: ToolbarPosition
        get() = ToolbarPosition.BOTTOM"""

    settings_old_light = """var shouldUseLightTheme by booleanPreference(
        appContext.getPreferenceKey(R.string.pref_key_light_theme),
        default = false,
    )"""

    settings_new_light = """private val lightThemePreferenceKey =
        appContext.getPreferenceKey(R.string.pref_key_light_theme)

    /**
     * Fork policy: never use the explicit light theme.
     */
    var shouldUseLightTheme: Boolean
        get() = false
        set(value) {
            preferences.edit {
                putBoolean(lightThemePreferenceKey, false)
            }
        }"""

    settings_old_dark = """var shouldUseDarkTheme by booleanPreference(
        appContext.getPreferenceKey(R.string.pref_key_dark_theme),
        default = false,
    )"""

    settings_new_dark = """private val darkThemePreferenceKey =
        appContext.getPreferenceKey(R.string.pref_key_dark_theme)

    /**
     * Fork policy: always use dark theme.
     */
    var shouldUseDarkTheme: Boolean
        get() = true
        set(value) {
            preferences.edit {
                putBoolean(darkThemePreferenceKey, true)
            }
        }"""

    settings_old_follow_device = """var shouldFollowDeviceTheme by booleanPreference(
        appContext.getPreferenceKey(R.string.pref_key_follow_device_theme),
        default = false,
    )"""

    settings_new_follow_device = """private val followDeviceThemePreferenceKey =
        appContext.getPreferenceKey(R.string.pref_key_follow_device_theme)

    /**
     * Fork policy: do not follow system theme; force app dark mode.
     */
    var shouldFollowDeviceTheme: Boolean
        get() = false
        set(value) {
            preferences.edit {
                putBoolean(followDeviceThemePreferenceKey, false)
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

    try:
        patch_file(
            SETTINGS_PATH,
            settings_old_composable,
            settings_new_composable,
            "Settings.kt / force legacy toolbar",
        )
        patch_file(
            SETTINGS_PATH,
            settings_old_bottom,
            settings_new_bottom,
            "Settings.kt / force bottom toolbar",
        )
        patch_file(
            SETTINGS_PATH,
            settings_old_toolbar_position,
            settings_new_toolbar_position,
            "Settings.kt / force toolbarPosition BOTTOM",
        )
        patch_file(
            SETTINGS_PATH,
            settings_old_light,
            settings_new_light,
            "Settings.kt / disable light theme",
        )
        patch_file(
            SETTINGS_PATH,
            settings_old_dark,
            settings_new_dark,
            "Settings.kt / force dark theme",
        )
        patch_file(
            SETTINGS_PATH,
            settings_old_follow_device,
            settings_new_follow_device,
            "Settings.kt / disable follow device theme",
        )
        patch_file(
            BASE_BROWSER_PATH,
            base_browser_old,
            base_browser_new,
            "BaseBrowserFragment.kt / force BrowserToolbarView",
        )
        patch_browser_toolbar_view_safely()

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("\nNo sigas compilando hasta revisar el archivo indicado.")
        return 1

    print("\nListo. Revisa los cambios con:")
    print("  git diff")
    print("\nCompila con:")
    print("  ./gradlew assembleDebug")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

