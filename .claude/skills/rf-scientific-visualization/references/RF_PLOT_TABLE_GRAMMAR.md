# RF plot/table grammar -- quick reference

A scannable checklist. The reasoning behind each row is in `SKILL.md`; this
file is for a fast pass during implementation or review, not for first
reading.

## Proportion decision

| At this state... | Chart | Table |
| --- | --- | --- |
| A sweep/study answers the live question | Dominant | Secondary / collapsible |
| A single point, no sweep exists | None | The values themselves, plainly |
| Inspecting specific solved points from a chart already shown | Stays dominant | Supports it, dense, scrollable |

## Kill list (reject by default)

- [ ] Pie chart
- [ ] Dual axis
- [ ] 3D effect on a 2D quantity
- [ ] Rainbow scale on ordered data
- [ ] Redundant data-ink (bar + label + dense gridline, same quantity)
- [ ] Legend floating away from its data when a direct label would do

## Keep list

- [ ] Direct labels on data
- [ ] Range frame (axis spans only where data exists)
- [ ] One accent colour, actually applied to the focal point/series
- [ ] Table instead of chart once n <~ 20 and exact values matter
- [ ] Sorted categories, unless input order is itself meaningful

## Before publishing any chart

- [ ] `RFPlotSurface.xTitle` / `yTitle` carry the unit, not blank
- [ ] Any stated tolerance/validity envelope is represented, not implied
- [ ] Every colour distinction is paired with a non-colour cue
- [ ] If this is a Trade Study Pareto plot: the caption or a visible note
      states how many objectives actually define membership, and the plot
      does not visually claim the two plotted axes alone decide it
- [ ] Axis change (if the workspace supports arbitrary axis selection)
      triggers zero physics solves -- verify, do not assume

## Component map

| Need | Component |
| --- | --- |
| Axis/grid/tick frame for any chart | `RFPlotSurface` |
| A line/sweep series on that frame | `RFLineChart` |
| Dense numeric rows | `RFEngineeringTable` |
| A non-numeric column inside that table | `columns: [{ key, label, align: "left" }]` |
