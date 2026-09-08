import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"
import "../components"
import "../data"
import "model"
import "workspaces"
import "dialogs"

/*
 * EngineWorkspace - the engine design mode.
 *
 * It owns the arrangement (sidebar, documents, inspector, bottom panel) and
 * the set of open documents. Everything about the engine itself lives in
 * EngineModel, so this file stays a shell: it routes selection, opens
 * workspaces and passes the canvas around.
 *
 * Documents stay instantiated once opened, which is what preserves canvas
 * pan, zoom and workspace state when switching tabs.
 *
 * The two side panels fold away. Between a project tree, a configuration rail,
 * a drawing and an inspector, the engineering content is the fourth claimant on
 * a 1366 px display and loses; being able to drop the two that carry context
 * rather than work is what makes the narrow case usable. Their state is held
 * here rather than in the panels so it survives switching documents.
 */
Item {
    id: workspace

    signal analysisModeRequested(int pageIndex)

    // ---- panel state -----------------------------------------------------
    property bool projectCollapsed: false
    property bool inspectorCollapsed: false

    // Focus mode remembers what it hid, so leaving it restores the panels the
    // user actually had open rather than opening both.
    property bool focusMode: false
    property var focusRestore: null

    function toggleFocusMode() {
        if (focusMode) {
            if (focusRestore) {
                projectCollapsed = focusRestore.project
                inspectorCollapsed = focusRestore.inspector
                bottomPanel.expanded = focusRestore.bottom
            }
            focusMode = false
            return
        }
        focusRestore = { project: projectCollapsed,
                         inspector: inspectorCollapsed,
                         bottom: bottomPanel.expanded }
        projectCollapsed = true
        inspectorCollapsed = true
        bottomPanel.expanded = false
        focusMode = true
    }

    // Reopening a panel by hand is a way out of focus mode too.
    onProjectCollapsedChanged: if (!projectCollapsed) focusMode = false
    onInspectorCollapsedChanged: if (!inspectorCollapsed) focusMode = false

    property var documents: [{ id: "layout", kind: "layout", title: "Engine Layout",
                               nodeId: "", glyph: "" }]
    property int currentDocument: 0

    readonly property var breadcrumbParts: {
        EngineModel.graphRevision
        var doc = documents[currentDocument]
        if (!doc)
            return [EngineModel.engineName]
        var title = doc.nodeId ? EngineModel.nodeName(doc.nodeId) : doc.title
        return [EngineModel.engineName, title]
    }

    property Item layoutDocument: null
    readonly property Item canvas: layoutDocument ? layoutDocument.canvas : null

    /* What the inspector needs in order to know where the user is standing.
     * "layout" means the architecture is on screen and navigating into a
     * component is a real move; "component" means one already fills the page. */
    readonly property var activeDocument: documents[currentDocument]
    readonly property string documentKind: activeDocument && activeDocument.nodeId
                                           ? "component" : "layout"
    readonly property string documentNodeId: activeDocument && activeDocument.nodeId
                                             ? activeDocument.nodeId : ""

    // =====================================================================
    // documents
    // =====================================================================

    function documentIndex(id) {
        for (var i = 0; i < documents.length; ++i) {
            if (documents[i].id === id)
                return i
        }
        return -1
    }

    function openComponentWorkspace(nodeId) {
        var node = EngineModel.node(nodeId)
        if (!node)
            return
        var existing = documentIndex("node:" + nodeId)
        if (existing >= 0) {
            currentDocument = existing
            return
        }
        var definition = ComponentRegistry.definition(node.type)
        var next = documents.slice()
        next.push({
            id: "node:" + nodeId,
            kind: definition ? definition.workspace : "placeholder",
            title: node.name,
            nodeId: nodeId,
            glyph: definition ? definition.glyph : ""
        })
        documents = next
        currentDocument = next.length - 1
        EngineModel.selectNode(nodeId, false)
    }

    function closeDocument(index) {
        if (index <= 0 || index >= documents.length)
            return
        var next = documents.slice()
        next.splice(index, 1)
        documents = next
        if (currentDocument >= next.length)
            currentDocument = next.length - 1
        else if (currentDocument > index)
            currentDocument -= 1
    }

    // A component workspace cannot outlive its component.
    Connections {
        target: EngineModel
        function onGraphRevisionChanged() {
            var next = workspace.documents.filter(function (doc) {
                return doc.nodeId === "" || EngineModel.node(doc.nodeId) !== null
            })
            if (next.length !== workspace.documents.length) {
                workspace.documents = next
                if (workspace.currentDocument >= next.length)
                    workspace.currentDocument = next.length - 1
            }
        }
    }

    function handleRename(nodeId) {
        EngineModel.selectNode(nodeId, false)
        inspector.focusName()
    }

    /* Bring the architecture back with one component picked out. Used by the
     * problems list and by the inspector way back out of a component
     * workspace: both refer to something that only exists on the canvas, so
     * both have to put the canvas on screen first. */
    function showInLayout(nodeId) {
        currentDocument = 0
        if (nodeId) {
            EngineModel.selectNode(nodeId, false)
            if (canvas)
                canvas.focusNode(nodeId)
        }
    }

    /* Opening a component tab hands the inspector that component; returning to
     * the tab should do the same, or the panel would go on describing whatever
     * was last clicked somewhere else. */
    onCurrentDocumentChanged: {
        var doc = documents[currentDocument]
        if (doc && doc.nodeId && !EngineModel.isNodeSelected(doc.nodeId))
            EngineModel.selectNode(doc.nodeId, false)
    }

    // =====================================================================
    // commands
    // =====================================================================

    function runCommand(id) {
        switch (id) {
        case "engine.demo":
            EngineModel.loadDemo()
            currentDocument = 0
            if (canvas)
                canvas.fitAll()
            return
        case "engine.new":
            newEngineDialog.open()
            return
        case "engine.fit":
            currentDocument = 0
            if (canvas)
                canvas.fitAll()
            return
        case "engine.fitselection":
            currentDocument = 0
            if (canvas)
                canvas.fitSelection()
            return
        case "engine.problems":
            bottomPanel.open(0)
            return
        case "view.focus":
            workspace.toggleFocusMode()
            return
        case "view.project":
            workspace.projectCollapsed = !workspace.projectCollapsed
            return
        case "view.inspector":
            workspace.inspectorCollapsed = !workspace.inspectorCollapsed
            return
        case "open.layout":
            currentDocument = 0
            return
        case "mode.analysis":
            workspace.analysisModeRequested(-1)
            return
        case "page.isentropic":
            workspace.analysisModeRequested(Navigation.indexOfKey("isentropic"))
            return
        case "page.nozzlelab":
            workspace.analysisModeRequested(Navigation.indexOfKey("nozzlelab"))
            return
        case "page.equations":
            workspace.analysisModeRequested(Navigation.indexOfKey("equations"))
            return
        }
        if (id.indexOf("add.") === 0 && canvas) {
            currentDocument = 0
            canvas.addComponentAtCentre(id.substring(4))
        }
    }

    Shortcut {
        sequence: "Ctrl+K"
        onActivated: commandPalette.open()
    }

    Shortcut {
        sequence: "Ctrl+Shift+F"
        onActivated: workspace.toggleFocusMode()
    }

    // =====================================================================
    // layout
    // =====================================================================

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            PanelRail {
                Layout.fillHeight: true
                Layout.preferredWidth: Metrics.collapsedRailWidth
                visible: workspace.projectCollapsed && !projectPanel.transitioning
                side: "left"
                label: "Project"
                onRestore: workspace.projectCollapsed = false
            }

            SplitView {
                id: split
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: Qt.Horizontal

                handle: Rectangle {
                    implicitWidth: 5
                    color: "transparent"

                    Rectangle {
                        anchors.centerIn: parent
                        width: Metrics.hairline
                        height: parent.height
                        color: SplitHandle.pressed ? Theme.accent
                             : SplitHandle.hovered ? Theme.borderStrong
                             : Theme.divider
                        Behavior on color { ColorAnimation { duration: Motion.fast } }
                    }
                }

                CollapsiblePanel {
                    id: projectPanel
                    collapsed: workspace.projectCollapsed
                    expandedWidth: Metrics.projectPanelWidth
                    minimumWidth: Metrics.projectPanelMin
                    maximumWidth: Metrics.projectPanelMax

                    EngineSidebar {
                        id: sidebar
                        anchors.fill: parent
                        canvas: workspace.canvas
                        dragLayer: dragLayer
                        onCollapseRequested: workspace.projectCollapsed = true
                    }
                }

                Item {
                    SplitView.fillWidth: true
                    SplitView.minimumWidth: 380

                    WorkspaceTabs {
                    id: tabs
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.right: parent.right
                    documents: workspace.documents
                    currentIndex: workspace.currentDocument
                    focusMode: workspace.focusMode
                    onSelected: function (index) { workspace.currentDocument = index }
                    onClosed: function (index) { workspace.closeDocument(index) }
                    onFocusModeToggled: workspace.toggleFocusMode()
                }

                StackLayout {
                    anchors.top: tabs.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    currentIndex: workspace.currentDocument

                    Repeater {
                        model: workspace.documents

                        delegate: Loader {
                            id: documentLoader
                            required property var modelData

                            sourceComponent: modelData.kind === "layout" ? layoutComponent
                                           : modelData.kind === "injector" ? injectorComponent
                                           : modelData.kind === "nozzle" ? nozzleComponent
                                           : placeholderComponent

                            onLoaded: {
                                if (modelData.kind === "layout") {
                                    workspace.layoutDocument = item
                                    item.componentWorkspaceRequested.connect(
                                                workspace.openComponentWorkspace)
                                    item.renameRequested.connect(workspace.handleRename)
                                } else {
                                    item.nodeId = modelData.nodeId
                                }
                            }
                        }
                    }
                }
            }

                CollapsiblePanel {
                    id: inspectorPanel
                    collapsed: workspace.inspectorCollapsed
                    expandedWidth: Metrics.inspectorWidth
                    minimumWidth: Metrics.inspectorMin
                    maximumWidth: Metrics.inspectorMax

                    EngineInspector {
                        id: inspector
                        anchors.fill: parent
                        contextKind: workspace.documentKind
                        contextNodeId: workspace.documentNodeId
                        onComponentWorkspaceRequested: function (nodeId) {
                            workspace.openComponentWorkspace(nodeId)
                        }
                        onEngineLayoutRequested: function (nodeId) {
                            workspace.showInLayout(nodeId)
                        }
                        onCollapseRequested: workspace.inspectorCollapsed = true
                        onNewEngineRequested: newEngineDialog.open()
                        onDemoRequested: workspace.runCommand("engine.demo")
                    }
                }
            }

            PanelRail {
                Layout.fillHeight: true
                Layout.preferredWidth: Metrics.collapsedRailWidth
                visible: workspace.inspectorCollapsed && !inspectorPanel.transitioning
                side: "right"
                label: "Inspector"
                onRestore: workspace.inspectorCollapsed = false
            }
        }

        BottomPanel {
            id: bottomPanel
            Layout.fillWidth: true
            canvas: workspace.canvas
            onFocusRequested: function (nodeId) { workspace.showInLayout(nodeId) }
        }
    }

    // ---- document components --------------------------------------------

    Component { id: layoutComponent; EngineLayoutDocument {} }
    Component { id: injectorComponent; InjectorWorkspace {} }
    Component { id: nozzleComponent; NozzleWorkspace {} }
    Component { id: placeholderComponent; PlaceholderComponentWorkspace {} }

    // ---- overlays --------------------------------------------------------

    // Palette drags are parented here so they can travel over the canvas.
    Item {
        id: dragLayer
        anchors.fill: parent
        z: 100
    }

    NewEngineDialog {
        id: newEngineDialog
        onCreated: function (name, architecture) {
            EngineModel.newProject(name, architecture)
            workspace.currentDocument = 0
            if (workspace.canvas)
                workspace.canvas.fitAll()
        }
    }

    CommandPalette {
        id: commandPalette
        onCommandInvoked: function (commandId) { workspace.runCommand(commandId) }
    }
}
