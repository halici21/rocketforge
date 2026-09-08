pragma Singleton
import QtQuick
import QtQml.Models

/*
 * EngineModel - the editor-level graph of the engine architecture.
 *
 * This is layer one of the eventual three:
 *
 *     UI graph model  ->  engineering configuration  ->  solver
 *
 * It stores what the user has drawn: which components exist, where they sit,
 * and which ports are joined. It deliberately contains no engineering
 * behaviour - no properties are propagated along a connection, nothing is
 * balanced, nothing is solved. Component metadata (ports, geometry, default
 * placeholder rows) comes from ComponentRegistry; per-node placeholder text
 * lives in each node's `meta` role so a future configuration layer can replace
 * it without touching the graph.
 *
 * Two revision counters exist because QML cannot track reads inside a
 * ListModel: bindings that depend on positions read `geometryRevision`, and
 * bindings that depend on the graph shape read `graphRevision`.
 */
QtObject {
    id: model

    // ---- project ---------------------------------------------------------
    property string engineName: "Engine-01"
    property string architecture: "Gas generator"
    property string propellants: "LOX / CH₄"
    property string environment: "Vacuum"

    // ---- graph -----------------------------------------------------------
    readonly property ListModel nodes: ListModel { dynamicRoles: true }
    readonly property ListModel connections: ListModel { dynamicRoles: true }

    property int geometryRevision: 0
    property int graphRevision: 0

    // ---- selection -------------------------------------------------------
    property string selectionKind: "none"      // none | node | connection
    property string selectionId: ""
    property var selectedNodes: []             // node ids, for multi-selection

    // ---- view state ------------------------------------------------------
    property string detailLevel: "normal"      // normal | compact

    property int _nextId: 1

    // =====================================================================
    // node access
    // =====================================================================

    function nodeIndex(id) {
        for (var i = 0; i < nodes.count; ++i) {
            if (nodes.get(i).nodeId === id)
                return i
        }
        return -1
    }

    function node(id) {
        var i = nodeIndex(id)
        return i < 0 ? null : nodes.get(i)
    }

    function nodeName(id) {
        var n = node(id)
        return n ? n.name : ""
    }

    function addNode(type, x, y, options) {
        var def = ComponentRegistry.definition(type)
        if (!def)
            return ""

        var id = "n" + (_nextId++)
        var meta = {
            subtitle: def.subtitle,
            readout: JSON.parse(JSON.stringify(def.readout || []))
        }
        if (options) {
            if (options.subtitle !== undefined)
                meta.subtitle = options.subtitle
            if (options.readout !== undefined)
                meta.readout = options.readout
        }

        nodes.append({
            nodeId: id,
            type: type,
            name: options && options.name ? options.name : uniqueName(def.defaultName),
            x: Math.round(x),
            y: Math.round(y),
            enabled: true,
            meta: meta
        })
        graphRevision++
        return id
    }

    function uniqueName(base) {
        var taken = {}
        for (var i = 0; i < nodes.count; ++i)
            taken[nodes.get(i).name] = true
        if (!taken[base])
            return base
        var n = 2
        while (taken[base + " " + n])
            ++n
        return base + " " + n
    }

    function removeNode(id) {
        var i = nodeIndex(id)
        if (i < 0)
            return
        for (var c = connections.count - 1; c >= 0; --c) {
            var conn = connections.get(c)
            if (conn.fromNode === id || conn.toNode === id)
                connections.remove(c)
        }
        nodes.remove(i)
        selectedNodes = selectedNodes.filter(function (n) { return n !== id })
        if (selectionKind === "node" && selectionId === id)
            clearSelection()
        graphRevision++
        geometryRevision++
    }

    function moveNode(id, x, y) {
        var i = nodeIndex(id)
        if (i < 0)
            return
        nodes.setProperty(i, "x", x)
        nodes.setProperty(i, "y", y)
        geometryRevision++
    }

    function renameNode(id, name) {
        var i = nodeIndex(id)
        if (i < 0 || name.length === 0)
            return
        nodes.setProperty(i, "name", name)
        graphRevision++
    }

    function setNodeEnabled(id, enabled) {
        var i = nodeIndex(id)
        if (i < 0)
            return
        nodes.setProperty(i, "enabled", enabled)
        graphRevision++
    }

    function duplicateNode(id) {
        var source = node(id)
        if (!source)
            return ""
        // Connections are deliberately not copied: a duplicated component is
        // a new part of the architecture, not a parallel branch.
        return addNode(source.type, source.x + 32, source.y + 32, {
            name: uniqueName(source.name),
            subtitle: source.meta.subtitle,
            readout: JSON.parse(JSON.stringify(source.meta.readout))
        })
    }

    // =====================================================================
    // geometry
    // =====================================================================

    function nodeRect(id) {
        var n = node(id)
        if (!n)
            return Qt.rect(0, 0, 0, 0)
        var size = ComponentRegistry.nodeSize(n.type, detailLevel)
        return Qt.rect(n.x, n.y, size.width, size.height)
    }

    function portPoint(nodeId, portId) {
        var n = node(nodeId)
        if (!n)
            return Qt.point(0, 0)
        var offset = ComponentRegistry.portOffset(n.type, portId, detailLevel)
        return Qt.point(n.x + offset.x, n.y + offset.y)
    }

    function contentBounds() {
        return boundsOf(null)
    }

    /* The box around a set of components, or around all of them when `ids` is
     * null. One function rather than two because "fit the engine" and "fit what
     * I picked" differ only in which components are measured. */
    function boundsOf(ids) {
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
        var found = 0
        for (var i = 0; i < nodes.count; ++i) {
            var n = nodes.get(i)
            if (ids && ids.indexOf(n.nodeId) < 0)
                continue
            var size = ComponentRegistry.nodeSize(n.type, detailLevel)
            minX = Math.min(minX, n.x)
            minY = Math.min(minY, n.y)
            maxX = Math.max(maxX, n.x + size.width)
            maxY = Math.max(maxY, n.y + size.height)
            ++found
        }
        if (found === 0)
            return Qt.rect(0, 0, 0, 0)
        return Qt.rect(minX, minY, maxX - minX, maxY - minY)
    }

    function selectionBounds() {
        geometryRevision
        if (selectionKind === "connection") {
            var c = connection(selectionId)
            return c ? boundsOf([c.fromNode, c.toNode]) : Qt.rect(0, 0, 0, 0)
        }
        return selectedNodes.length > 0 ? boundsOf(selectedNodes) : Qt.rect(0, 0, 0, 0)
    }

    // =====================================================================
    // connections
    // =====================================================================

    function connectionIndex(id) {
        for (var i = 0; i < connections.count; ++i) {
            if (connections.get(i).connId === id)
                return i
        }
        return -1
    }

    function connection(id) {
        var i = connectionIndex(id)
        return i < 0 ? null : connections.get(i)
    }

    function isPortConnected(nodeId, portId) {
        for (var i = 0; i < connections.count; ++i) {
            var c = connections.get(i)
            if ((c.fromNode === nodeId && c.fromPort === portId)
                    || (c.toNode === nodeId && c.toPort === portId))
                return true
        }
        return false
    }

    function connectionForPort(nodeId, portId) {
        for (var i = 0; i < connections.count; ++i) {
            var c = connections.get(i)
            if ((c.fromNode === nodeId && c.fromPort === portId)
                    || (c.toNode === nodeId && c.toPort === portId))
                return c
        }
        return null
    }

    function connectionsForNode(nodeId) {
        var out = []
        for (var i = 0; i < connections.count; ++i) {
            var c = connections.get(i)
            if (c.fromNode === nodeId || c.toNode === nodeId)
                out.push(c)
        }
        return out
    }

    /* Editor-level typing only: outlets join inlets of the same port type.
     * This says nothing about whether the resulting architecture would work -
     * that judgement needs physics this build does not have. */
    function canConnect(fromNode, fromPort, toNode, toPort) {
        var a = node(fromNode)
        var b = node(toNode)
        if (!a || !b)
            return { ok: false, reason: "Unknown component" }
        if (fromNode === toNode)
            return { ok: false, reason: "A component cannot connect to itself" }

        var pa = ComponentRegistry.port(a.type, fromPort)
        var pb = ComponentRegistry.port(b.type, toPort)
        if (!pa || !pb)
            return { ok: false, reason: "Unknown port" }
        if (pa.direction === pb.direction)
            return { ok: false, reason: pa.direction === "out" ? "Two outlets cannot be joined"
                                                               : "Two inlets cannot be joined" }
        if (pa.type !== pb.type)
            return { ok: false,
                     reason: ComponentRegistry.portTypeLabel(pa.type) + " cannot connect to "
                             + ComponentRegistry.portTypeLabel(pb.type).toLowerCase() }

        var inletNode = pa.direction === "in" ? fromNode : toNode
        var inletPort = pa.direction === "in" ? fromPort : toPort
        if (isPortConnected(inletNode, inletPort))
            return { ok: false, reason: "That inlet already has a connection" }

        return { ok: true, reason: "" }
    }

    function addConnection(fromNode, fromPort, toNode, toPort) {
        var check = canConnect(fromNode, fromPort, toNode, toPort)
        if (!check.ok)
            return ""

        // Store the connection in flow direction, whichever way it was drawn.
        var a = node(fromNode)
        var pa = ComponentRegistry.port(a.type, fromPort)
        var source = pa.direction === "out" ? { n: fromNode, p: fromPort } : { n: toNode, p: toPort }
        var target = pa.direction === "out" ? { n: toNode, p: toPort } : { n: fromNode, p: fromPort }

        var sourcePort = ComponentRegistry.port(node(source.n).type, source.p)
        var targetPort = ComponentRegistry.port(node(target.n).type, target.p)
        var id = "c" + (_nextId++)
        connections.append({
            connId: id,
            fromNode: source.n,
            fromPort: source.p,
            toNode: target.n,
            toPort: target.p,
            portType: sourcePort.type,
            subtype: mediumOf(sourcePort, targetPort),
            name: connectionName(sourcePort, targetPort)
        })
        graphRevision++
        return id
    }

    /* Generic carriers ("propellant") give way to the specific medium at the
     * other end, so a tank feeding a fuel inlet draws as a fuel line. */
    function mediumOf(sourcePort, targetPort) {
        if (sourcePort.subtype === "propellant" && targetPort.subtype !== "propellant")
            return targetPort.subtype
        return sourcePort.subtype
    }

    function connectionName(sourcePort, targetPort) {
        var word = sourcePort.type === "mechanical" ? "drive"
                 : sourcePort.type === "thermal" ? "path" : "line"
        var medium = mediumOf(sourcePort, targetPort)
        var stem = medium.charAt(0).toUpperCase() + medium.slice(1)
        var n = 1
        while (nameTaken(stem + " " + word + " " + pad(n)))
            ++n
        return stem + " " + word + " " + pad(n)
    }

    function pad(n) {
        return n < 10 ? "0" + n : "" + n
    }

    function nameTaken(name) {
        for (var i = 0; i < connections.count; ++i) {
            if (connections.get(i).name === name)
                return true
        }
        return false
    }

    function removeConnection(id) {
        var i = connectionIndex(id)
        if (i < 0)
            return
        connections.remove(i)
        if (selectionKind === "connection" && selectionId === id)
            clearSelection()
        graphRevision++
    }

    function disconnectNode(id) {
        for (var c = connections.count - 1; c >= 0; --c) {
            var conn = connections.get(c)
            if (conn.fromNode === id || conn.toNode === id)
                connections.remove(c)
        }
        graphRevision++
    }

    // =====================================================================
    // status and structural checks
    // =====================================================================

    function nodeStatus(id) {
        var n = node(id)
        if (!n)
            return "unconfigured"
        if (!n.enabled)
            return "disabled"

        var ports = ComponentRegistry.ports(n.type)
        var connected = 0
        var missingRequired = 0
        for (var i = 0; i < ports.length; ++i) {
            var isConnected = isPortConnected(id, ports[i].id)
            if (isConnected)
                ++connected
            else if (ports[i].required)
                ++missingRequired
        }
        if (missingRequired > 0)
            return "problem"
        if (ports.length > 0 && connected === ports.length)
            return "configured"
        return "unconfigured"
    }

    /* Structural checks only: ports that the editor knows are required, names
     * that collide, components left out of the architecture. Nothing here
     * inspects pressures, flows or temperatures - that is solver work. */
    readonly property var problems: {
        graphRevision                        // dependency: recompute on graph change
        var list = []
        var i, j

        var names = {}
        for (i = 0; i < nodes.count; ++i) {
            var n = nodes.get(i)
            var ports = ComponentRegistry.ports(n.type)
            var flagged = false

            for (j = 0; j < ports.length; ++j) {
                if (ports[j].required && !isPortConnected(n.nodeId, ports[j].id)) {
                    list.push({
                        problemId: "req-" + n.nodeId + "-" + ports[j].id,
                        severity: "warning",
                        message: n.name + " has no " + ports[j].label.toLowerCase() + " connected.",
                        targetKind: "node",
                        targetId: n.nodeId
                    })
                    flagged = true
                }
            }

            if (!flagged && nodes.count > 1 && connectionsForNode(n.nodeId).length === 0) {
                list.push({
                    problemId: "orphan-" + n.nodeId,
                    severity: "info",
                    message: n.name + " is not connected to the architecture.",
                    targetKind: "node",
                    targetId: n.nodeId
                })
            }

            if (names[n.name] !== undefined) {
                list.push({
                    problemId: "dup-" + n.nodeId,
                    severity: "warning",
                    message: "Two components are named " + n.name + ".",
                    targetKind: "node",
                    targetId: n.nodeId
                })
            }
            names[n.name] = n.nodeId
        }

        var hasChamber = false
        var hasNozzle = false
        for (i = 0; i < nodes.count; ++i) {
            if (nodes.get(i).type === "chamber") hasChamber = true
            if (nodes.get(i).type === "nozzle") hasNozzle = true
        }
        if (hasChamber && !hasNozzle) {
            list.push({
                problemId: "arch-noexpansion",
                severity: "info",
                message: "Architecture has a combustion chamber but no expansion stage.",
                targetKind: "none",
                targetId: ""
            })
        }

        return list
    }

    // =====================================================================
    // selection
    // =====================================================================

    function selectNode(id, additive) {
        if (additive) {
            var next = selectedNodes.slice()
            var at = next.indexOf(id)
            if (at >= 0)
                next.splice(at, 1)
            else
                next.push(id)
            selectedNodes = next
            selectionKind = next.length > 0 ? "node" : "none"
            selectionId = next.length > 0 ? next[next.length - 1] : ""
        } else {
            selectedNodes = [id]
            selectionKind = "node"
            selectionId = id
        }
    }

    function setSelectedNodes(ids) {
        selectedNodes = ids.slice()
        selectionKind = ids.length > 0 ? "node" : "none"
        selectionId = ids.length > 0 ? ids[ids.length - 1] : ""
    }

    function selectConnection(id) {
        selectedNodes = []
        selectionKind = "connection"
        selectionId = id
    }

    function clearSelection() {
        selectedNodes = []
        selectionKind = "none"
        selectionId = ""
    }

    function isNodeSelected(id) {
        return selectedNodes.indexOf(id) >= 0
    }

    function selectAll() {
        var ids = []
        for (var i = 0; i < nodes.count; ++i)
            ids.push(nodes.get(i).nodeId)
        setSelectedNodes(ids)
    }

    function deleteSelection() {
        if (selectionKind === "connection") {
            removeConnection(selectionId)
            return
        }
        var ids = selectedNodes.slice()
        for (var i = 0; i < ids.length; ++i)
            removeNode(ids[i])
        clearSelection()
    }

    function duplicateSelection() {
        var ids = selectedNodes.slice()
        var created = []
        for (var i = 0; i < ids.length; ++i) {
            var id = duplicateNode(ids[i])
            if (id)
                created.push(id)
        }
        if (created.length > 0)
            setSelectedNodes(created)
    }

    // =====================================================================
    // project lifecycle
    // =====================================================================

    function clearAll() {
        connections.clear()
        nodes.clear()
        clearSelection()
        _nextId = 1
        graphRevision++
        geometryRevision++
    }

    function newProject(name, architectureName) {
        clearAll()
        engineName = name && name.length > 0 ? name : "Engine-01"
        architecture = architectureName
    }

    function loadDemo() {
        clearAll()
        var spec = MockEngineData.demoEngine
        var idByKey = {}
        var i

        for (i = 0; i < spec.nodes.length; ++i) {
            var n = spec.nodes[i]
            idByKey[n.key] = addNode(n.type, n.x, n.y, {
                name: n.name,
                subtitle: n.subtitle,
                readout: n.readout
            })
        }
        for (i = 0; i < spec.connections.length; ++i) {
            var c = spec.connections[i]
            addConnection(idByKey[c.from], c.fromPort, idByKey[c.to], c.toPort)
        }
        engineName = spec.engineName
        architecture = spec.architecture
        propellants = spec.propellants
        environment = spec.environment
        clearSelection()
    }
}
