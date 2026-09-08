"""A stable list model for publishing rows to QML.

Handing QML a ``@Property("QVariantList")`` and letting a binding re-read it on
every update retains memory that neither garbage collector reclaims: measured
at roughly 27 KB per publication for six two-field rows, linear and unbounded,
in a twenty-line program containing no RocketForge code
(``experiments/qml_memory/minimal_reproducer.py``). The cost is the
QVariantList conversion performed on each read, not the delegates and not the
rebuilding of the Python list -- caching the list only halves it.

The same rows delivered through this model retain nothing measurable.

Use it for anything list-shaped that a view binds and that changes as results
are recomputed. Scalars and strings are unaffected and need no model.

The model is created once and updated in place. It emits ``dataChanged`` when
values change and only resets when the row count moves, so delegates are reused
rather than destroyed and rebuilt.
"""
from __future__ import annotations

from PySide6.QtCore import (QAbstractListModel, QByteArray, QModelIndex, Qt,
                            Slot)


class RowListModel(QAbstractListModel):
    """Uniform rows of string fields, addressed by role name.

    ``roles`` names the fields a delegate may bind, in order. A row missing a
    field yields an empty string rather than ``undefined``, so a delegate never
    has to guard against a key that a particular result did not produce.
    """

    __slots__ = ()

    def __init__(self, roles, parent=None) -> None:
        super().__init__(parent)
        if not roles:
            raise ValueError("a row model needs at least one role")
        # An entry is either "name" (role and dict key are the same) or
        # ("roleName", "dictKey"). The pair form exists because a delegate
        # cannot redeclare a property its own type already defines: binding a
        # PerfMetricReadout to roles called `value`/`unit`/`primary` collided
        # with the component's own properties and the whole readout silently
        # rendered empty.
        pairs: list[tuple[str, str]] = []
        for entry in roles:
            if isinstance(entry, str):
                pairs.append((entry, entry))
            else:
                role, key = entry
                pairs.append((str(role), str(key)))
        self._roles = tuple(role for role, _ in pairs)
        base = int(Qt.ItemDataRole.UserRole) + 1
        self._role_ids = {base + index: role
                          for index, (role, _) in enumerate(pairs)}
        self._role_keys = dict(pairs)
        self._rows: list[dict] = []

    # -- QAbstractListModel ------------------------------------------------

    def roleNames(self) -> dict:
        return {key: QByteArray(name.encode("utf-8"))
                for key, name in self._role_ids.items()}

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        if not 0 <= row < len(self._rows):
            return None
        name = self._role_ids.get(int(role))
        if name is None:
            return None
        value = self._rows[row].get(self._role_keys.get(name, name), "")
        if value is None:
            return ""
        # bool/int/float reach QML as themselves. Stringifying a flag turns
        # `primary` into the string "True", which is truthy either way and
        # would make `primary: false` silently mean `true`.
        if isinstance(value, (bool, int, float)):
            return value
        return str(value)

    # -- publication -------------------------------------------------------

    def set_rows(self, rows) -> None:
        """Replace the contents, in place wherever possible.

        A changed row count is a structural change and resets the model. A
        same-length update emits ``dataChanged`` over the rows that actually
        moved, so unchanged delegates are not touched at all.
        """
        incoming = [dict(row) for row in (rows or [])]
        if len(incoming) != len(self._rows):
            self.beginResetModel()
            self._rows = incoming
            self.endResetModel()
            return
        if not incoming:
            return
        changed = [index for index, (old, new)
                   in enumerate(zip(self._rows, incoming)) if old != new]
        if not changed:
            return
        self._rows = incoming
        first, last = min(changed), max(changed)
        self.dataChanged.emit(self.index(first, 0), self.index(last, 0),
                              list(self._role_ids))

    # -- read-back, for tests and diagnostics ------------------------------

    @Slot(result=int)
    def count(self) -> int:
        return len(self._rows)

    def rows(self) -> list[dict]:
        """The current contents. For Python callers; QML binds the model."""
        return [dict(row) for row in self._rows]
