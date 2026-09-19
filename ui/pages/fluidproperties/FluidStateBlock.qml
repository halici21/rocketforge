import QtQuick
import QtQuick.Layouts
import "../../theme"
import "../../components"

/*
 * The Fluid Properties centerpiece: the fluid state itself.
 *
 * WHAT THIS IS. Per rf-engineering-workbench: "object-first" does not
 * require a hardware drawing -- a thermodynamic state can itself be the
 * central engineering object. This is a plain layout, not a Canvas: there
 * is no geometry to draw for a state, so none is invented. Every field
 * below is sourced from the solved FluidOutcome (resultChanged), never
 * from a live input control -- editing the fluid/T/p fields without
 * evaluating must never move this block, per rf-scientific-ui-contract's
 * header-vs-drawing rule.
 *
 * PHASE IS NEUTRAL, NOT VALIDITY. Phase (liquid/gas/supercritical/solid/
 * two-phase) is a scientific classification, not a trustworthiness signal
 * -- TWO_PHASE is a real, valid answer (rocketforge/physics/fluids/types.py),
 * not a warning state. Success/warning/error tones are reserved for the
 * RESULT status chip (evaluated / evaluated with warnings / refused); this
 * block never borrows them for phase, so a two-phase state never reads as
 * suspect next to a liquid one.
 */
Item {
    id: root

    property bool hasResult: false
    property bool stale: false
    property string fluidLabel: ""
    property string phase: ""
    property string temperatureText: ""
    property string pressureText: ""

    function phaseLabel(raw) {
        if (raw === "" || raw === "not determined")
            return "PHASE NOT DETERMINED"
        return raw.replace("_", "-").toUpperCase()
    }

    readonly property color activeColor: root.hasResult && !root.stale
                                         ? Theme.text : Theme.textMuted
    readonly property color secondaryColor: root.hasResult && !root.stale
                                            ? Theme.textSecondary : Theme.textMuted

    implicitHeight: column.implicitHeight

    ColumnLayout {
        id: column
        width: parent.width
        spacing: Metrics.spacing.xs

        RFSectionLabel {
            text: "Fluid state"
        }

        Text {
            Layout.fillWidth: true
            text: root.hasResult ? root.fluidLabel : "No state evaluated"
            color: root.activeColor
            font.family: Typography.sans
            font.pixelSize: Typography.readoutSmall
            font.weight: Typography.medium
            elide: Text.ElideRight

            Behavior on color { ColorAnimation { duration: Motion.base } }
        }

        Text {
            Layout.fillWidth: true
            text: root.hasResult ? root.phaseLabel(root.phase) : "—"
            color: root.secondaryColor
            font.family: Typography.sans
            font.pixelSize: Typography.body
            font.letterSpacing: Typography.sectionTracking
            elide: Text.ElideRight

            Behavior on color { ColorAnimation { duration: Motion.base } }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.xs
            spacing: Metrics.spacing.l

            Text {
                text: "T  " + (root.hasResult ? root.temperatureText : "—")
                color: root.secondaryColor
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall

                Behavior on color { ColorAnimation { duration: Motion.base } }
            }
            Text {
                text: "p  " + (root.hasResult ? root.pressureText : "—")
                color: root.secondaryColor
                font.family: Typography.mono
                font.pixelSize: Typography.readoutSmall

                Behavior on color { ColorAnimation { duration: Motion.base } }
            }
            Item { Layout.fillWidth: true }
        }
    }
}
