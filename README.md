# ARS110 – RESTCONF and EIGRP
Group 3 – Fatimah and Neda

This is our network automation project for the ARS110 course. We use Python and RESTCONF to configure three Cisco routers: MAX, McD and BK.

# Python files

- `skill.py` – configures the router names, IP addresses, EIGRP AS 100 and default route on MAX.
- `robert.py` – checks the router configuration and shows which parts are correct or incorrect.

## Before running

Python 3 and the requests library are required.

Install requests:

```bash
pip install requests
```

RESTCONF must be enabled on the routers, and the management IP addresses must be reachable.

## Run the programs

First, run the configuration script:

```bash
python skill.py
```

Then check the configuration:

```bash
python robert.py
```

The checking script prints OK or FEL for each test and shows GODKÄND or UNDERKÄND at the end.

## Note

The scripts use login details for our school lab. HTTPS certificate verification is disabled for testing in the lab environment only.
