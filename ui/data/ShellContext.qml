pragma Singleton
import QtQuick

/*
 * ShellContext -- Analysis mode's shared shell selection/context state.
 *
 * A plain QML singleton, not Python-backed, mirroring EngineModel's own
 * role for Engine Design mode (ui/engine/model/EngineModel.qml): this is
 * UI-only state, not scientific data, so it belongs beside
 * Navigation/MockData rather than behind a controller.
 *
 * `currentPageIndex` and `browserCollapsed` are ONE-WAY mirrors of
 * `window.currentPageIndex`/`window.navCollapsed` (bound in ui/Main.qml).
 * `window`'s properties stay the sole write authority and the sole
 * externally-settable surface deliberately: several of the packaged
 * headless diagnostics under rocketforge/application/ already call
 * `window.setProperty` on these two by name, and renaming or relocating
 * the write path would break that production infrastructure. Read these
 * two from here (not from `window`) only from a
 * component defined in its own file that cannot reach `window`'s id
 * (`AnalysisDock`, `InspectorDrawer`, anything added later); never assign
 * to them, since an active Binding is silently removed by the first
 * imperative write to the same property.
 */
QtObject {
    property int currentPageIndex: 0

    property bool browserCollapsed: false

    // Whether the contextual Inspector drawer is open. Not wired to any
    // workspace yet (see InspectorDrawer.qml) -- present so a future
    // workspace that opens it has one shared flag to set, rather than each
    // caller inventing its own. Genuinely owned here (no window mirror):
    // no prior external contract references it.
    property bool inspectorOpen: false
}
