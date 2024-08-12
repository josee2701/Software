# apps/powerbi/embed_service.py

import logging
import uuid

import requests
from django.db import connection

from .azure_utils import get_power_bi_headers


class EmbedService:
    @staticmethod
    def get_embed_token_for_rdl_report(workspace_id, report_id, access_level="view"):
        headers = get_power_bi_headers()
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/GenerateToken"
        body = {"accessLevel": access_level}
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_embed_token(report_id, dataset_ids, target_workspace_id=None):
        headers = get_power_bi_headers()
        url = f"https://api.powerbi.com/v1.0/myorg/GenerateToken"
        body = {
            "datasets": [{"id": str(dataset_id)} for dataset_id in dataset_ids],
            "reports": [{"id": str(report_id)}],
        }
        if target_workspace_id:
            body["targetWorkspaces"] = [{"id": str(target_workspace_id)}]

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_embed_params(workspace_id, report_id, additional_dataset_id=None):
        headers = get_power_bi_headers()

        url_report = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
        url_pages = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/pages"

        logging.info(f"Requesting report info from {url_report}")
        report_response = requests.get(url_report, headers=headers)
        logging.info(f"Report response status: {report_response.status_code}")
        logging.info(f"Report response content: {report_response.content}")

        report_response.raise_for_status()
        pbi_report = report_response.json()

        logging.info(f"Requesting report pages from {url_pages}")
        pages_response = requests.get(url_pages, headers=headers)
        logging.info(f"Pages response status: {pages_response.status_code}")
        logging.info(f"Pages response content: {pages_response.content}")

        pages_response.raise_for_status()
        pbi_page = pages_response.json()

        is_rdl_report = not pbi_report.get("datasetId")

        if is_rdl_report:
            embed_token = EmbedService.get_embed_token_for_rdl_report(
                workspace_id, report_id
            )
        else:
            dataset_ids = [uuid.UUID(pbi_report["datasetId"])]
            if additional_dataset_id:
                dataset_ids.append(additional_dataset_id)
            embed_token = EmbedService.get_embed_token(
                report_id, dataset_ids, workspace_id
            )

        embed_reports = [
            {
                "ReportId": str(pbi_report["id"]),
                "ReportName": pbi_report["name"],
                "EmbedUrl": pbi_report["embedUrl"],
            }
        ]

        embed_params = {
            "ReportId": str(pbi_report["id"]),
            "EmbedUrl": pbi_report["embedUrl"],
            "EmbedToken": embed_token["token"],
        }

        return embed_params

    @staticmethod
    def get_basic_params(advanced_id):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT [table], [column], [logical_operator], [values], [filter_type]
                FROM PowerBI.report_parameters
                WHERE advanced_id = %s and [filter_type] = 'BasicFilter'
            """,
                [advanced_id],
            )
            db_result = cursor.fetchall()
            result = [
                {
                    "table": row[0],
                    "column": row[1],
                    "logical_operator": row[2],
                    "values": row[3],
                    "filterType": row[4],
                }
                for row in db_result
            ]
            return result

    @staticmethod
    def get_advanced_params(advanced_id):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT [table], [column], [logical_operator], [condition_op1], [condition_va1], [condition_op2], [condition_va2], [filter_type]
                FROM PowerBI.report_parameters
                WHERE advanced_id = %s and [filter_type] = 'AdvancedFilter'
            """,
                [advanced_id],
            )
            db_result = cursor.fetchall()

            result = []
            for row in db_result:
                conditions = []
                if row[3] and row[4]:
                    conditions.append({"operator": row[3], "value": row[4]})
                if row[5] and row[6]:
                    conditions.append({"operator": row[5], "value": row[6]})

                result.append(
                    {
                        "table": row[0],
                        "column": row[1],
                        "logical_operator": row[2],
                        "conditions": conditions,
                        "filterType": row[7],
                    }
                )
            return result

    @staticmethod
    def get_groups():
        headers = get_power_bi_headers()
        url = "https://api.powerbi.com/v1.0/myorg/groups"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_reports_in_group(group_id):
        headers = get_power_bi_headers()
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/reports"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_embed_user(user_id):
        embedded_lists = []
        embed_reports = []

        # Obtener los datos de la base de datos usando SQL directo
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT [id_report], [id_workspace], [is_report], [id]
                FROM [PowerBI].[advanced_analytical]
                WHERE user_id = %s
            """,
                [user_id],
            )
            db_result = cursor.fetchall()
            result = [
                {
                    "reportId": row[0],
                    "workspaceId": row[1],
                    "Type": row[2],
                    "advancedId": row[3],
                }
                for row in db_result
            ]

            print(result)
        headers = get_power_bi_headers()

        print(result)

        for datos in result:
            try:
                if datos["Type"] == False:
                    url = f"https://api.powerbi.com/v1.0/myorg/groups/{datos['workspaceId']}/reports"
                    pbi_workspace = (
                        requests.get(url, headers=headers).json().get("value", [])
                    )
                    embedded_lists.extend(
                        [
                            {
                                "WorkspaceId": datos["workspaceId"],
                                "ReportId": report["id"],
                                "ReportName": report["name"],
                            }
                            for report in pbi_workspace
                            if report["name"] != "Report Usage Metrics Report"
                        ]
                    )
                elif datos["Type"] == True:
                    additional_params = {}
                    if datos["advancedId"]:
                        basic_params = EmbedService.get_basic_params(
                            datos["advancedId"]
                        )
                        advanced_params = EmbedService.get_advanced_params(
                            datos["advancedId"]
                        )
                        combined_params = basic_params + advanced_params

                    url = f"https://api.powerbi.com/v1.0/myorg/groups/{datos['workspaceId']}/reports/{datos['reportId']}"
                    pbi_report = requests.get(url, headers=headers).json()
                    embedded_lists.append(
                        {
                            "WorkspaceId": datos["workspaceId"],
                            "ReportId": pbi_report["id"],
                            "ReportName": pbi_report["name"],
                            "Parameters": combined_params,
                        }
                    )
            except Exception as e:
                logging.error(str(e))

        for report in embedded_lists:
            try:
                url = f"https://api.powerbi.com/v1.0/myorg/groups/{report['WorkspaceId']}/reports/{report['ReportId']}/pages"
                pbi_pages = requests.get(url, headers=headers).json().get("value", [])

                print(pbi_pages)

                if len(pbi_pages) > 1:
                    embed_reports.append(
                        {
                            "WorkspaceId": report["WorkspaceId"],
                            "ReportId": report["ReportId"],
                            "ReportName": report["ReportName"],
                            "Pages": pbi_pages,
                            "Page": len(pbi_pages) > 1,
                            "Parameters": report.get("Parameters", {}),
                        }
                    )
                else:
                    embed_reports.append(
                        {
                            "WorkspaceId": report["WorkspaceId"],
                            "ReportId": report["ReportId"],
                            "ReportName": report["ReportName"],
                            "Pages": {},
                            "Page": False,
                            "Parameters": report.get("Parameters", {}),
                        }
                    )

            except Exception as e:
                logging.error(str(e))

        embed_reports = sorted(embed_reports, key=lambda report: report["ReportName"])
        return embed_reports
