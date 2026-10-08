import QtQuick
import RocketForge 1.0
import "../components"

/*
 * Tank Pressurization - regulated stored gas or blowdown per branch, with a
 * perfect gas (SYS-4). The pressurant's gas constant, the expansion exponent
 * and every pressure and temperature are stated; none is assumed. The
 * required tank pressure is stated or taken from the injector ledger.
 * Autogenous and warm-gas pressurization are recorded as intent only.
 * Nothing is computed until Compute is pressed.
 */
Item {
    id: page

    RFSystemWorkspace {
        anchors.fill: parent
        controller: TankPressurization
        prefix: "pressurization"
        title: "Tank Pressurization"
        subtitle: "Pressurant mass and bottle volume, or blowdown pressure evolution, and the margin over each branch's required tank pressure"
        scopeText: "Perfect gas · autogenous and warm gas are intent only"
        upstreamText: "From Propellant Management: compute it first."
        emptyBody: "State each branch's pressurization mode, pressurant and states, then press Compute. Nothing is computed until you do."
    }
}
