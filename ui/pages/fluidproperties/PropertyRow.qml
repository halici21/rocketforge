import QtQuick
import QtQuick.Layouts
import "../../theme"

/*
 * One property row, weighted by tier (primary/thermodynamic/transport).
 *
 * Every property in the vocabulary carries a PropertyStatus with one of
 * seven distinct reasons when it has no value (AVAILABLE, NOT_REQUESTED,
 * NOT_SUPPORTED, OUT_OF_RANGE, PHASE_UNSUPPORTED, TWO_PHASE_AMBIGUOUS,
 * PROVIDER_FAILED -- rocketforge/physics/fluids/types.py). This row shows
 * the exact reason text the service already formats, in full, for every
 * one of them -- never shortened to a generic "unavailable". A tier
 * changes type size, never whether the reason is legible.
 */
RowLayout {
    id: root

    property var row: null
    property string tier: "transport"   // hero | primary | thermodynamic | transport

    readonly property real valueSize: tier === "hero" ? Typography.readoutHero
                                    : tier === "primary" ? Typography.readoutLarge
                                    : tier === "thermodynamic" ? Typography.readoutMedium
                                    : Typography.readoutSmall
    readonly property real labelSize: tier === "hero" || tier === "primary"
                                    ? Typography.body : Typography.bodySmall

    Layout.fillWidth: true
    Layout.fillHeight: false
    Layout.topMargin: tier === "hero" ? Metrics.spacing.s
                    : tier === "primary" ? Metrics.spacing.xs : 0
    spacing: Metrics.spacing.s

    Text {
        Layout.preferredWidth: 190
        text: root.row ? root.row.label : ""
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: root.labelSize
        elide: Text.ElideRight
    }
    Text {
        Layout.preferredWidth: 170
        horizontalAlignment: Text.AlignRight
        text: root.row ? root.row.value : ""
        color: (root.row && root.row.available) ? Theme.text : Theme.textMuted
        font.family: Typography.mono
        font.pixelSize: root.valueSize
        font.weight: root.tier === "hero" || root.tier === "primary"
                     ? Typography.medium : Typography.regular
        elide: Text.ElideRight
    }
    Text {
        Layout.preferredWidth: 96
        text: root.row ? root.row.unit : ""
        color: Theme.textMuted
        font.family: Typography.mono
        font.pixelSize: Typography.meta
        elide: Text.ElideRight
    }
    Text {
        Layout.fillWidth: true
        visible: root.row && !root.row.available
        text: root.row ? root.row.status : ""
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        elide: Text.ElideRight
    }
}
