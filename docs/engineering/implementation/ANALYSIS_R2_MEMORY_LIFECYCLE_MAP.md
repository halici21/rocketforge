# Analysis R2 — chart-page lifecycle map

Every dynamically-lived object on the navigation path, with its owner and its
destruction trigger. Compiled by reading the implementation and confirmed
against a live scene (`acceptance/analysis_r2_closure/memory/ownership_audit.json`).

## The chain

```
ApplicationWindow (Main.qml)            application lifetime
  └─ currentPageIndex : int             plain value, no object reference
      └─ WorkspaceHost                  application lifetime
          └─ Loader                     application lifetime
              source: "pages/" + Navigation.pageSource(currentIndex)
              └─ <Workspace>Page.qml    ← CREATED AND DESTROYED PER NAVIGATION
                  └─ StackLayout        page lifetime
                      ├─ <Calculator>   page lifetime
                      ├─ <Table>        page lifetime
                      └─ <Charts>       page lifetime
                          └─ RFLineChart / RFPlotSurface
                              ├─ Canvas plot        page lifetime
                              ├─ Canvas hover       page lifetime
                              ├─ MouseArea          page lifetime
                              └─ Connections        page lifetime
```

## Ownership table

| Object | Created by | Parent | Lifetime | Destroyed by | External refs |
| --- | --- | --- | --- | --- | --- |
| `<Workspace>Page` | `Loader` on `source` change | `Loader` | one navigation | `Loader.source` change | none observed |
| `StackLayout` children | page QML | page | page | page destruction | none |
| `RFLineChart` | chart QML | page subtree | page | page destruction | none |
| plot `Canvas` | `RFLineChart` | `RFLineChart` | page | parent destruction | none |
| hover `Canvas` | `RFLineChart` | `RFLineChart` | page | parent destruction | none |
| `MouseArea` / handlers | `RFLineChart` | `RFLineChart` | page | parent destruction | none |
| `Connections { target: <Controller> }` | chart QML | page subtree | page | parent destruction | **controller outlives it — see below** |
| result rows | controller `QVariantList` property | controller (Python) | controller | controller | value copies, not object refs |

## The one cross-lifetime edge

`Connections { target: Isentropic }` (and the equivalent on every chart page)
binds a page-lifetime object to an **application-lifetime singleton**
controller. This is the classic retention shape, so it was checked directly
rather than reasoned about:

- `QQmlConnections` is parented into the page subtree, so it is destroyed with
  the page.
- Qt removes a connection when either end is destroyed; the controller holds
  no strong reference back.
- Measured: `Connections` live-count growth over 200 page loads is **0**
  (`soak.py focused_100`, `object_growth: {}`).

## Result publication

Controllers publish results as `QVariantList` / `QVariantMap` properties read
by QML. These carry **values**, not object references, so a published result
cannot retain a page. Verified: `workspaceState`, `shellContext`, `navigation`
each hold **0** child QObjects; `Theme` holds 2, neither visual.

## Destruction, confirmed rather than assumed

`shiboken6.isValid()` on the page item after navigating away:

| Page | Class | C++ object alive afterwards |
| --- | --- | --- |
| Isentropic | `IsentropicPage_QMLTYPE_368` | **no** |
| Fanno | `FannoPage_QMLTYPE_402` | **no** |
| Nozzle Lab | `NozzleLabPage_QMLTYPE_453` | **no** |
| Oblique Shock | `ObliqueShockPage_QMLTYPE_482` | **no** |

`visible: false` is not used to retire a page anywhere on this path; the
`Loader` genuinely replaces its item.

## Why counting this is easy to get wrong

Two traps were hit during this work and are recorded so the next reader avoids
them:

1. **`processEvents()` does not dispatch `DeferredDelete`.** Destroyed pages
   remain countable until it is dispatched, which makes correct destruction
   look like retention. 28.5 MB per page load, entirely artificial.
2. **`findChildren()` creates a Python wrapper per object returned**, so a
   census taken inside a soak inflates the very count it reports, and a census
   taken while different pages are resident measures which page is loaded
   rather than what was retained. Both censuses are now taken parked on a
   fixed chart-free page.
