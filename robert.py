import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

username = "admin"
password = "cisco"

enheter = {
    "MAX": "100.100.100.1",
    "McD": "100.100.100.2",
    "BK": "100.100.100.3"
}

headers = {"Accept": "application/yang-data+json"}

fel = 0





def get(enhet, path):
    url = f"https://{enheter[enhet]}/restconf/data/{path}"
    try:
        svar = requests.get(
            url,
            auth=(username, password),
            headers=headers,
            verify=False,
            timeout=10
        )
        if svar.status_code == 200:
            return svar.json()
    except requests.exceptions.RequestException:
        pass
    return None


def forsta(varde):
    if isinstance(varde, list):
        return varde[0] if varde else {}
    return varde or {}


def resultat(ok, text):
    global fel
    if ok:
        print("[OK] ", text)
    else:
        print("[FEL]", text)
        fel += 1




def hostname(enhet):
    data = get(enhet, "Cisco-IOS-XE-native:native/hostname")
    ok = data is not None and data.get("Cisco-IOS-XE-native:hostname") == enhet
    resultat(ok, f"{enhet} hostname")



def interface(enhet, namn, ratt_ip, ratt_mask):
    data = get(
        enhet,
        "Cisco-IOS-XE-interfaces-oper:interfaces/interface=" + namn.replace("/", "%2F")
    )

    intf = forsta((data or {}).get("Cisco-IOS-XE-interfaces-oper:interface"))

    resultat(
        intf.get("ipv4") == ratt_ip and intf.get("ipv4-subnet-mask") == ratt_mask,
        f"{enhet} {namn} {ratt_ip} {ratt_mask}"
    )
    resultat(
        intf.get("oper-status") == "if-oper-state-ready",
        f"{enhet} {namn} är uppe"
    )


def eigrp(enhet, ratt_neighbors):
    data = get(enhet, "Cisco-IOS-XE-eigrp-oper:eigrp-oper-data")

    instances = (data or {}).get(
        "Cisco-IOS-XE-eigrp-oper:eigrp-oper-data", {}
    ).get("eigrp-instance", [])

    neighbors = []
    as100 = False

    for instance in instances:
        if int(instance.get("as-num", 0)) == 100:
            as100 = True
            for intf in instance.get("eigrp-interface", []):
                for nbr in intf.get("eigrp-nbr", []):
                    neighbors.append(nbr.get("nbr-address"))

    resultat(as100, f"{enhet} EIGRP AS 100")

    for nbr in ratt_neighbors:
        resultat(nbr in neighbors, f"{enhet} EIGRP neighbor {nbr}")


def route(enhet, prefix):
    data = get(enhet, "Cisco-IOS-XE-fib-oper:fib-oper-data")

    instances = (data or {}).get(
        "Cisco-IOS-XE-fib-oper:fib-oper-data", {}
    ).get("fib-ni-entry", [])

    for instance in instances:
        if "default" in instance.get("instance-name", "").lower():
            for r in instance.get("fib-entries", []):
                if r.get("ip-addr") == prefix:
                    resultat(True, f"{enhet} route {prefix}")
                    return

    resultat(False, f"{enhet} route {prefix}")



def default_route(enhet, next_hop):
    data = get(enhet, "Cisco-IOS-XE-native:native/ip/route")

    routes = (data or {}).get(
        "Cisco-IOS-XE-native:route", {}
    ).get("ip-route-interface-forwarding-list", [])

    for r in routes:
        if r.get("prefix") == "0.0.0.0" and r.get("mask") == "0.0.0.0":
            for fwd in r.get("fwd-list", []):
                if fwd.get("fwd") == next_hop:
                    resultat(True, f"{enhet} default route via {next_hop}")
                    return

    resultat(False, f"{enhet} default route via {next_hop}")



print("\n- MAX -")
hostname("MAX")
interface("MAX", "GigabitEthernet0/0/0", "192.168.1.2", "255.255.255.0")
interface("MAX", "Serial0/1/0", "192.168.2.5", "255.255.255.252")
interface("MAX", "Serial0/1/1", "192.168.2.1", "255.255.255.252")
eigrp("MAX", ["192.168.2.6", "192.168.2.2"])
route("MAX", "10.10.12.0/25")
route("MAX", "10.10.13.0/24")
default_route("MAX", "192.168.1.1")




print("\n- McD -")
hostname("McD")
interface("McD", "Serial0/1/0", "192.168.2.6", "255.255.255.252")
interface("McD", "GigabitEthernet0/0/0", "10.10.13.1", "255.255.255.0")
eigrp("McD", ["192.168.2.5"])
route("McD", "10.10.13.0/24")
route("McD", "0.0.0.0/0")




print("\n- BK -")
hostname("BK")
interface("BK", "Serial0/1/1", "192.168.2.2", "255.255.255.252")
interface("BK", "GigabitEthernet0/0/0", "10.10.12.1", "255.255.255.128")
eigrp("BK", ["192.168.2.1"])
route("BK", "10.10.12.0/25")
route("BK", "0.0.0.0/0")




print("\n============================")
if fel == 0:
    print("RESULTAT: GODKÄND")
else:
    print("RESULTAT: UNDERKÄND")
    print("Antal fel:", fel)
print("============================")
