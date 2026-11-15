"""Blue-Eyes Live Coach V1 — offline Windows floating overlay (manual-state MVP)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QMessageBox, QScrollArea, QCheckBox,
    QGraphicsScene, QGraphicsView, QGraphicsTextItem, QGraphicsRectItem,
    QFrame, QGridLayout
)
from core.engine import CoachEngine, DuelState, load_deck

STORE = Path.home() / ".blue_eyes_live_coach" / "state.json"
STYLE = """
QWidget {background:#111b2b;color:#eaf2ff;font-family:'Segoe UI';font-size:12px}
QPushButton {background:#234469;color:#f2f6ff;border:1px solid #4778a6;border-radius:7px;padding:7px}
QPushButton:hover {background:#35608c}
QPushButton:disabled {background:#202a3a;color:#8090a4}
QComboBox {background:#1e324d;color:white;padding:6px;border:1px solid #476487;border-radius:5px}
QLabel#heading {font-size:15px;font-weight:bold;color:#a8d2ff}
QLabel#action {font-size:15px;font-weight:600;color:white}
QLabel#hint {color:#b3c9df}
QLabel#warning {color:#ffb89c}
"""

def load_saved() -> DuelState:
    try:
        return DuelState.from_json(json.loads(STORE.read_text(encoding="utf-8")))
    except (FileNotFoundError, ValueError, TypeError, KeyError):
        return DuelState()

def persist(state: DuelState) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(state.to_json(), indent=2), encoding="utf-8")

class HandDialog(QDialog):
    def __init__(self, deck, current, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opening hand — choose 5 cards")
        self.resize(380, 340)
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Select the five cards actually visible in your hand."))
        names = sorted(name for name, _ in deck["mainDeck"])
        self.pickers = []
        for i in range(5):
            picker = QComboBox()
            picker.addItems(names)
            if len(current) > i and current[i] in names:
                picker.setCurrentText(current[i])
            else:
                picker.setCurrentIndex(min(i, len(names) - 1))
            root.addWidget(picker)
            self.pickers.append(picker)
        save = QPushButton("Use this opening hand")
        save.clicked.connect(self.accept)
        root.addWidget(save)

    def cards(self):
        return [picker.currentText() for picker in self.pickers]

class ExtraDialog(QDialog):
    def __init__(self, engine, changed, parent=None):
        super().__init__(parent)
        self.engine, self.changed = engine, changed
        self.setWindowTitle("Extra Deck tracker — manual")
        self.resize(480, 530)
        outer = QVBoxLayout(self)
        outer.addWidget(QLabel("Mark a card ONLY when you actually summon/use it."))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        interior = QWidget()
        self.rows = QVBoxLayout(interior)
        for name, count in engine.deck["extraDeck"]:
            row = QHBoxLayout()
            label = QLabel(name)
            label.setWordWrap(True)
            row.addWidget(label, 1)
            used = QLabel()
            row.addWidget(used)
            minus = QPushButton("−")
            plus = QPushButton("+")
            minus.setFixedWidth(32)
            plus.setFixedWidth(32)
            row.addWidget(minus)
            row.addWidget(plus)
            def update(n=name, qty=count, lbl=used, dec=minus, inc=plus):
                u = self.engine.state.extra_used.get(n, 0)
                lbl.setText(f"{u}/{qty}")
                dec.setEnabled(u > 0)
                inc.setEnabled(u < qty)
            def change(delta, n=name, updater=update):
                try:
                    if delta > 0: self.engine.mark_extra(n)
                    else: self.engine.undo_extra(n)
                except ValueError as exc:
                    QMessageBox.warning(self, "Extra Deck", str(exc))
                updater()
                self.changed()
            plus.clicked.connect(lambda _=False, change=change: change(1))
            minus.clicked.connect(lambda _=False, change=change: change(-1))
            update()
            self.rows.addLayout(row)
        scroll.setWidget(interior)
        outer.addWidget(scroll)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        outer.addWidget(close)

class GraphDialog(QDialog):
    def __init__(self, engine, choose_route, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Blue-Eyes branching combo map")
        self.resize(1040, 690)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Click a starter branch to select it. Red nodes are safety stops, not automatic recovery combos."))
        self.scene = QGraphicsScene(self)
        view = QGraphicsView(self.scene)
        view.setRenderHint(QPainter.Antialiasing)
        view.setDragMode(QGraphicsView.ScrollHandDrag)
        layout.addWidget(view)
        self.choose_route = choose_route
        self.engine = engine
        self.draw()

    def node(self, x, y, w, h, title, bg="#244264", callback=None):
        if callback:
            btn = QPushButton(title)
            btn.setMinimumSize(w, h)
            btn.setMaximumWidth(w)
            btn.setStyleSheet(f"QPushButton{{background:{bg};white-space:normal;border:1px solid #7ba1c8;border-radius:6px;padding:5px;color:white}}")
            btn.clicked.connect(lambda: (callback(), self.accept()))
            proxy = self.scene.addWidget(btn)
            proxy.setPos(x, y)
        else:
            rect = self.scene.addRect(x,y,w,h,QPen(QColor("#7198c0")),QColor(bg))
            txt = self.scene.addText(title)
            txt.setDefaultTextColor(QColor("#ffffff"))
            txt.setTextWidth(w - 12)
            txt.setPos(x+6, y+6)
        return (x+w/2,y+h/2)

    def edge(self, a, b, color="#7d97b5"):
        self.scene.addLine(a[0],a[1],b[0],b[1],QPen(QColor(color),2))

    def draw(self):
        routes = self.engine.available_routes()
        top = self.node(355,10,270,55,"OPENING HAND — choose a starter","#1b5879")
        if not routes:
            self.node(285,110,410,75,"No starter route matched. Check your hand or inspect manually.","#694a30")
        else:
            # Branch nodes in a row. Horizontal scrolling supports several options.
            for i,route in enumerate(routes):
                x=i*310+18
                n=self.node(x,112,265,64,route.starter,"#28577a",
                    callback=lambda rid=route.id:self.choose_route(rid))
                self.edge((top[0],65),(n[0],112))
                self.node(x,207,265,55,"Resolved → inspect next action","#1d574a")
                self.node(x,285,265,55,"Negated → pause & replan","#70343e")
                self.edge((n[0],176),(n[0],207),"#76c9a2")
                self.edge((n[0],176),(n[0]+90,285),"#f0a3a9")
        route=self.engine.route()
        if route:
            base_y=405
            last=(475,375)
            self.node(310,362,350,37,"SELECTED ROUTE: "+route.title,"#27517a")
            for i,step in enumerate(route.steps):
                y=base_y+i*92
                n=self.node(285,y,380,66,f"{i+1}. {step.title}" + ("  ◀ CURRENT" if i==self.engine.state.index else ""),"#176253" if i==self.engine.state.index else "#29496b")
                self.edge(last,(n[0],y))
                last=(n[0],y+66)
                if i==self.engine.state.index:
                    red=self.node(720,y,240,66,"Negated → stop & reassess","#713842")
                    self.edge((665,y+33),(720,y+33),"#ec9ca5")
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-25,-25,25,25))

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = CoachEngine(load_deck(), load_saved())
        self.setWindowTitle("Blue-Eyes Live Coach V1")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(350)
        self.setMaximumWidth(470)
        self.setStyleSheet(STYLE)
        self.drag_origin = None
        root=QVBoxLayout(self)
        root.setSpacing(9)
        title=QLabel("BLUE-EYES LIVE COACH  ·  V1")
        title.setObjectName("heading")
        root.addWidget(title)
        sub=QLabel("OFFLINE  ·  MANUAL CONFIRMATION  ·  NO SCREEN CAPTURE")
        sub.setObjectName("hint")
        sub.setWordWrap(True)
        root.addWidget(sub)
        buttons=QHBoxLayout()
        self.hand_button=QPushButton("Opening hand")
        self.hand_button.clicked.connect(self.pick_hand)
        buttons.addWidget(self.hand_button)
        self.extra_button=QPushButton("Extra Deck")
        self.extra_button.clicked.connect(self.show_extra)
        buttons.addWidget(self.extra_button)
        self.graph_button=QPushButton("Combo map")
        self.graph_button.clicked.connect(self.show_graph)
        buttons.addWidget(self.graph_button)
        root.addLayout(buttons)
        self.hand_label=QLabel()
        self.hand_label.setObjectName("hint")
        self.hand_label.setWordWrap(True)
        root.addWidget(self.hand_label)
        self.route_picker=QComboBox()
        self.route_picker.currentIndexChanged.connect(self.choose_from_picker)
        root.addWidget(self.route_picker)
        self.status=QLabel()
        self.status.setObjectName("warning")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.action=QLabel()
        self.action.setObjectName("action")
        self.action.setWordWrap(True)
        root.addWidget(self.action)
        self.instruction=QLabel()
        self.instruction.setWordWrap(True)
        root.addWidget(self.instruction)
        self.note=QLabel()
        self.note.setObjectName("hint")
        self.note.setWordWrap(True)
        root.addWidget(self.note)
        controls=QHBoxLayout()
        self.resolved=QPushButton("✓ Resolved")
        self.resolved.clicked.connect(self.resolve)
        self.negated=QPushButton("✕ Negated")
        self.negated.clicked.connect(self.negate)
        self.replan=QPushButton("↺ Replan")
        self.replan.clicked.connect(self.replan_route)
        for b in (self.resolved,self.negated,self.replan): controls.addWidget(b)
        root.addLayout(controls)
        footer=QHBoxLayout()
        self.progress=QLabel()
        footer.addWidget(self.progress,1)
        hide=QPushButton("Minimize")
        hide.clicked.connect(self.showMinimized)
        footer.addWidget(hide)
        root.addLayout(footer)
        self.populate_routes()
        self.render()

    def save(self):
        persist(self.engine.state)

    def pick_hand(self):
        dialog=HandDialog(self.engine.deck,self.engine.state.hand,self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.engine.select_hand(dialog.cards())
            except ValueError as exc:
                QMessageBox.warning(self,"Invalid hand",str(exc))
                return
            self.populate_routes()
            self.save()
            self.render()

    def populate_routes(self):
        current=self.engine.state.route_id
        self.route_picker.blockSignals(True)
        self.route_picker.clear()
        self.route_picker.addItem("Select a starter route", "")
        for r in self.engine.available_routes():
            self.route_picker.addItem(r.title, r.id)
        self.route_picker.addItem("— REFERENCE ROUTES (unverified) —", "")
        for r in self.engine.routes:
            if r.id.startswith("ref:"):
                self.route_picker.addItem("⚠ "+r.title, r.id)
        index=self.route_picker.findData(current)
        self.route_picker.setCurrentIndex(max(0,index))
        self.route_picker.blockSignals(False)

    def choose_from_picker(self, i):
        rid=self.route_picker.itemData(i)
        if rid:
            self.choose_route(rid)

    def choose_route(self, rid):
        try:
            self.engine.select_route(rid)
        except ValueError as exc:
            QMessageBox.warning(self,"Route",str(exc))
            return
        self.save()
        self.populate_routes()
        self.render()

    def render(self):
        state=self.engine.state
        self.hand_label.setText("HAND: " + (", ".join(state.hand) if state.hand else "Not selected"))
        route=self.engine.route()
        step=self.engine.current_step()
        if state.paused:
            self.status.setText("NEGATED / INTERRUPTED — paused. Replan from the actual field; no automatic continuation.")
        elif route:
            self.status.setText(route.status)
        else:
            self.status.setText("Select opening hand to see starter routes.")
        if step and not state.paused:
            self.action.setText(step.title)
            self.instruction.setText(step.instruction)
            self.note.setText(step.note)
        elif state.paused:
            self.action.setText("STOP — verify game state")
            self.instruction.setText("The previous step failed. Check what remains in hand, field and Graveyard, then select Replan or a different route. Do not continue as if it resolved.")
            self.note.setText("")
        elif route:
            self.action.setText("Route checklist completed")
            self.instruction.setText("Verify the actual endboard in Master Duel. Completion does not certify a legal full combo.")
            self.note.setText("")
        else:
            self.action.setText("Waiting for opening hand")
            self.instruction.setText("Choose five cards and a starter route to begin.")
            self.note.setText("")
        self.progress.setText(f"Step {min(state.index+1,len(route.steps)) if route else 0} / {len(route.steps) if route else 0}   ·   Extra used: {sum(state.extra_used.values())}/15")
        self.resolved.setEnabled(bool(step) and not state.paused)
        self.negated.setEnabled(bool(step) and not state.paused)
        self.replan.setEnabled(bool(route))

    def resolve(self):
        self.engine.resolve()
        self.save()
        self.render()

    def negate(self):
        self.engine.negate()
        self.save()
        self.render()

    def replan_route(self):
        self.engine.retry_or_replan()
        self.save()
        self.populate_routes()
        self.render()

    def show_extra(self):
        ExtraDialog(self.engine, lambda:(self.save(),self.render()),self).exec()
        self.render()

    def show_graph(self):
        GraphDialog(self.engine,self.choose_route,self).exec()

def main():
    app=QApplication(sys.argv)
    app.setStyle("Fusion")
    window=Overlay()
    window.show()
    raise SystemExit(app.exec())

if __name__ == "__main__":
    main()
