import os
import globus_sdk
from globus_sdk.tokenstorage import SimpleJSONFileAdapter

MY_FILE_ADAPTER = SimpleJSONFileAdapter(os.path.expanduser("~/.sdk-manage-flow.json"))

def do_login_flow(scopes, native_client):
    native_client.oauth2_start_flow(requested_scopes=scopes,
                                    refresh_tokens=True)
    authorize_url = native_client.oauth2_get_authorize_url()
    print(f"Please go to this URL and login:\n\n{authorize_url}\n")
    auth_code = input("Please enter the code here: ").strip()
    tokens = native_client.oauth2_exchange_code_for_tokens(auth_code)
    return tokens


def get_authorizer(client_id, flow_id=None):

    native_client = globus_sdk.NativeAppAuthClient(client_id)

    if flow_id:
        resource_server = flow_id
        scopes = globus_sdk.SpecificFlowClient(flow_id).scopes.user
    else:
        resource_server = globus_sdk.FlowsClient.resource_server
        scopes = [
            globus_sdk.FlowsClient.scopes.manage_flows,
            globus_sdk.FlowsClient.scopes.run_status,
        ]

     # try to load the tokens from the file, possibly returning None
    if MY_FILE_ADAPTER.file_exists():# and not collection_ids:
        tokens = MY_FILE_ADAPTER.get_token_data(flow_id)
    else:
        tokens = None

    if tokens is None:
        # do a login flow, getting back initial tokens
        response = do_login_flow(scopes, native_client)
        # now store the tokens and pull out the correct token
        MY_FILE_ADAPTER.store(response)
        tokens = response.by_resource_server[resource_server]

    return globus_sdk.RefreshTokenAuthorizer(
        tokens["refresh_token"],
        native_client,
        access_token=tokens["access_token"],
        expires_at=tokens["expires_at_seconds"],
    )


def get_flows_client(client_id):
    return globus_sdk.FlowsClient(authorizer=get_authorizer(client_id))


def get_specific_flow_client(flow_id, client_id):
    authorizer = get_authorizer(client_id, flow_id)
    return globus_sdk.SpecificFlowClient(flow_id, authorizer=authorizer)
