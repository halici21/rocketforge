import QtQuick
import RocketForge 1.0
import "../components"

/*
 * Tank Geometry & Packaging - the internal volume and dimensions each
 * branch's tank needs to hold its loaded propellant (SYS-2). The density,
 * the ullage, the shape and the one dimension that fixes it are stated; no
 * shape, diameter or optimum is chosen, and a geometry that cannot hold the
 * volume is refused. Internal geometry only. Nothing is computed until
 * Compute is pressed.
 */
Item {
    id: page

    RFSystemWorkspace {
        anchors.fill: parent
        controller: PropellantTanks
        prefix: "tanks"
        title: "Tank Geometry & Packaging"
        subtitle: "Liquid, ullage and tank volume and the internal geometry of each branch's tank"
        scopeText: "Internal geometry · no wall, mass, insulation or common bulkhead"
        upstreamText: "From Propellant Inventory: compute a complete inventory first. An unresolved load has no volume."
        emptyBody: "State each tank's density, ullage, shape and the dimension that fixes it, then press Compute. Nothing is computed until you do."
    }
}
