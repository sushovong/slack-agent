import os
from dotenv import load_dotenv
import requests

load_dotenv()


def execute_adx_query(database: str, query: str):
    """
    Executes a query against Azure Data Explorer (ADX) using interactive authentication.
    
    Args:
        database (str): The name of the ADX database to query
        query (str): The Kusto query string to execute
        
    Returns:
        KustoResponseDataSet: The response from ADX containing the query results
    """
    # Get API endpoint from environment variable
    api_endpoint = "http://10.66.12.122:8000/query/clusters/sin0/db/kubernetes"
    if not api_endpoint:
        raise ValueError("ADX_API_ENDPOINT environment variable not set")
    
    # Prepare the request payload
    payload = {
        'database': database,
        'query': query
    }
    
    # Make the API call
    response = requests.post(api_endpoint, json=payload)
    response.raise_for_status()
    
    return response.json()


# tools response
def get_latency_report_for_preorder_service(service_name):
    """
    Retrieves latency metrics for the specified service over the last 30 minutes
    Args:
        service_name (str): Name of the service to get latency report for
    Returns:
        dict: Latency report
    """
    
    response = execute_adx_query(
        database= "kubernetes",
        query= "let _containerName = 'preorder-service'; HttpRequests | where Timestamp >= ago (12h)   | where Properties.req_container == _containerName    | summarize p99 = percentiles(Duration, 99) by Host"
    )

    # Convert Kusto response to a list of dictionaries
    results = []
    row_data = response["rowData"]

    for row in row_data:
        host = row["Host"]
        p99 = row["p99"]
        #   print(f"Host: {host}, p99: {p99}")
        results.append({"Host": {host}, "p99": {p99}})


    return {
        "status": "success",
        "service": service_name,
        "timeframe": "last 30 minutes",
        "results": results,
    }


def get_5xx_error_rate_over_last_1hr(service_name, resource_name):
    response = execute_adx_query(
        database= "kubernetes", 
        query= f"""
        let _containerName = '{service_name}';
        let _resourceAPI = '{resource_name}';
        let _statusCodes = dynamic([500, 503, 504]);
        HttpRequests
        | where Timestamp >= ago(24h)
        | where Container == _containerName
        | where StatusCode in (_statusCodes)
        | where tostring(Properties.loc) has (_resourceAPI)
        | join Exceptions on $left.Pod == $right.Pod and $left.TraceId == $right.TraceId 
        | where Container == _containerName
        | project Path, Message, Stacktrace, Timestamp, Duration
        """
    )

    # Convert Kusto response to a list of dictionaries
    print(response)
    results = []
    row_data = response["rowData"]

    for row in row_data:
        results.append({
            "path": row["Path"],
            "message": row["Message"],
            "stacktrace": row["Stacktrace"],
            "timestamp": str(row["Timestamp"]),  # Convert datetime to string
            "duration": float(row["Duration"])
        })
        results.append({"Host": {host}, "p99": {p99}})

    return {
        "status": "success",
        "service": service_name,
        "resource": resource_name,
        "timeframe": "last 24 hours",
        "error_count": len(results),
        "errors": results
    }



# process the
def process_tool_call(tool_name, tool_input):
    if tool_name == "get_latency_report_for_preorder_service":
        return get_latency_report_for_preorder_service(tool_input["service_name"])
    if tool_name == "get_5xx_error_rate_over_last_1hr":
        return get_5xx_error_rate_over_last_1hr(tool_input["service_name"], tool_input["resource_name"])
