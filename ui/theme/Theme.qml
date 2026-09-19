pragma Singleton
import QtQuick

/*
 * Theme — the single source of truth for every colour in the application.
 *
 * Two complete palettes are declared side by side and swapped as a unit, so a
 * token can never be defined for one scheme and forgotten in the other.  Call
 * sites only ever see the flattened semantic names (Theme.surface, Theme.text,
 * ...), which keeps pages free of raw colour literals.
 */
QtObject {
    id: root

    // ---- scheme selection -------------------------------------------------
    // "light" | "dark" | "system"
    property string mode: "dark"
    // Mirrored from the platform colour scheme by the application shell.
    property bool systemPrefersDark: true

    readonly property bool isDark: mode === "system" ? systemPrefersDark : mode === "dark"
    readonly property QtObject palette: isDark ? darkPalette : lightPalette

    // ---- semantic tokens --------------------------------------------------
    // Surfaces
    readonly property color background: palette.background
    readonly property color surface: palette.surface
    readonly property color surfaceElevated: palette.surfaceElevated
    readonly property color surfaceSubtle: palette.surfaceSubtle
    readonly property color surfaceHover: palette.surfaceHover
    readonly property color surfaceSunken: palette.surfaceSunken

    // Text
    readonly property color text: palette.text
    readonly property color textSecondary: palette.textSecondary
    readonly property color textMuted: palette.textMuted
    readonly property color textDisabled: palette.textDisabled

    // Lines
    readonly property color divider: palette.divider
    readonly property color border: palette.border
    readonly property color borderStrong: palette.borderStrong

    // Accent
    readonly property color accent: palette.accent
    readonly property color accentHover: palette.accentHover
    readonly property color accentPressed: palette.accentPressed
    readonly property color accentSubtle: palette.accentSubtle
    readonly property color accentContrast: palette.accentContrast

    // Feedback
    readonly property color success: palette.success
    readonly property color warning: palette.warning
    readonly property color error: palette.error

    // Scientific plotting
    readonly property color plotBackground: palette.plotBackground
    readonly property color gridLine: palette.gridLine
    readonly property color axisLine: palette.axisLine
    readonly property var series: palette.series


    function toggle() {
        mode = isDark ? "light" : "dark"
    }

    // ---- palettes ---------------------------------------------------------
    /* Obsidian / Champagne Gold.  Values sourced from the canonical
     * Sunumatik palette library (docs/design/CAD_WORKBENCH_R1_REFERENCE_STUDY.md),
     * extended to this application's full token set and contrast-validated
     * (acceptance/cad_workbench_r1/contrast_audit.json) rather than invented.
     * Obsidian, never pure black; surfaces separate by luminance only, on
     * one warm-neutral temperature family throughout -- mixing a cool grey
     * into a warm scheme is what the reference material calls the "dirty
     * deck" failure. */
    readonly property QtObject darkPalette: QtObject {
        readonly property color background: "#0F1013"
        readonly property color surface: "#1A1C21"
        readonly property color surfaceElevated: "#22252C"
        readonly property color surfaceSubtle: "#14151A"
        readonly property color surfaceHover: "#2B2E37"
        readonly property color surfaceSunken: "#0A0B0D"

        readonly property color text: "#F4EEE1"
        readonly property color textSecondary: "#D2CCBF"
        readonly property color textMuted: "#A9A296"
        readonly property color textDisabled: "#54524E"

        readonly property color divider: "#2E3037"
        readonly property color border: "#383B44"
        readonly property color borderStrong: "#4A4E5A"

        // Champagne: application state only -- selection, focus, the
        // primary action. Never a fill for a panel, a body, or decoration
        // (see docs/design/CAD_WORKBENCH_R1_REFERENCE_STUDY.md -- the source
        // material is itself a luxury/keynote theme; restraint here is load
        // -bearing, not a style preference).
        readonly property color accent: "#D3B26A"
        readonly property color accentHover: "#DABF84"
        readonly property color accentPressed: "#9C8552"
        readonly property color accentSubtle: "#34312B"
        readonly property color accentContrast: "#191307"

        readonly property color success: "#6FBF9A"
        readonly property color warning: "#D98A3E"
        readonly property color error: "#C95F6A"

        readonly property color plotBackground: "#14151A"
        readonly property color gridLine: "#2E3037"
        readonly property color axisLine: "#4A4E5A"
        // Accent stays out of the front of the series ramp so that a curve is
        // never the same colour as the marker sitting on it. series[5] is
        // copper/thermal, not the rose used for Theme.error -- Engine
        // Design's ComponentRegistry.subtypeColor() maps "hot gas" and
        // "wall" to series[5], and that color must never equal Theme.error
        // (brief-mandated check: error must stay distinguishable from hot
        // gas, acceptance/cad_workbench_r1/contrast_audit.json's palette
        // section records this pair explicitly).
        readonly property var series: ["#5590C9", "#6FBF9A", "#A88BD9",
                                       "#D9C36A", "#62A8B2", "#C86A40",
                                       "#A9A296", "#D3B26A"]

    }

    /* Warm pearl paper, never pure white -- the light register of the same
     * Obsidian / Champagne system, not a straight inversion of the dark
     * palette. Sunumatik does not publish a light variant of this theme (it
     * is documented there as dark/keynote-only); every value below was
     * derived to keep the same hue family as the dark palette and verified
     * against WCAG 4.5:1 by acceptance/cad_workbench_r1/contrast_audit.json
     * rather than guessed -- including textMuted, which the pre-R1 palette
     * failed at 4.33:1 here and this one clears at 5.36:1+. */
    readonly property QtObject lightPalette: QtObject {
        readonly property color background: "#F3EEE3"
        readonly property color surface: "#FAF7F1"
        readonly property color surfaceElevated: "#FFFFFF"
        readonly property color surfaceSubtle: "#ECE6D8"
        readonly property color surfaceHover: "#E7DFCC"
        readonly property color surfaceSunken: "#E1D7C0"

        readonly property color text: "#191307"
        readonly property color textSecondary: "#4A4030"
        readonly property color textMuted: "#6B6046"
        readonly property color textDisabled: "#A79C86"

        readonly property color divider: "#DED3BD"
        readonly property color border: "#D0C2A4"
        readonly property color borderStrong: "#B7A683"

        readonly property color accent: "#7D5E28"
        readonly property color accentHover: "#8F6E34"
        readonly property color accentPressed: "#664B1E"
        readonly property color accentSubtle: "#F1E6CC"
        readonly property color accentContrast: "#FFF8EC"

        readonly property color success: "#376E52"
        readonly property color warning: "#A05A16"
        readonly property color error: "#A13F4A"

        readonly property color plotBackground: "#F7F3EA"
        readonly property color gridLine: "#E4DAC4"
        readonly property color axisLine: "#B7A683"
        readonly property var series: ["#2E5C8C", "#376E52", "#634A8C",
                                       "#7A6524", "#2A6266", "#8A4826",
                                       "#6B6046", "#7D5E28"]

    }
}
