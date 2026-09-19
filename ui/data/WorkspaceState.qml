pragma Singleton
import QtQuick
import RocketForge 1.0

/*
 * WorkspaceState -- one place that turns a workspace's own controller
 * state into the short, honest summary text the Browser (ui/shell/
 * SideNav.qml) and Home (ui/pages/HomePage.qml) both show.
 *
 * Every field read here is resultChanged-scoped (statusLabel, resultStale,
 * hasResult, visibleRowCount) -- never a live input property -- so this
 * summary can never show a number or state that has since moved without
 * the reader also seeing it marked stale. See
 * docs/design/CAD_WORKBENCH_R1_STRUCTURAL_RECOVERY_DESIGN.md.
 */
QtObject {
    // A stale result still says what it is AND that it is stale in the
    // text itself -- colour is reinforcement, never the only signal
    // (rf-scientific-ui-contract's colour-only rule applies here exactly
    // as it does to a workspace's own stale chip).
    function withStaleSuffix(text, stale) {
        return stale ? text + " · Stale" : text
    }

    function stateFor(key) {
        switch (key) {
        case "thermochem":
            return { text: withStaleSuffix(Thermochemistry.statusLabel, Thermochemistry.resultStale),
                     stale: Thermochemistry.resultStale, hasResult: Thermochemistry.hasResult }
        case "performance":
            return { text: withStaleSuffix(RocketPerformance.statusLabel, RocketPerformance.resultStale),
                     stale: RocketPerformance.resultStale, hasResult: RocketPerformance.hasResult }
        case "tradestudy":
            return {
                text: withStaleSuffix(
                    TradeStudy.hasResult
                    ? TradeStudy.visibleRowCount + " point"
                      + (TradeStudy.visibleRowCount === 1 ? "" : "s") + " evaluated"
                    : "Not configured",
                    TradeStudy.resultStale),
                stale: TradeStudy.resultStale, hasResult: TradeStudy.hasResult
            }
        case "fluidproperties":
            return { text: withStaleSuffix(FluidProperties.statusLabel, FluidProperties.resultStale),
                     stale: FluidProperties.resultStale, hasResult: FluidProperties.hasResult }
        case "line":
            return { text: withStaleSuffix(Line.statusLabel, Line.resultStale),
                     stale: Line.resultStale, hasResult: Line.hasResult }
        default:
            return { text: "", stale: false, hasResult: false }
        }
    }
}
