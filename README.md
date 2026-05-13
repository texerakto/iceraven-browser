## Texerakto Custom Iceraven Build – Feature Summary

This custom build of Iceraven introduces several behavior and UI modifications that are not available in the original upstream browser.

### Main Custom Features

#### 1. Forced Personal Homepage Startup

The browser is modified to always launch directly into the configured personal homepage at startup.

Behavior:

* App startup immediately opens the user-defined homepage.
* Bypasses the default startup flow used by upstream Iceraven/Fenix.
* Ensures consistent startup behavior across sessions.
* Works even after app restarts.

This creates a more kiosk-like or appliance-style browsing experience.

---

#### 2. Automatic Toolbar / Address Bar Auto-Hide

A custom auto-hide system was implemented for the browser toolbar/address bar.

Behavior:

* Automatically hides the navigation/search/address bar after a delay.
* Works independently from page load completion.
* Triggered simply by having an active focused tab.
* Intended for fullscreen-style browsing and cleaner UI.
* Designed to work with bottom toolbar mode enabled.

This behavior does not exist in stock Iceraven/Fenix.

---

#### 3. Persistent UI Simplification

The modified build prioritizes immersive browsing by reducing permanent UI visibility.

Effects:

* Cleaner screen usage.
* Less interface obstruction.
* More content-focused browsing.
* Better experience for tablets, embedded systems, kiosk devices, and media-oriented usage.

---

#### 4. Legacy / Classic Toolbar Restoration Experiments

The build includes work related to restoring older toolbar/menu behavior previously removed from newer upstream versions.

This includes:

* investigation into hidden “Enable Composable Toolbar” settings
* compatibility experimentation with older toolbar systems
* partial restoration tooling and patching infrastructure

---

#### 5. Advanced Patch Infrastructure

Custom Python patching scripts were developed to:

* automatically modify source files
* re-apply customizations after repository updates
* maintain compatibility with future upstream versions

This allows the build system to be reproducible and maintainable.

---

#### 6. Custom Build & Branding Pipeline

The project includes:

* automated Android SDK setup
* custom compilation workflow
* modified branding strings
* automated patch application
* reproducible release generation

---

## Resulting Browser Characteristics

Compared to original Iceraven/Fenix, this custom build provides:

* aggressive immersive browsing behavior
* startup directly into personal homepage
* autonomous toolbar hiding
* reduced UI persistence
* experimental restoration of legacy browser UX elements
* custom patching and build automation

---

## Intended Use Cases

This build is especially suitable for:

* fullscreen browsing
* kiosk systems
* embedded Android devices
* media terminals
* dedicated homepage launchers
* custom Android browser deployments
