import QtQuick
import "../theme"

/*
 * RFBoundNumberField - a number field wired to a backend property.
 *
 * A field that both displays and edits the same value is the classic source of
 * a QML binding loop: binding `text` to the property while writing the property
 * from `onTextChanged` means each drives the other forever.
 *
 * The loop is broken by making the flow one-way in each direction:
 *
 *   backend -> field   `value` is bound by the caller; the field mirrors it
 *                      into `text` only when the two genuinely differ.
 *   field -> backend   editing emits `valueEdited`; the field never assigns to
 *                      `value` itself, so the caller's binding stays intact.
 *
 * The guard flag suppresses the echo that a programmatic text update would
 * otherwise produce.
 */
RFNumberField {
    id: control

    // Bound by the caller to the backing property. Never assigned from here.
    property real value: 0
    property int digits: 4
    property int decimals: -1

    readonly property int effectiveDecimals: decimals >= 0 ? decimals : digits

    signal valueEdited(real newValue)

    property bool _guard: false

    function _show(v) {
        var shown = parseFloat(control.text)
        if (shown === v)
            return
        _guard = true
        control.text = v.toFixed(control.effectiveDecimals)
        _guard = false
    }

    onValueChanged: control._show(value)

    onTextChanged: {
        if (_guard)
            return
        var parsed = parseFloat(control.text)
        // A partially typed number ("-", ".", "1e") is an ordinary event while
        // someone is typing, not an error. Wait for something parseable.
        if (isNaN(parsed) || parsed === control.value)
            return
        control.valueEdited(parsed)
    }

    Component.onCompleted: {
        _guard = true
        control.text = control.value.toFixed(control.effectiveDecimals)
        _guard = false
    }
}
