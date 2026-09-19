import QtQuick
import QtQuick.Layouts
import "../theme"

/*
 * RFPanel - the only surface container in the application.
 *
 * Children are laid out in a ColumnLayout, so a panel can hold a stack of
 * fields or a single item that fills it (a plot, a drawing). Panels are used
 * to group content, never to decorate it: no shadow, no gradient, one hairline.
 *
 * `chromeless: true` drops the border and background entirely, keeping only
 * the title/trailing header and the content layout -- for the dominant
 * engineering-object region of a recomposed workbench view, where spacing
 * and a divider already do the grouping a border would otherwise repeat
 * (rf-engineering-workbench's own "ask what a border does that spacing
 * could not" test, applied at the structural-recovery pass rather than
 * left unapplied). Defaults to false: every existing consumer keeps its
 * exact current appearance unless it opts in.
 */
Rectangle {
    id: root

    property string title: ""
    property Component trailing: null
    property real contentPadding: Metrics.panelPadding
    property real contentSpacing: Metrics.spacing.m
    property bool chromeless: false

    default property alias content: body.data

    color: root.chromeless ? "transparent" : Theme.surface
    radius: root.chromeless ? 0 : Metrics.radius.xl
    border.width: root.chromeless ? 0 : Metrics.hairline
    border.color: Theme.border

    implicitWidth: outer.implicitWidth + contentPadding * 2
    implicitHeight: outer.implicitHeight + contentPadding * 2

    Behavior on color { ColorAnimation { duration: Motion.fast } }
    Behavior on border.color { ColorAnimation { duration: Motion.fast } }

    ColumnLayout {
        id: outer
        anchors.fill: parent
        anchors.margins: root.contentPadding
        spacing: header.visible ? Metrics.spacing.m : 0

        RowLayout {
            id: header
            visible: root.title !== "" || root.trailing !== null
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            RFSectionLabel {
                text: root.title
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
            }

            Loader {
                sourceComponent: root.trailing
                Layout.alignment: Qt.AlignVCenter
            }
        }

        ColumnLayout {
            id: body
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: root.contentSpacing

            // A panel is a frame, and a frame that lets its own content
            // paint outside it is not one. Found by opening a real capture
            // (acceptance/analysis_experience_r2_implementation/compressible/):
            // a chart whose Layout.minimumHeight exceeded the body printed
            // its axis labels and caption straight across the panel BELOW
            // it, so two unrelated panels' text overlapped. Clipping turns
            // that failure from "silently wrong on a neighbour" into
            // "visibly cramped here", which is the panel's own problem to
            // solve and is findable in a screenshot.
            clip: true
        }
    }
}
