import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * A quick visual read of the few species that dominate the mixture.
 *
 * Horizontal bars, not a pie: an equilibrium chamber has twenty-eight species
 * spanning fifteen orders of magnitude, and a pie chart of that is a circle
 * with three visible slices and twenty-five invisible ones - unreadable
 * exactly where the scientific interest is.
 *
 * The table below remains the authoritative numerical view. This is an
 * orientation aid and shows only the largest few; it never replaces a number
 * with a picture.
 */
ColumnLayout {
    id: bars

    property int barCount: 6

    readonly property string basisLabel:
        Thermochemistry.compositionBasis === "mole" ? "mole fraction X"
                                                    : "mass fraction Y"

    // Read straight from the display model, so the bars and the table are the
    // same rows under the same display threshold - they cannot disagree.
    readonly property var leaders: {
        // `speciesShown` is a notifying property and `rowCount()` is a plain
        // method call, so naming it here is what makes this binding
        // re-evaluate when the model is rebuilt.
        var shown = Thermochemistry.speciesShown
        var condensed = Thermochemistry.condensedRows
        var model = Thermochemistry.compositionModel
        var column = Thermochemistry.compositionBasis === "mole" ? 2 : 3
        var out = []
        var rows = Math.min(bars.barCount, shown)
        for (var i = 0; i < rows; ++i) {
            out.push({
                name: String(model.data(model.index(i, 0), Qt.DisplayRole)),
                text: String(model.data(model.index(i, column), Qt.DisplayRole)),
                value: model.valueAt(i, column),
                condensed: condensed.indexOf(i) >= 0
            })
        }
        return out
    }

    readonly property real peak: leaders.length > 0 ? Math.max(leaders[0].value, 1e-30) : 1

    spacing: Metrics.spacing.xs
    visible: leaders.length > 0

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        RFSectionLabel { text: Notation.sectionRich("Largest " + bars.leaders.length + " by " + bars.basisLabel); textFormat: Notation.textFormat("Largest " + bars.leaders.length + " by " + bars.basisLabel) }
        Item { Layout.fillWidth: true }
        Text {
            text: "Bars are linear and relative to the largest. The table below is the "
                  + "authoritative view."
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    Repeater {
        model: bars.leaders

        delegate: RowLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            Text {
                Layout.preferredWidth: 76
                text: Notation.species(modelData.name)
                textFormat: Notation.speciesFormat(modelData.name)
                elide: Text.ElideRight
                clip: true              // RichText does not elide
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.meta
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 9

                Rectangle {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    height: 7
                    radius: 2
                    width: Math.max(1, parent.width * modelData.value / bars.peak)
                    // Condensed material in the secondary tone the Calculator
                    // uses for it too; the name's phase suffix says the same
                    // thing in words, so the distinction is never colour alone.
                    color: modelData.condensed ? Theme.textSecondary : Theme.accent
                    opacity: 0.8
                }
            }

            Text {
                Layout.preferredWidth: 96
                horizontalAlignment: Text.AlignRight
                text: modelData.text
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.meta
            }
        }
    }
}
