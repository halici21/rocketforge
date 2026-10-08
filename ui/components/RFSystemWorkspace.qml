import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

/*
 * RFSystemWorkspace - the one workspace every propulsion-system page (SYS gates)
 * is laid out with.
 *
 * It renders a SYS controller (system_study_controller.py): the upstream result it reads, the
 * stated inputs as sections of fields, every reason the study cannot be
 * computed yet, Compute, and the result -- both branches side by side with
 * their grouped quantities, named states, ledger and series, then the
 * totals, advisories, model and provenance.
 *
 * Nothing is computed until Compute is pressed. Every number, label, unit
 * and reason comes from the controller; this file lays them out. Unresolved
 * values are shown as such and never as zero.
 *
 * objectNames: <prefix>Status, <prefix>Run, <prefix>Issue, <prefix>Basis,
 * <prefix>Message, <prefix>Scroll, <prefix>_<field key> for each input,
 * <prefix>_<branch>_Value_<key>, <prefix>_<branch>_labelValue_<key>,
 * <prefix>_<branch>_ledgerValue_<key>, <prefix>TotalValue_<key>.
 */
Item {
    id: ws

    property var controller
    property string prefix: "study"
    property string title: ""
    property string subtitle: ""
    property string scopeText: ""
    property string upstreamText: ""
    property string emptyBody: ""

    // Read once per change, not once per field binding.
    readonly property var sections: controller ? controller.inputSections : []

    function indexOfKey(options, key) {
        for (var i = 0; i < options.length; ++i)
            if (options[i].key === key) return i
        return 0
    }
    function labels(options) {
        return options.map(function (o) { return o.label })
    }

    component Note: Text {
        Layout.fillWidth: true
        visible: text !== ""
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        wrapMode: Text.WordWrap
    }

    component KeyValue: RowLayout {
        id: kv
        property string label
        property string value
        property string itemName: ""
        Layout.fillWidth: true
        spacing: Metrics.spacing.s
        Text {
            Layout.preferredWidth: 130
            text: kv.label
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        Text {
            objectName: kv.itemName
            Layout.fillWidth: true
            text: kv.value
            color: Theme.text
            font.family: Typography.mono
            font.pixelSize: Typography.meta
            wrapMode: Text.WordWrap
        }
    }

    // One quantity row: label, value, unit; the note or the reason on hover.
    component ValueRow: Item {
        id: line
        property var row
        property string prefix: ""
        Layout.fillWidth: true
        implicitHeight: 24
        HoverHandler { id: lineHover }
        RFTooltip {
            visible: lineHover.hovered && text !== ""
            text: line.row.reason !== "" ? line.row.reason : line.row.note
        }
        Text {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - 190
            text: line.row.label
            elide: Text.ElideRight
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        Text {
            objectName: line.prefix + line.row.key
            anchors.right: unitText.left
            anchors.rightMargin: Metrics.spacing.s
            anchors.verticalCenter: parent.verticalCenter
            width: Math.min(implicitWidth, parent.width * 0.5)
            horizontalAlignment: Text.AlignRight
            elide: Text.ElideLeft
            text: line.row.value
            color: line.row.reason !== "" || line.row.status === "unresolved"
                   ? Theme.textMuted : Theme.text
            font.family: Typography.mono
            font.pixelSize: Typography.meta
        }
        Text {
            id: unitText
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            width: 44
            text: line.row.unit
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    component Heading: Text {
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.weight: Font.DemiBold
    }

    // One section of stated inputs. Fixed counts: the delegates are not
    // recreated when a value changes, only when a row is added or removed.
    component InputSection: ColumnLayout {
        id: sec
        property int sectionIndex
        readonly property var s: ws.sections[sectionIndex]
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignTop
        Layout.columnSpan: s && s.wide ? 2 : 1
        spacing: Metrics.spacing.s

        RFSectionLabel { text: sec.s ? sec.s.title : "" }
        Note { text: sec.s ? sec.s.note : "" }
        GridLayout {
            Layout.fillWidth: true
            columns: width > 560 ? 2 : 1
            columnSpacing: Metrics.spacing.m
            rowSpacing: Metrics.spacing.s
            Repeater {
                model: sec.s ? sec.s.fields.length : 0
                delegate: ColumnLayout {
                    id: cell
                    required property int index
                    readonly property var f: sec.s.fields[index]
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    Layout.alignment: Qt.AlignTop
                    visible: f.visible
                    spacing: 2
                    RFNumberField {
                        objectName: cell.f.kind === "number" ? ws.prefix + "_" + cell.f.key : ""
                        Layout.fillWidth: true
                        visible: cell.f.kind === "number"
                        label: cell.f.label
                        unit: cell.f.unit
                        showSteppers: false
                        text: cell.f.text
                        onEdited: ws.controller.setField(cell.f.key, text)
                    }
                    RFComboBox {
                        objectName: cell.f.kind === "choice" ? ws.prefix + "_" + cell.f.key : ""
                        Layout.fillWidth: true
                        visible: cell.f.kind === "choice"
                        label: cell.f.label
                        model: ws.labels(cell.f.options)
                        currentIndex: ws.indexOfKey(cell.f.options, cell.f.value)
                        onActivated: function (i) {
                            ws.controller.setChoice(cell.f.key, cell.f.options[i].key)
                        }
                    }
                    RFTextField {
                        objectName: cell.f.kind === "text" ? ws.prefix + "_" + cell.f.key : ""
                        Layout.fillWidth: true
                        visible: cell.f.kind === "text"
                        label: cell.f.label
                        text: cell.f.text
                        onEdited: ws.controller.setText(cell.f.key, text)
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: cell.f.kind === "note"
                        text: cell.f.label
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Note { text: cell.f.note }
                }
            }
        }
        Flow {
            Layout.fillWidth: true
            visible: sec.s && sec.s.actions.length > 0
            spacing: Metrics.spacing.s
            Repeater {
                model: sec.s ? sec.s.actions : []
                delegate: RFButton {
                    required property var modelData
                    objectName: ws.prefix + "_action_" + modelData.key + "_" + modelData.argument
                    text: modelData.label
                    variant: "quiet"
                    compact: true
                    onClicked: ws.controller.invoke(modelData.key, modelData.argument)
                }
            }
        }
    }

    // One branch's result.
    component BranchResult: ColumnLayout {
        id: res
        property var view
        readonly property string p: ws.prefix + "_" + view.branch + "_"
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignTop
        spacing: 2

        RFSectionLabel { text: res.view.title }
        Text {
            objectName: res.p + "refusal"
            Layout.fillWidth: true
            visible: !res.view.ok && res.view.message !== ""
            text: res.view.message
            color: Theme.warning
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            wrapMode: Text.WordWrap
        }
        Heading { text: "State"; visible: res.view.labels.length > 0 }
        Repeater {
            model: res.view.labels
            delegate: ValueRow {
                required property var modelData
                prefix: res.p + "labelValue_"
                row: modelData
            }
        }
        Repeater {
            model: res.view.groups
            delegate: ColumnLayout {
                id: group
                required property var modelData
                Layout.fillWidth: true
                spacing: 2
                Heading { text: group.modelData.title }
                Repeater {
                    model: group.modelData.rows
                    delegate: ValueRow {
                        required property var modelData
                        prefix: res.p + "Value_"
                        row: modelData
                    }
                }
            }
        }
        Heading { text: "Ledger"; visible: res.view.ledger.length > 0 }
        Repeater {
            model: res.view.ledger
            delegate: ValueRow {
                required property var modelData
                prefix: res.p + "ledgerValue_"
                row: modelData
            }
        }
        readonly property var seriesHeaders: res.view.series && res.view.series.headers
                                             ? res.view.series.headers : []
        readonly property var seriesRows: res.view.series && res.view.series.rows
                                          ? res.view.series.rows : []
        Heading { text: "Evolution"; visible: res.seriesRows.length > 0 }
        GridLayout {
            Layout.fillWidth: true
            visible: res.seriesRows.length > 0
            columns: Math.max(1, res.seriesHeaders.length)
            columnSpacing: Metrics.spacing.m
            rowSpacing: 2
            Repeater {
                model: res.seriesHeaders
                delegate: Text {
                    required property var modelData
                    Layout.fillWidth: true
                    text: modelData
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    wrapMode: Text.WordWrap
                }
            }
            Repeater {
                model: res.seriesRows.reduce(function (a, r) { return a.concat(r) }, [])
                delegate: Text {
                    required property var modelData
                    Layout.fillWidth: true
                    text: modelData
                    color: Theme.text
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: ws.title
            subtitle: ws.subtitle

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: ws.scopeText
                        showDot: false
                    }
                    RFStatusChip {
                        objectName: ws.prefix + "Status"
                        anchors.verticalCenter: parent.verticalCenter
                        text: ws.controller.statusLabel
                        tone: ws.controller.statusTone
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            Flickable {
                id: mainScroll
                objectName: ws.prefix + "Scroll"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: width
                contentHeight: main.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: RFScrollBar {}

                ColumnLayout {
                    id: main
                    width: mainScroll.width - Metrics.spacing.m
                    spacing: Metrics.spacing.m

                    RFPanel {
                        Layout.fillWidth: true
                        title: "Basis and stated inputs"

                        Note {
                            visible: !ws.controller.hasBasis
                            text: ws.upstreamText
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: width > 760 ? 2 : 1
                            columnSpacing: Metrics.spacing.l
                            rowSpacing: Metrics.spacing.xs
                            Repeater {
                                model: ws.controller.basisRows
                                delegate: KeyValue {
                                    required property var modelData
                                    itemName: ws.prefix + "Basis"
                                    label: modelData.label
                                    value: modelData.value
                                }
                            }
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: width > 900 ? 2 : 1
                            columnSpacing: Metrics.spacing.xl
                            rowSpacing: Metrics.spacing.l
                            Repeater {
                                model: ws.sections.length
                                delegate: InputSection {
                                    required property int index
                                    sectionIndex: index
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            RFButton {
                                objectName: ws.prefix + "Run"
                                text: "Compute"
                                variant: "primary"
                                enabled: ws.controller.canCompute
                                onClicked: ws.controller.compute()
                            }
                        }
                        Repeater {
                            model: ws.controller.issues
                            delegate: Text {
                                objectName: ws.prefix + "Issue"
                                required property var modelData
                                Layout.fillWidth: true
                                text: modelData.message
                                color: Theme.warning
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                                wrapMode: Text.WordWrap
                            }
                        }
                        Note { objectName: ws.prefix + "Message"; text: ws.controller.message }
                    }

                    RFPanel {
                        Layout.fillWidth: true
                        title: "Branches"

                        RFEmptyState {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 160
                            visible: !ws.controller.hasResult
                            title: "Not computed yet"
                            body: ws.emptyBody
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            visible: ws.controller.hasResult
                            columns: width > 900 ? 2 : 1
                            columnSpacing: Metrics.spacing.xl
                            rowSpacing: Metrics.spacing.l
                            Repeater {
                                model: ws.controller.resultBranches
                                delegate: BranchResult {
                                    required property var modelData
                                    view: modelData
                                }
                            }
                        }

                        RFSectionLabel {
                            text: "Totals"
                            visible: ws.controller.totalRows.length > 0
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Repeater {
                                model: ws.controller.totalRows
                                delegate: ValueRow {
                                    required property var modelData
                                    prefix: ws.prefix + "TotalValue_"
                                    row: modelData
                                }
                            }
                        }
                    }
                }
            }

            RFPanel {
                Layout.preferredWidth: 380
                Layout.fillHeight: true
                title: "Model and provenance"

                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: width
                    contentHeight: side.implicitHeight
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: RFScrollBar {}

                    ColumnLayout {
                        id: side
                        width: parent.width - Metrics.spacing.m
                        spacing: Metrics.spacing.m

                        Note {
                            visible: !ws.controller.hasResult
                            text: "Shown with a result: advisories, the model and where "
                                  + "every upstream number came from."
                        }

                        RFSectionLabel {
                            text: "Advisories"
                            visible: ws.controller.noteRows.length > 0
                        }
                        Repeater {
                            model: ws.controller.noteRows
                            delegate: Note {
                                required property var modelData
                                objectName: ws.prefix + "Note"
                                text: modelData
                            }
                        }

                        RFDivider { Layout.fillWidth: true; visible: ws.controller.hasResult }
                        RFSectionLabel { text: "Model"; visible: ws.controller.hasResult }
                        Repeater {
                            model: ws.controller.modelAssumptions
                            delegate: Note {
                                required property var modelData
                                text: "· " + modelData
                            }
                        }

                        RFDivider { Layout.fillWidth: true; visible: ws.controller.hasResult }
                        RFSectionLabel { text: "Provenance"; visible: ws.controller.hasResult }
                        Repeater {
                            model: ws.controller.provenanceRows
                            delegate: Note {
                                required property var modelData
                                text: modelData.label + ": " + modelData.value
                            }
                        }
                    }
                }
            }
        }
    }
}
