import QtQuick
import RocketForge 1.0
import "../components"

/*
 * Propellant Inventory - how much propellant each branch must load for the
 * engine's burn (SYS-1). Usable = ṁ × burn time at the sized flows and the
 * requirement's burn time; the residual comes from a stated expulsion
 * efficiency or residual mass; a reserve, allowances and boil-off are stated,
 * not applicable, or unresolved. Nothing is computed until Compute is pressed.
 */
Item {
    id: page

    RFSystemWorkspace {
        anchors.fill: parent
        controller: PropellantInventory
        prefix: "inventory"
        title: "Propellant Inventory"
        subtitle: "Usable, available, residual and loaded propellant per branch at the sized flows and the requirement's burn time"
        scopeText: "Mass budget · no tanks, pressurization or cycle flows"
        upstreamText: "From Thrust Chamber Sizing and the Engine Requirement: size a selected trade candidate and state a burn time first."
        emptyBody: "State how each branch's unavailable propellant, reserve and allowances are given, then press Compute. Nothing is computed until you do."
    }
}
