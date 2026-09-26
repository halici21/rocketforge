pragma Singleton
import QtQuick

/*
 * Motion — one place for every duration and easing curve.
 * Transitions confirm a state change; they never announce themselves.
 * No overshoot, no bounce, no long fades.
 *
 * One preference governs all of it (Settings > Appearance > Motion):
 *
 *   full     every transition as designed, including small directional moves
 *   reduced  shorter fades and no spatial movement
 *   off      state changes are immediate; the flow cues start paused
 *
 * Every duration below is derived from the preference, so an animation
 * written with these tokens obeys it without knowing it exists. Whatever the
 * mode, the end state is the same: motion only ever changes how a state
 * change looks, never what state the page reaches.
 */
QtObject {
    property string mode: "full"

    readonly property bool animated: mode !== "off"
    // Directional offsets (a panel arriving from its edge, a section
    // shifting a few pixels) only in full motion.
    readonly property bool spatial: mode === "full"
    readonly property real factor: mode === "full" ? 1.0 : mode === "reduced" ? 0.55 : 0.0

    function ms(value) { return Math.round(value * factor) }

    // ---- the original tokens, now obeying the preference ------------------
    readonly property int fast: ms(110)      // hover, focus rings
    readonly property int base: ms(160)      // selection, panel state
    readonly property int slow: ms(220)      // page entry, marker travel

    // ---- semantic tokens --------------------------------------------------
    readonly property int micro: ms(90)      // pointer proximity, edge light
    readonly property int section: ms(170)   // Calculator / Chart / Table switch
    readonly property int panel: ms(200)     // a drawer arriving or leaving
    readonly property int focus: ms(240)     // focus mode, the analysis lens
    readonly property int camera: ms(320)    // a standard-view change
    readonly property int data: ms(280)      // one solved state to the next

    // Pixels a section or a panel travels while it fades in: enough to say
    // where it came from, never a slide across the screen.
    readonly property real sectionShift: spatial ? 10 : 0
    readonly property real panelShift: spatial ? 18 : 0

    readonly property int standard: Easing.OutCubic
    readonly property int emphasized: Easing.InOutCubic
}
