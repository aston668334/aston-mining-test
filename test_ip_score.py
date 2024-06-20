from dotenv import load_dotenv
import pandas as pd
import os
import ipaddress
import json
import requests
load_dotenv()


# Function to check if IP is within the same /24 subnet
def is_same_subnet(ip1, ip2):
    ip1_subnet = ipaddress.ip_network(ip1 + '/24', strict=False)
    return ipaddress.ip_address(ip2) in ip1_subnet

# Function to read proxy list from a file
def read_proxy_list(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Function to filter proxy IPs that are not in the same subnet as any bad IPs
def filter_proxies(proxy_list, bad_ip_list):
    filtered_proxies = []
    for proxy in proxy_list:
        proxy_ip = proxy.split('//')[1].split(':')[0]  # Extract IP address from URL
        if not any(is_same_subnet(bad_ip, proxy_ip) for bad_ip in bad_ip_list):
            filtered_proxies.append(proxy)
    return filtered_proxies

if __name__ == "__main__":
    max_page = 50
    once_per_request = 100
    API_KEY = os.getenv("API_KEY")
        # Define the CSV file name
    payload = {}
    headers = {
    'Authorization': str(API_KEY)
    }

    df = pd.DataFrame([])

    for i in range(max_page):
        url = "https://api.getgrass.io/devices?input=%7B%22limit%22:{},%22offset%22:{}%7D".format(once_per_request,i * once_per_request)
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        json_data = json.loads(response.text)
        # Extract the relevant data
        devices_data = json_data['result']['data']['data']
        # Create a DataFrame
        devices_data = pd.DataFrame(devices_data)
        df = pd.concat([df,devices_data], axis= 0)
        df = df.drop_duplicates()

    bad_ip_list = []
    for indx, row in df.iterrows():
        ipAddress = row['ipAddress']
        ipScore = row['ipScore']
        totalUptime = row['totalUptime']
        if (totalUptime > 600) and (ipScore == 0):
            bad_ip_list.append(ipAddress)
    # Write the bad IPs to bad_ip.txt
    with open('bad_ip.txt', 'w') as bad_ip_file:
        for bad_ip in bad_ip_list:
            bad_ip_file.write(bad_ip + '\n')
            
    # Read the IPs back from the file
    with open('bad_ip.txt', 'r') as bad_ip_file:
        ips = bad_ip_file.readlines()

    # Remove duplicates by converting to a set, then back to a list
    unique_ips = list(set(ips))
    # Sort the list to maintain a consistent order (optional)
    unique_ips.sort()

    # Write the unique IPs back to the file
    with open('bad_ip.txt', 'w') as bad_ip_file:
        for ip in unique_ips:
            bad_ip_file.write(ip)

    # Read the proxy list from good-grass-proxy-list.txt
    proxy_list = read_proxy_list('good-grass-proxy-list.txt')

    # Get the filtered list of proxy IPs
    filtered_proxies = filter_proxies(proxy_list, bad_ip_list)
    # Write the filtered proxies to proxy-list.txt
    with open('good-grass-proxy-list-filterd.txt', 'w') as proxy_file:
        for proxy in filtered_proxies:
            proxy_file.write(proxy + '\n')