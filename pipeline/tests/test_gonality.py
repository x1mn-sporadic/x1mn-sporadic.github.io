"""Regression checks for the sporadicity consequences of Varivoda's Theorem D."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build
import knowledge
from common import KNOWLEDGE_DIR, read_json


class GonalityClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tables = build.load_tables()
        magma = read_json(KNOWLEDGE_DIR / "curves_magma.json")
        cls.curves = {
            (rec["m"], rec["n"]): build.curve_record(
                rec["m"], rec["n"], rec, tables.get((rec["m"], rec["n"]))
            )
            for rec in magma["curves"]
        }

    def test_theorem_d_and_earlier_upper_bound_credit(self):
        # Theorem D, page 2, in order N = 41, ..., 50.
        expected = [22, 12, 24, 15, 18, 19, 29, 16, 21, 15]
        for n, gamma in zip(range(41, 51), expected):
            with self.subTest(n=n):
                gon = self.curves[1, n]["gonality"]
                self.assertEqual((gon["lb"], gon["ub"], gon["exact"]), (gamma, gamma, True))
                self.assertEqual(gon["lb_source"], "Varivoda26")
                self.assertEqual(gon["ub_source"], "DvH14")

    def test_rank_zero_gives_sporadicity_below_gonality(self):
        for n in [41, 42, 44, 45, 46, 47, 48, 49, 50]:
            curve = self.curves[1, n]
            gamma = curve["gonality"]["lb"]
            self.assertEqual(curve["rank"]["value"], 0)
            for degree in range(1, gamma):
                with self.subTest(n=n, degree=degree):
                    self.assertIn(str(degree), curve["degrees_finite"])
                    result = knowledge.classify_point(curve, degree)
                    self.assertEqual(result["sporadic"]["value"], "yes")
                    self.assertEqual(result["isolated"]["value"], "yes")
                    self.assertEqual(result["infinite_in_degree"]["value"], "no")
            self.assertIn("Varivoda26", result["sporadic"]["sources"])
            self.assertIn("DvH14", result["sporadic"]["sources"])
            self.assertIn("RankZeroLemma", result["sporadic"]["sources"])

    def test_gonality_is_a_strict_sporadicity_boundary(self):
        for n in [41, 42, 44, 45, 46, 47, 48, 49, 50]:
            curve = self.curves[1, n]
            gamma = curve["gonality"]["lb"]
            with self.subTest(n=n):
                self.assertNotIn(str(gamma), curve["degrees_finite"])
                at_boundary = knowledge.classify_point(curve, gamma)
                self.assertEqual(at_boundary["infinite_in_degree"]["value"], "yes")
                self.assertEqual(at_boundary["sporadic"]["value"], "no")
                above = knowledge.classify_point(curve, gamma + 1)
                self.assertEqual(above["sporadic"]["value"], "no")

    def test_level_43_does_not_inherit_rank_zero(self):
        curve = self.curves[1, 43]
        self.assertIsNone(curve["rank"]["value"])
        self.assertEqual(knowledge.classify_point(curve, 11)["sporadic"]["value"], "yes")
        for degree in [12, 14, 23]:
            with self.subTest(degree=degree):
                result = knowledge.classify_point(curve, degree, {"p1_isolated": True})
                self.assertEqual(result["sporadic"]["value"], "maybe")
                self.assertEqual(result["isolated"]["value"], "maybe")

    def test_isolated_point_can_exceed_the_sporadicity_boundary(self):
        result = knowledge.classify_point(self.curves[1, 49], 22, {"p1_isolated": True})
        self.assertEqual(result["sporadic"]["value"], "no")
        self.assertEqual(result["isolated"]["value"], "yes")
        self.assertEqual(result["status"], "certified")

    def test_q_gonality_result_is_not_applied_over_cyclotomic_fields(self):
        self.assertNotEqual(self.curves[3, 12]["gonality"]["source"], "Varivoda26")


if __name__ == "__main__":
    unittest.main()
