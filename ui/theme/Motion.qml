pragma Singleton
import QtQuick

/*
 * Motion — one place for every duration and easing curve.
 * Transitions confirm a state change; they never announce themselves.
 * No overshoot, no bounce, no long fades.
 */
QtObject {
    readonly property int fast: 110      // hover, focus rings
    readonly property int base: 160      // selection, panel state
    readonly property int slow: 220      // page entry, marker travel

    readonly property int standard: Easing.OutCubic
    readonly property int emphasized: Easing.InOutCubic
}
