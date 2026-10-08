import QtQuick
import RocketForge 1.0
import "../components"

/*
 * Propellant Management - what keeps liquid at each tank outlet, and the
 * liquid and gas volumes through the burn (SYS-3). The mode, the
 * acceleration environment and the settling intent are stated; outlet
 * coverage is shown as a declaration with its basis, never a demonstration.
 * The expulsion efficiency is the inventory's. No slosh dynamics are
 * modelled. Nothing is computed until Compute is pressed.
 */
Item {
    id: page

    RFSystemWorkspace {
        anchors.fill: parent
        controller: PropellantManagement
        prefix: "management"
        title: "Propellant Management"
        subtitle: "Management intent per branch, outlet-coverage declaration and the liquid and gas volumes through the burn"
        scopeText: "Intent and bookkeeping · slosh dynamics not modelled"
        upstreamText: "From Propellant Inventory and Tank Geometry & Packaging: compute both first."
        emptyBody: "State how each branch keeps liquid at its outlet and in what acceleration environment, then press Compute. Nothing is computed until you do."
    }
}
