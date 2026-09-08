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
    readonly property QtObject darkPalette: QtObject {
        // Graphite, never pure black; surfaces separate by luminance only.
        readonly property color background: "#131519"
        readonly property color surface: "#191C21"
        readonly property color surfaceElevated: "#1F232A"
        readonly property color surfaceSubtle: "#16191E"
        readonly property color surfaceHover: "#232830"
        readonly property color surfaceSunken: "#101216"

        readonly property color text: "#E7E9EC"
        readonly property color textSecondary: "#A4ABB5"
        readonly property color textMuted: "#727A85"
        readonly property color textDisabled: "#4E555F"

        readonly property color divider: "#232830"
        readonly property color border: "#2B313A"
        readonly property color borderStrong: "#3A414C"

        // Ember: heat without alarm.  Used sparingly, for state only.
        readonly property color accent: "#D97F45"
        readonly property color accentHover: "#E68F55"
        readonly property color accentPressed: "#BF6C36"
        readonly property color accentSubtle: "#2A2018"
        readonly property color accentContrast: "#14161A"

        readonly property color success: "#5FAE8C"
        readonly property color warning: "#D9B25B"
        readonly property color error: "#D9695E"

        readonly property color plotBackground: "#15181D"
        readonly property color gridLine: "#232830"
        readonly property color axisLine: "#3E4650"
        // Accent stays out of the front of the series ramp so that a curve is
        // never the same colour as the marker sitting on it.
        readonly property var series: ["#7FB3E0", "#72C09B", "#B58FD6",
                                       "#D9C069", "#6FC2C6", "#E08078",
                                       "#9BA6B2", "#D97F45"]

    }

    /* Warm neutral paper, never pure white.  The scheme was legible but sat
     * too close together: secondary text, borders and the grid have each been
     * darkened by roughly one step so that hierarchy survives a bright room and
     * a laptop panel, without turning the surfaces grey. */
    readonly property QtObject lightPalette: QtObject {
        readonly property color background: "#EDEBE5"
        readonly property color surface: "#FAF9F6"
        readonly property color surfaceElevated: "#FFFFFF"
        readonly property color surfaceSubtle: "#F3F1EB"
        readonly property color surfaceHover: "#E5E1D8"
        readonly property color surfaceSunken: "#E2DED6"

        readonly property color text: "#171A1F"
        readonly property color textSecondary: "#49505A"
        readonly property color textMuted: "#666E79"
        readonly property color textDisabled: "#9AA1AA"

        readonly property color divider: "#DBD7CE"
        readonly property color border: "#C8C3B8"
        readonly property color borderStrong: "#A6A093"

        readonly property color accent: "#B85A26"
        readonly property color accentHover: "#C86730"
        readonly property color accentPressed: "#9C4A1D"
        readonly property color accentSubtle: "#F7E7D9"
        readonly property color accentContrast: "#FFFFFF"

        readonly property color success: "#357A5B"
        readonly property color warning: "#8C6B1D"
        readonly property color error: "#A9423A"

        readonly property color plotBackground: "#FCFBF8"
        readonly property color gridLine: "#D7D3C9"
        readonly property color axisLine: "#9E9789"
        readonly property var series: ["#33689B", "#357A5B", "#6B4795",
                                       "#7D6117", "#26787D", "#A9423A",
                                       "#4E5763", "#B85A26"]

    }
}
