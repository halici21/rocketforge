import QtQuick
import RocketForge 1.0
import "../../components"

/*
 * The Reference Engines Inspector content: provenance, not results.
 *
 * One reading at a time, each prepared by the ReferenceEngines controller: the
 * configuration (lineage, operating points, cited sources), one assertion (as
 * printed, its value kind, scope, every recorded condition -- an unknown one
 * stays "Unknown" -- its locator and its source's rights), one source
 * (authority and shipping, kept apart), one capability (its gaps and caveats),
 * or the topology graph, a component or a connection. The layout is the shared
 * RFProvenanceInspector.
 */
RFProvenanceInspector {
    id: root

    readout: ReferenceEngines.inspectionReadout
    namePrefix: "engine"
    recordAvailable: root.hasReadout && root.readout.kind !== "configuration"
    recordTooltip: "Back to the configuration's identity and sources"
    onRecordRequested: ReferenceEngines.inspectRecord()
    emptyText: "Select an engine configuration in the library to inspect it."
    footerText: "Shipped reference evidence, shown as recorded. Nothing here is computed, converted, "
                + "edited or solved, and no record drives a design or a solver."

    // Shown for an assertion with a source, exactly when its one button is.
    extraToolsShown: root.hasReadout && root.readout.kind === "assertion" && root.readout.sourceId !== undefined
    extraTools: RFToolButton {
        objectName: "engineInspectSource"
        text: "Source ›"
        tooltip: "This value's source: its authority and its rights, separately"
        onClicked: ReferenceEngines.inspectSource(root.readout.sourceId)
    }
}
