# class Test(TestCase):
#     def setUp(self) -> None:
#         Company.objects.create(
#             name="test",
#             nit=1,
#             business_name="test",
#             provider_id=None,
#             address="test",
#             phone="test",
#             country="test",
#             city="test",
#             signed_contract=True,
#             consultant="test",
#             seller="test",
#         )
#         Company.objects.create(
#             name="test2",
#             nit=2,
#             business_name="test2",
#             provider_id=2,
#             address="test2",
#             phone="test2",
#             country="test2",
#             city="test2",
#             signed_contract=True,
#             consultant="test2",
#             seller="test2",
#         )

#     def test_company(self):
#         company = Company.objects.get(name="test")
#         company2 = Company.objects.get(name="test2")
#         self.assertEqual(company.name, "test")
#         self.assertEqual(company2.name, "test2")
