pragma Singleton
import QtQuick

/*
 * Typography — type families, sizes and weights.
 *
 * Two families carry the whole interface: a humanist sans for prose and a
 * monospaced face for every engineering quantity.  The monospace face is what
 * gives the readouts their column alignment (tabular figures) and keeps Greek
 * symbols, subscripts and exponents on a predictable rhythm.
 */
QtObject {
    id: root

    readonly property var sansCandidates: [
        "Inter", "Segoe UI Variable Text", "Segoe UI",
        "SF Pro Text", "Helvetica Neue", "Noto Sans", "DejaVu Sans"
    ]
    readonly property var monoCandidates: [
        "JetBrains Mono", "IBM Plex Mono", "Cascadia Mono", "Consolas",
        "SF Mono", "Menlo", "DejaVu Sans Mono", "Courier New"
    ]

    readonly property string sans: firstAvailable(sansCandidates)
    readonly property string mono: firstAvailable(monoCandidates)

    // ---- sizes ------------------------------------------------------------
    readonly property real pageTitle: 21
    readonly property real pageSubtitle: 12.5
    readonly property real sectionLabel: 10.5      // uppercase, tracked
    readonly property real groupLabel: 12
    readonly property real body: 13
    readonly property real bodySmall: 12
    readonly property real inputLabel: 11.5
    readonly property real inputValue: 15          // mono
    readonly property real readoutLarge: 20        // mono
    readonly property real readoutMedium: 15       // mono
    readonly property real readoutSmall: 12.5      // mono
    readonly property real navItem: 12.5
    readonly property real navGroup: 10
    readonly property real status: 11
    readonly property real meta: 10.5

    // ---- weights ----------------------------------------------------------
    readonly property int regular: Font.Normal
    readonly property int medium: Font.Medium
    readonly property int semibold: Font.DemiBold

    // ---- tracking ---------------------------------------------------------
    readonly property real sectionTracking: 1.1
    readonly property real navGroupTracking: 1.0
    readonly property real titleTracking: -0.2

    // ---- rhythm -----------------------------------------------------------
    readonly property real proseLineHeight: 1.45

    function firstAvailable(candidates) {
        var installed = Qt.fontFamilies()
        for (var i = 0; i < candidates.length; ++i) {
            if (installed.indexOf(candidates[i]) !== -1)
                return candidates[i]
        }
        return candidates[candidates.length - 1]
    }
}
