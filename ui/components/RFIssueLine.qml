import QtQuick
import QtQuick.Layouts
import "../theme"
import "../data"

/*
 * RFIssueLine - one reason a study cannot run yet.
 *
 * `text` is the controller's message, shown unchanged. When the reason is an
 * upstream result that is missing, stale, refused or mismatched (`code` is in
 * Navigation.upstreamPageOfIssue), a quiet button opens that page. The button
 * only navigates: it never runs or changes anything upstream.
 *
 * `showLink` lets a list show one button per upstream page rather than one per
 * line when several reasons point at the same page; `firstForPage()` is the
 * usual binding.
 */
RowLayout {
    id: line

    property string text: ""
    property string code: ""
    property bool showLink: true

    signal openRequested(int index)

    readonly property int targetIndex: Navigation.upstreamPageOf(code)

    // Whether no earlier issue in `issues` (a controller's list) points at the
    // same upstream page as the one at `index`.
    function firstForPage(issues, index) {
        if (!issues || !issues[index])
            return true
        var target = Navigation.upstreamPageOf(issues[index].code)
        for (var i = 0; i < index; ++i)
            if (issues[i] && Navigation.upstreamPageOf(issues[i].code) === target)
                return false
        return true
    }

    Layout.fillWidth: true
    spacing: Metrics.spacing.s

    Text {
        Layout.fillWidth: true
        text: line.text
        color: Theme.warning
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        wrapMode: Text.WordWrap
    }

    RFButton {
        objectName: "issueLink"
        visible: line.showLink && line.targetIndex >= 0
        Layout.alignment: Qt.AlignTop
        variant: "quiet"
        compact: true
        text: line.targetIndex >= 0 ? "Open " + Navigation.items[line.targetIndex].label : ""
        onClicked: line.openRequested(line.targetIndex)
    }
}
