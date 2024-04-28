import adal
import time
import requests
import jwt
import json
import streamlit as st
import streamlit.components.v1 as components

class EmbedTokenRequestBody:

    # Camel casing is used for the member variables as they are going to be serialized and camel case is standard for JSON keys

    datasets = None
    reports = None
    targetWorkspaces = None
    identities = None

    def __init__(self):
        self.datasets = []
        self.reports = []
        self.targetWorkspaces = []
        self.identities = []

class EmbedToken:

    # Camel casing is used for the member variables as they are going to be serialized and camel case is standard for JSON keys

    tokenId = None
    token = None
    tokenExpiry = None

    def __init__(self, token_id, token, token_expiry):
        self.tokenId = token_id
        self.token = token
        self.tokenExpiry = token_expiry

class ReportConfig:

    # Camel casing is used for the member variables as they are going to be serialized and camel case is standard for JSON keys

    reportId = None
    reportName = None
    embedUrl = None
    datasetId = None

    def __init__(self, report_id, report_name, embed_url, dataset_id):
        self.reportId = report_id
        self.reportName = report_name
        self.embedUrl = embed_url
        self.datasetId = dataset_id

class EmbedConfig:

    # Camel casing is used for the member variables as they are going to be serialized and camel case is standard for JSON keys

    tokenId = None
    accessToken = None
    tokenExpiry = None
    reportConfig = None

    def __init__(self, token_id, access_token, token_expiry, report_config):
        self.tokenId = token_id
        self.accessToken = access_token
        self.tokenExpiry = token_expiry
        self.reportConfig = report_config


resource_url = 'https://analysis.windows.net/powerbi/api'
client_id = '<>'
client_secret="<>"
tenant_id = '<>'
authority_url = 'https://login.microsoftonline.com/' + tenant_id

context = adal.AuthenticationContext(authority_url)

token_response = context.acquire_token_with_client_credentials(
    resource=resource_url,
    client_secret=client_secret,
    client_id=client_id
)

token_sp = token_response["accessToken"]

def get_embed_token_for_single_report_single_workspace(report_id, dataset_ids, target_workspace_id=None):
    '''Get Embed token for single report, multiple datasets, and an optional target workspace

    Args:
        report_id (str): Report Id
        dataset_ids (list): Dataset Ids
        target_workspace_id (str, optional): Workspace Id. Defaults to None.

    Returns:
        EmbedToken: Embed token
    '''

    request_body = EmbedTokenRequestBody()

    for dataset_id in dataset_ids:
        request_body.datasets.append({'id': dataset_id})

    request_body.reports.append({'id': report_id})

    if target_workspace_id is not None:
        request_body.targetWorkspaces.append({'id': target_workspace_id})

    # request_body.identities.append({'username': "bananas","roles":["rlspbirole"],"datasets":["<>"]})

    # Generate Embed token for multiple workspaces, datasets, and reports. Refer https://aka.ms/MultiResourceEmbedToken
    embed_token_api = 'https://api.powerbi.com/v1.0/myorg/GenerateToken'
    api_response = requests.post(embed_token_api, data=json.dumps(request_body.__dict__),
                                 headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token_sp})

    # if api_response.status_code != 200:
    #    abort(api_response.status_code, description=f'Error while retrieving Embed token\n{api_response.reason}:\t{api_response.text}\nRequestId:\t{api_response.headers.get("RequestId")}')

    # print(api_response.text)

    api_response = json.loads(api_response.text)
    embed_token = EmbedToken(api_response['tokenId'], api_response['token'], api_response['expiration'])
    return embed_token


def get_embed_params_for_single_report(workspace_id, report_id, additional_dataset_id=None):
    '''Get embed params for a report and a workspace

    Args:
        workspace_id (str): Workspace Id
        report_id (str): Report Id
        additional_dataset_id (str, optional): Dataset Id different than the one bound to the report. Defaults to None.

    Returns:
        EmbedConfig: Embed token and Embed URL
    '''

    report_url = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}'

    api_response = requests.get(report_url,
                                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token_sp})
    # print(api_response)

    # if api_response.status_code != 200:
    #    abort(api_response.status_code, description=f'Error while retrieving Embed URL\n{api_response.reason}:\t{api_response.text}\nRequestId:\t{api_response.headers.get("RequestId")}')

    api_response = json.loads(api_response.text)
    # print(api_response)
    report = ReportConfig(api_response['id'], api_response['name'], api_response['embedUrl'], api_response['datasetId'])
    dataset_ids = [api_response['datasetId']]

    # Append additional dataset to the list to achieve dynamic binding later
    if additional_dataset_id is not None:
        dataset_ids.append(additional_dataset_id)

    embed_token = get_embed_token_for_single_report_single_workspace(report_id, dataset_ids, workspace_id)
    embed_config = EmbedConfig(embed_token.tokenId, embed_token.token, embed_token.tokenExpiry, [report.__dict__])
    return embed_config, report


datasetID = "<>"
reportID = "<>"
embed_info,report = get_embed_params_for_single_report("<workspaceID>", reportID)

st.set_page_config(layout="wide")
st.header("This is a streamlit Page!")

HtmlFile = open("index.html", 'r', encoding='utf-8')

source_code = HtmlFile.read()
source_code= source_code.replace("TOREPLACEACCESSTOKEN",str(embed_info.accessToken))
source_code= source_code.replace("TOREPLACEEMBEDURL",str(report.embedUrl))
source_code= source_code.replace("datasetIDTOREPLACE",str(datasetID))
source_code= source_code.replace("reportIDToReplace",str(reportID))

print(source_code)
components.html(source_code,height=1000)
