import QtQuick
import RocketForge 1.0
import "../components"

/*
 * Feed Network - each branch's liquid line from the tank outlet to the
 * injector inlet as components in series (SYS-5): pipes with the Darcy
 * friction factor, local losses K ρv²/2, stated losses and static head.
 * The injector-inlet requirement comes from the injector ledger without
 * counting its feed-line and valve terms twice. Unknown components stay
 * unresolved. Nothing is computed until Compute is pressed.
 */
Item {
    id: page

    RFSystemWorkspace {
        anchors.fill: parent
        controller: FeedNetwork
        prefix: "feed"
        title: "Feed Network"
        subtitle: "Pressure losses from tank outlet to injector inlet and the margin of each tank pressure over the requirement"
        scopeText: "Single-phase, steady · no cavitation, transients, pumps or cooling channels"
        upstreamText: "From Tank Pressurization and Injector & Feed Pressure: compute both first, on the same sizing."
        emptyBody: "Add each branch's components from the tank outlet to the injector inlet, state the liquid and the LIQ-6 term assignments, then press Compute. Nothing is computed until you do."
    }
}
