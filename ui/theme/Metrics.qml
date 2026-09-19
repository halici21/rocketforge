pragma Singleton
import QtQuick

/*
 * Metrics — spacing, radii and the fixed dimensions of the shell.
 * Nothing in the application should hard-code a layout constant that belongs
 * to one of these scales.
 */
QtObject {
    // ---- spacing scale ----------------------------------------------------
    readonly property QtObject spacing: QtObject {
        readonly property real xxs: 2
        readonly property real xs: 4
        readonly property real s: 8
        readonly property real m: 12
        readonly property real l: 16
        readonly property real xl: 20
        readonly property real xxl: 24
        readonly property real h1: 32
        readonly property real h2: 40
    }

    // ---- corner radii -----------------------------------------------------
    // Restrained on purpose: surfaces are only slightly softened, never pills.
    readonly property QtObject radius: QtObject {
        readonly property real xs: 4
        readonly property real s: 6      // chips, ticks, small markers
        readonly property real m: 8      // inputs, buttons, segments
        readonly property real l: 10     // grouped controls
        readonly property real xl: 12    // panels and workspace surfaces
    }

    // ---- strokes ----------------------------------------------------------
    readonly property real hairline: 1
    readonly property real focusRing: 1.5

    // ---- shell ------------------------------------------------------------
    readonly property real topBarHeight: 46
    readonly property real statusBarHeight: 26
    readonly property real navWidth: 238
    readonly property real navItemHeight: 29
    readonly property real navGroupHeight: 26
    readonly property real railWidth: 316

    // ---- engine workspace panels -----------------------------------------
    // The side panels are collapsible, so each needs a resting width, a floor
    // it may not be dragged below, and the width of the strip that is left
    // behind to bring it back.
    readonly property real projectPanelWidth: 264
    readonly property real projectPanelMin: 210
    readonly property real projectPanelMax: 380
    readonly property real inspectorWidth: 324
    readonly property real inspectorMin: 264
    readonly property real inspectorMax: 440
    readonly property real collapsedRailWidth: 26
    readonly property real configRailWidth: 272
    readonly property real configRailMin: 236

    // ---- analysis mode: model browser --------------------------------
    // Slimmer than Engine Design's project panel by design (the
    // shell-prototype decision, docs/design/CAD_WORKBENCH_R1_DESIGN_DECISION.md):
    // the Analysis-mode viewport stays as dominant as it already was, so
    // this rail costs less width, both resting and at its floor.
    // Analysis Experience R2: the rail is a narrow, always-visible family
    // strip now, not a permanent page list -- the contextual module
    // drawer floats over the workspace instead of reserving width, so the
    // resting panel only needs to fit the rail itself.
    readonly property real browserPanelWidth: 64
    readonly property real browserPanelMin: 64
    readonly property real browserPanelMax: 200

    // ---- controls ---------------------------------------------------------
    readonly property real controlHeight: 34
    readonly property real controlHeightSmall: 26
    readonly property real iconButton: 28
    readonly property real chipHeight: 22
    readonly property real panelPadding: 16
    readonly property real pagePadding: 20
    readonly property real touchTarget: 24
}
