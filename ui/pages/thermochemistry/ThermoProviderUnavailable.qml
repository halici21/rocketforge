import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * What the workspace looks like with no chemistry provider installed.
 *
 * A first-class screen, not an error page. The base RocketForge environment
 * deliberately ships without a chemistry library, and the compressible
 * workspaces have no chemistry dependency and must never acquire one.
 *
 * The one rule this screen exists to keep: it shows no number. No defaults, no
 * placeholders shaped like results, no values quietly drawn from a table
 * nobody chose. It says what is missing, what would provide it, and what still
 * works.
 */
Item {
    id: view

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - Metrics.spacing.h2 * 2, 620)
        spacing: Metrics.spacing.l

        RFEmptyState {
            Layout.fillWidth: true
            tag: "NO PROVIDER"
            title: "Thermochemistry provider unavailable"
            body: Thermochemistry.providerLabel + " is not available in this environment, "
                  + "so no chamber equilibrium can be solved. Nothing is estimated in its "
                  + "place and no values are shown."
        }

        RFPanel {
            Layout.fillWidth: true
            title: "Detail"
            contentSpacing: Metrics.spacing.s

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.m

                Text {
                    Layout.preferredWidth: 108
                    text: "Status"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
                Text {
                    Layout.fillWidth: true
                    text: Thermochemistry.providerStatus
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.bodySmall
                }
            }

            RowLayout {
                Layout.fillWidth: true
                visible: Thermochemistry.providerDetail !== ""
                spacing: Metrics.spacing.m

                Text {
                    Layout.preferredWidth: 108
                    text: "Reported"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
                Text {
                    Layout.fillWidth: true
                    text: Thermochemistry.providerDetail
                    wrapMode: Text.WordWrap
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
            }

            RowLayout {
                Layout.fillWidth: true
                visible: Thermochemistry.providerRemedy !== ""
                spacing: Metrics.spacing.m

                Text {
                    Layout.preferredWidth: 108
                    text: "To enable"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
                Text {
                    Layout.fillWidth: true
                    text: Thermochemistry.providerRemedy
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
            }
        }

        RFPanel {
            Layout.fillWidth: true
            title: "Still available"
            contentSpacing: Metrics.spacing.s

            Text {
                Layout.fillWidth: true
                text: "Every compressible flow workspace works unchanged. Those pages have "
                      + "no chemistry dependency, and installing a chemistry library is not "
                      + "a prerequisite for any of them."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
        }

        RFButton {
            Layout.alignment: Qt.AlignHCenter
            text: "Re-check provider"
            onClicked: Thermochemistry.refreshProvider()
        }
    }
}
