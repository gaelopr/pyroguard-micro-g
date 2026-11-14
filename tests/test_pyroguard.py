"""Regresión de las cifras que se dicen en la demo.

Se ejecuta con: python -m unittest discover -s tests -v
Sin dependencias nuevas: solo stdlib + las del proyecto.
"""
import io
import sys
import threading
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anomaly_engine as ae  # noqa: E402
import iss_live  # noqa: E402
import physics_simulator as ps  # noqa: E402

ISS = list(ps.ATM)[0]
AEA = [a for a in ps.ATM if "Artemis" in a][0]
DEMO = Path(__file__).resolve().parents[1] / "demo_saffire_sintetico.csv"


def _escenario(i, atm=ISS, corte=0):
    df = ps.simular_escenario(i, atm, corte)
    return df, ae.detectar_anomalias(df), ae.calcular_ventaja_deteccion(ae.detectar_anomalias(df))


class TestSimulador(unittest.TestCase):
    """Los cuatro escenarios: forma, magnitudes y reproducibilidad."""

    def test_forma_y_contrato(self):
        df = ps.simular_escenario(0, ISS, 0)
        self.assertEqual(len(df), 600)
        self.assertEqual(list(df.columns), ps.COLS)
        self.assertEqual(df.timestamp_sec.iloc[0], 0)
        self.assertEqual(df.timestamp_sec.iloc[-1], 599)

    def test_reproducible(self):
        a = ps.simular_escenario(2, ISS, 0)
        b = ps.simular_escenario(2, ISS, 0)
        pd.testing.assert_frame_equal(a, b)

    def test_nominal(self):
        df, d, v = _escenario(0)
        self.assertAlmostEqual(d.miri_score.max(), 19.9, delta=0.2)
        self.assertAlmostEqual(df.temp_c.max(), 23.0, delta=0.1)
        self.assertAlmostEqual(df.co_ppm.max(), 2.8, delta=0.2)
        self.assertIsNone(v["pyroguard_seg"])
        self.assertIsNone(v["tradicional_seg"])
        self.assertEqual(ae.generar_protocolo_respuesta(df)["nivel_amenaza"], "NOMINAL")

    def test_smoldering_detector_ciego(self):
        df, d, v = _escenario(1)
        self.assertAlmostEqual(d.miri_score.max(), 59.1, delta=0.2)
        self.assertAlmostEqual(df.temp_c.max(), 26.7, delta=0.1)
        self.assertAlmostEqual(df.hcn_ppm.max(), 12.4, delta=0.2)
        self.assertEqual(v["pyroguard_seg"], 170)
        self.assertIsNone(v["tradicional_seg"])
        self.assertIn("Ciego", v["veredicto"])

    def test_saffire_ventaja_323(self):
        df, d, v = _escenario(2)
        self.assertAlmostEqual(d.miri_score.max(), 98.0, delta=0.2)
        self.assertAlmostEqual(df.co_ppm.max(), 192.4, delta=0.5)
        self.assertAlmostEqual(df.co2_ppm.max(), 9617, delta=15)
        self.assertAlmostEqual(df.radiative_heat_flux_kwm2.max(), 4.51, delta=0.02)
        self.assertAlmostEqual(df.smoke_obscuration_pct_m.max(), 5.47, delta=0.02)
        self.assertEqual(v["pyroguard_seg"], 180)
        self.assertEqual(v["tradicional_seg"], 503)
        self.assertEqual(v["ventaja_seg"], 323)

    def test_cool_flame_pre_ignicion(self):
        df, d, v = _escenario(3)
        self.assertAlmostEqual(d.miri_score.max(), 50.1, delta=0.2)
        self.assertAlmostEqual(df.temp_c.max(), 23.4, delta=0.1)
        self.assertAlmostEqual(df.smoke_obscuration_pct_m.max(), 0.21, delta=0.01)
        self.assertAlmostEqual(df.co2_ppm.max(), 6200, delta=15)
        self.assertEqual(v["pyroguard_seg"], 182)
        self.assertIsNone(v["tradicional_seg"])
        self.assertEqual(ae.generar_protocolo_respuesta(df)["nivel_amenaza"], "PRE-IGNICIÓN")

    def test_artemis_y_corte_de_ventilacion(self):
        df = ps.simular_escenario(2, AEA, 220)
        self.assertAlmostEqual(df.co_ppm.max(), 33, delta=1.0)
        self.assertAlmostEqual(df.radiative_heat_flux_kwm2.max(), 3.60, delta=0.03)
        self.assertAlmostEqual(df.temp_c.max(), 25.3, delta=0.2)
        self.assertLess(df.airflow_cms.iloc[-1], 1.0)

    def test_corte_de_ventilacion_apaga_el_caudal(self):
        sin = ps.simular_escenario(2, ISS, 0)
        con = ps.simular_escenario(2, ISS, 220)
        self.assertGreater(sin.airflow_cms.iloc[-1], 5.0)
        self.assertLess(con.airflow_cms.iloc[-1], 1.0)


class TestMapeador(unittest.TestCase):
    """Unidades, rangos y rechazo: los bugs que costaron una demo."""

    PSI = """Time (s),TC1 (K),Rad1 (kW/m2),CO2 mole fraction,O2 mole fraction,Flow (cm/s),CO (ppm),HCN (ppm)
0,296.5,0.02,0.0041,0.209,20,0.4,0.0
60,301.2,0.35,0.0048,0.207,20,1.2,0.1
120,318.7,1.80,0.0072,0.203,20,45.0,3.4
"""

    def _mapear(self, csv):
        return ae.mapear_dataset(pd.read_csv(io.StringIO(csv)))

    def test_unidades_psi(self):
        out, rep = self._mapear(self.PSI)
        self.assertTrue(rep["ok"])
        self.assertAlmostEqual(out.temp_c.iloc[0], 23.35, delta=0.01)   # K -> °C
        self.assertAlmostEqual(out.temp_c.iloc[-1], 45.55, delta=0.01)
        self.assertAlmostEqual(out.o2_pct.iloc[0], 20.9, delta=0.01)    # fracción -> %
        self.assertAlmostEqual(out.co2_ppm.iloc[0], 4100, delta=1)      # fracción -> ppm
        self.assertAlmostEqual(out.radiative_heat_flux_kwm2.iloc[-1], 1.80, delta=0.01)
        self.assertAlmostEqual(out.airflow_cms.iloc[0], 20.0, delta=0.01)  # "cm s" NO es m/s

    def test_conserva_tiempos_reales(self):
        out, _ = self._mapear(self.PSI)
        self.assertEqual(out.timestamp_sec.tolist(), [0, 60, 120])

    def test_rechaza_sin_temperatura(self):
        out, rep = self._mapear("t,O2 (%),CO2 (ppm),CO (ppm)\n0,20.9,4000,1\n10,20.8,4050,1.5\n")
        self.assertFalse(rep["ok"])
        self.assertIn("temp_c", rep["missing"])

    def test_rechaza_sin_gases(self):
        out, rep = self._mapear("t,Temp (C)\n0,23\n10,24\n")
        self.assertFalse(rep["ok"])

    def test_ms_a_cms(self):
        out, _ = self._mapear("t,temp (C),flow (m/s),O2 (%),CO2 (ppm)\n0,23,0.20,20.9,4000\n5,24,0.25,20.8,4050\n")
        self.assertAlmostEqual(out.airflow_cms.iloc[0], 20.0, delta=0.01)
        self.assertAlmostEqual(out.airflow_cms.iloc[1], 25.0, delta=0.01)

    def test_fahrenheit_y_w_m2(self):
        out, _ = self._mapear("t,Temp (F),Rad (W/m2),O2 (%),CO2 (ppm)\n0,73.4,20,20.9,4000\n10,75.2,350,20.8,4050\n")
        self.assertAlmostEqual(out.temp_c.iloc[0], 23.0, delta=0.05)
        self.assertAlmostEqual(out.radiative_heat_flux_kwm2.iloc[1], 0.35, delta=0.001)

    def test_fraccion_sin_unidades(self):
        out, rep = self._mapear(
            "t,Temp (C),O2,CO2\n0,23,0.209,0.0041\n5,23.1,0.209,0.0042\n")
        self.assertTrue(rep["ok"])
        self.assertAlmostEqual(out.o2_pct.iloc[0], 20.9, delta=0.02)
        self.assertAlmostEqual(out.co2_ppm.iloc[0], 4100, delta=15)

    def test_informe_declara_ausentes(self):
        out, rep = self._mapear(self.PSI)
        self.assertEqual(len(rep["mapped"]), 7)
        self.assertEqual(rep["missing"], ["smoke_obscuration_pct_m"])
        estados = {c["canal"]: c["estado"] for c in rep["channels"]}
        self.assertEqual(estados["smoke_obscuration_pct_m"], "default")


class TestMotor(unittest.TestCase):
    """Casos límite del motor que ya rompieron una vez."""

    def test_umbral_con_baseline_constante(self):
        plano = pd.DataFrame({
            "timestamp_sec": range(120), "temp_c": 23.0, "o2_pct": 20.9, "co_ppm": 0.0,
            "co2_ppm": 4000.0, "hcn_ppm": 0.0, "airflow_cms": 12.0,
            "smoke_obscuration_pct_m": 0.0, "radiative_heat_flux_kwm2": 0.0})
        d = ae.detectar_anomalias(plano)
        self.assertEqual(int(d.ia_alerta.sum()), 0)

    def test_dataframe_vacio(self):
        with self.assertRaises(ValueError):
            ae.detectar_anomalias(pd.DataFrame(columns=ps.COLS))

    def test_ventaja_en_segundos_reales(self):
        df = ps.simular_escenario(2, ISS, 0).iloc[::2].reset_index(drop=True)
        df["timestamp_sec"] = df.index * 2
        v = ae.calcular_ventaja_deteccion(ae.detectar_anomalias(df))
        ts = df["timestamp_sec"].to_numpy()
        self.assertIn(v["pyroguard_seg"], ts.tolist())
        self.assertIn(v["tradicional_seg"], ts.tolist())

    def test_protocolo_incluye_delta_real(self):
        df = ps.simular_escenario(2, ISS, 0)
        p = ae.generar_protocolo_respuesta(df)
        self.assertAlmostEqual(p["temp_baseline_c"], float(df.temp_c.iloc[0]), delta=0.01)
        self.assertEqual(len(p["acciones_inmediatas"]), 5)


class TestDatasetDemo(unittest.TestCase):
    """El CSV que se sube en el cierre del guion."""

    def test_cifras_del_guion(self):
        self.assertTrue(DEMO.exists(), f"falta {DEMO}")
        out, rep = ae.mapear_dataset(pd.read_csv(DEMO))
        self.assertTrue(rep["ok"])
        self.assertEqual(len(out), 200)
        self.assertEqual(len(rep["mapped"]), 7)

        d = ae.detectar_anomalias(out)
        v = ae.calcular_ventaja_deteccion(d)
        p = ae.generar_protocolo_respuesta(out)
        self.assertAlmostEqual(d.miri_score.max(), 65.5, delta=0.3)
        self.assertAlmostEqual(out.co_ppm.max(), 175, delta=1.5)
        self.assertAlmostEqual(out.co2_ppm.max(), 12291, delta=40)
        self.assertAlmostEqual(out.radiative_heat_flux_kwm2.max(), 2.65, delta=0.02)
        self.assertEqual(v["pyroguard_seg"], 111)
        self.assertEqual(v["tradicional_seg"], 183)
        self.assertEqual(v["ventaja_seg"], 72)
        self.assertEqual(p["nivel_amenaza"], "CRÍTICO")


class TestLiveISS(unittest.TestCase):
    """Cliente TLCP sin red: idempotencia y parseo."""

    def test_start_idempotente(self):
        feed = iss_live.LiveISS()
        calls, ev = [], threading.Event()
        feed.client._run = lambda: (calls.append(1), ev.wait(2))
        feed.start()
        feed.start()
        self.assertEqual(len(calls), 1)
        ev.set()
        feed.stop()
        self.assertFalse(feed.client._started)

    def test_coma_decimal_europea(self):
        feed = iss_live.LiveISS()
        feed._rows.clear()
        feed._on_update("U,1,USLAB000059,23,4")
        feed._on_update("U,1,USLAB000059,#")     # nulo: se ignora
        df = feed.frame()
        self.assertEqual(len(df), 1)
        self.assertAlmostEqual(float(df.cabin_temp_c.iloc[0]), 23.4, delta=0.001)


if __name__ == "__main__":
    unittest.main(verbosity=2)
