"""Smoke test de la app: los cuatro modos se ejecutan sin excepciones.

Un `NameError` en un modo (el caso de `render_psi_mode` cuando se añadió) pasaba la suite
porque ningún test ejecutaba la UI. Esto recorre la app real con `AppTest`, sin red:
el modo PSI no descarga hasta que se pulsa el botón y el feed LIVE no se conecta solo.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

MODO = "Modo de datos"
MODOS = ["Simulador Físico Micro-G",
         "Live ISS (NASA · Lightstreamer)",
         "Histórico NASA (PSI · Saffire)",
         "Subir Dataset Real (CSV NASA OSDR / Saffire)"]


def _abrir() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90)
    at.run()
    return at


def _texto(at: AppTest) -> str:
    partes = [str(x.value) for x in at.markdown] + [str(x.value) for x in at.caption]
    partes += [str(x.value) for x in at.info] + [str(x.value) for x in at.warning]
    partes += [str(x.value) for x in at.error] + [str(x.value) for x in at.title]
    return " ".join(partes)


class TestSmokeApp(unittest.TestCase):

    def test_simulador_dibuja_el_veredicto(self):
        at = _abrir()
        self.assertFalse(at.exception, at.exception)
        self.assertIn("MIRI AHORA", _texto(at))
        self.assertIn("NOMINAL", _texto(at))

    def test_modo_live_abre_panel_sin_conectarse(self):
        at = _abrir()
        at.sidebar.radio[1].set_value(MODOS[1]).run()
        self.assertFalse(at.exception, at.exception)
        self.assertIn("Estado del enlace", _texto(at))

    def test_modo_psi_pide_descarga_explicita(self):
        at = _abrir()
        at.sidebar.radio[1].set_value(MODOS[2]).run()
        self.assertFalse(at.exception, at.exception)
        self.assertIn("traer la tabla oficial del experimento", _texto(at))
        self.assertTrue(any("Descargar" in (b.label or "") for b in at.button),
                        [b.label for b in at.button])

    def test_modo_csv_sin_fichero_no_simula(self):
        at = _abrir()
        at.sidebar.radio[1].set_value(MODOS[3]).run()
        self.assertFalse(at.exception, at.exception)
        # Sin fichero no debe aparecer un veredicto: sería el simulador disfrazado.
        self.assertIn("Sube un CSV", _texto(at))
        self.assertNotIn("MIRI AHORA", _texto(at))

    def test_cursor_al_inicio_no_anuncia_el_pico(self):
        at = _abrir()
        at.sidebar.selectbox[0].set_value("Ventilation-Driven Flame Spread "
                                          "(Propagación Estilo NASA Saffire)").run()
        self.assertFalse(at.exception, at.exception)
        texto = _texto(at)
        self.assertIn("NOMINAL", texto)
        self.assertIn("Veredicto calculado con las", texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
