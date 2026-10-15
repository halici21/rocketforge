import QtQuick
import RocketForge 1.0
import "../../components"

/*
 * The Propulsion Database's Inspector content: provenance, not results.
 *
 * Two readings, both prepared by the controller from the stored record: the
 * record itself (identity, formulation, each source with its locator, access,
 * shipping and rights, and the record's notes), or one stored field (its exact
 * stored value, the unit as printed, how it entered the record, where it is
 * printed, and the source) -- or, for a missing field, its reason. The layout
 * is the shared RFProvenanceInspector.
 */
RFProvenanceInspector {
    id: root

    readout: PropulsionEvidence.inspectionReadout
    namePrefix: "evidence"
    recordAvailable: root.hasReadout && root.readout.kind === "datum"
    recordTooltip: "Back to the record's sources and notes"
    onRecordRequested: PropulsionEvidence.inspectRecord()
    emptyText: "Select a record in the library to inspect its sources."
    footerText: "Stored evidence, shown as stored. Nothing here is computed, converted or solved."
}
