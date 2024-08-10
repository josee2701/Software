import unittest

from django.test import TestCase
from whitelabel.models import Coin, Company

from .models import DataPlan


class DataPlanTestCase(TestCase):
    def setUp(self):
        # Creamos instancias de modelos relacionados necesarios para el test
        coin = Coin.objects.create(name="Dollar", symbol="$")
        company = Company.objects.create(name="Empresa de Prueba")

        # Creamos un plan de datos para usar en los tests
        self.data_plan = DataPlan.objects.create(
            name="Plan de Prueba",
            coin=coin,
            price=10.99,
            company=company,
            operator="Operador de Prueba",
            visible=True,
        )

    def test_data_plan_name(self):
        self.assertEqual(self.data_plan.name, "Plan de Prueba")

    def test_data_plan_coin(self):
        self.assertEqual(self.data_plan.coin.name, "Dollar")
        self.assertEqual(self.data_plan.coin.symbol, "$")

    def test_data_plan_price(self):
        self.assertEqual(self.data_plan.price, 10.99)

    def test_data_plan_company(self):
        self.assertEqual(self.data_plan.company.name, "Empresa de Prueba")

    def test_data_plan_operator(self):
        self.assertEqual(self.data_plan.operator, "Operador de Prueba")

    def test_data_plan_visible(self):
        self.assertTrue(self.data_plan.visible)

    def test_data_plan_str(self):
        self.assertEqual(str(self.data_plan), "Plan de Prueba")


if __name__ == "__main__":
    unittest.main()
