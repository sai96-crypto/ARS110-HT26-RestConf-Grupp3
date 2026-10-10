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

headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}



def bas_url(enhet):
    return f"https://{enheter[enhet]}/restconf/data/"


def patch(enhet, path, data, beskrivning):
    try:
        svar = requests.patch(
            bas_url(enhet) + path,
            auth=(username, password),
            headers=headers,
            json=data,
            verify=False,
            timeout=10
        )
        if svar.status_code in [200, 201, 204]:
            print(f"[OK]  {enhet} {beskrivning}")
            return True
        print(f"[FEL] {enhet} {beskrivning}: {svar.status_code}")
        print(svar.text)
    except requests.exceptions.RequestException as e:
        print(f"[FEL] {enhet} {beskrivning}: {e}")
    return False


def delete(enhet, path):
    # om det visar 404 betyder det att det redan var borta, det är ok
    try:
        requests.delete(
            bas_url(enhet) + path,
            auth=(username, password),
            headers=headers,
            verify=False,
            timeout=10
        )
    except requests.exceptions.RequestException:
        pass


def koda(namn):
    return namn.replace("/", "%2F")


# conf av hsotnames
def hostname(enhet):
    patch(
        enhet,
        "Cisco-IOS-XE-native:native/hostname",
        {"Cisco-IOS-XE-native:hostname": enhet},
        "hostname"
    )



def interface(enhet, namn, ip, mask):
    data = {
        "ietf-interfaces:interface": {
            "name": namn,
            "type": "iana-if-type:ethernetCsmacd",
            "enabled": True,
            "ietf-ip:ipv4": {
                "address": [{"ip": ip, "netmask": mask}]
            }
        }
    }
    patch(
        enhet,
        "ietf-interfaces:interfaces/interface=" + koda(namn),
        data,
        f"{namn} {ip}"
    )



def serial(enhet, namn, ip, mask):
    data = {
        "Cisco-IOS-XE-native:Serial": [{
            "name": namn,
            "ip": {
                "address": {
                    "primary": {"address": ip, "mask": mask}
                }
            }
        }]
    }
    patch(
        enhet,
        "Cisco-IOS-XE-native:native/interface/Serial=" + koda(namn),
        data,
        f"Serial{namn} {ip}"
    )

    delete(
        enhet,
        "Cisco-IOS-XE-native:native/interface/Serial=" + koda(namn) + "/shutdown"
    )

#conf av EIGRP
def eigrp(enhet, networks, redistribuera_static=False):
    instans = {
        "autonomous-system": 100,
        "network": {
            "address-wildcard": [
                {"ipv4-address": ip, "wildcard": wc} for ip, wc in networks
            ]
        }
    }

    if redistribuera_static:
        instans["redistribute"] = {
            "static": {
                "metric": {
                    "bandwidth": 1544,
                    "delay": 2000,
                    "reliability": 255,
                    "load": 1,
                    "mtu": 1500
                }
            }
        }

    data = {
        "Cisco-IOS-XE-eigrp:router-eigrp": {
            "eigrp": {"classic-mode": [instans]}
        }
    }
    patch(
        enhet,
        "Cisco-IOS-XE-native:native/router/Cisco-IOS-XE-eigrp:router-eigrp",
        data,
        "EIGRP AS 100"
    )

    delete(
        enhet,
        "Cisco-IOS-XE-native:native/router/Cisco-IOS-XE-eigrp:router-eigrp"
        "/eigrp/classic-mode=100/auto-summary"
    )


# DEFAULT ROUTE (native)

def default_route(enhet, next_hop):
    data = {
        "Cisco-IOS-XE-native:route": {
            "ip-route-interface-forwarding-list": [{
                "prefix": "0.0.0.0",
                "mask": "0.0.0.0",
                "fwd-list": [{"fwd": next_hop}]
            }]
        }
    }
    patch(
        enhet,
        "Cisco-IOS-XE-native:native/ip/route",
        data,
        f"default route via {next_hop}"
    )


# MAX

print("\n----- MAX -----")
hostname("MAX")
interface("MAX", "GigabitEthernet0/0/0", "192.168.1.2", "255.255.255.0")  # Internet
serial("MAX", "0/1/0", "192.168.2.5", "255.255.255.252")                   # mot McD
serial("MAX", "0/1/1", "192.168.2.1", "255.255.255.252")                   # mot BK
default_route("MAX", "192.168.1.1")
eigrp("MAX", [
    ("192.168.2.4", "0.0.0.3"),  
    ("192.168.2.0", "0.0.0.3")    
], redistribuera_static=True)


# McD

print("\n----- McD -----")
hostname("McD")
serial("McD", "0/1/0", "192.168.2.6", "255.255.255.252")                   # mot MAX
interface("McD", "GigabitEthernet0/0/0", "10.10.13.1", "255.255.255.0")   # PC
eigrp("McD", [
    ("192.168.2.4", "0.0.0.3"),
    ("10.10.13.0", "0.0.0.255")
])


# BK

print("\n----- BK -----")
hostname("BK")
serial("BK", "0/1/1", "192.168.2.2", "255.255.255.252")                    # mot MAX
interface("BK", "GigabitEthernet0/0/0", "10.10.12.1", "255.255.255.128")  # PC
eigrp("BK", [
    ("192.168.2.0", "0.0.0.3"),
    ("10.10.12.0", "0.0.0.127")
])

# om allt är confad
print("\nConfen är klar")
