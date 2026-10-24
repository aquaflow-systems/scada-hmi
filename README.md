# scada-hmi

Operator supervision interface. Polls all 5 PLCs over Modbus -- plaintext for
`plc-dosing`, Modbus Security (TLS) for the rest -- and displays plant state the
way a control-room operator would see it.

Depends on `plc-fleet` (installed as a package) for the register map's
encode/decode logic, so register addresses and scaling only live in one place.

## Running standalone

```bash
pip install -r requirements.txt
python -m src.main
```

Serves at http://localhost:8081. Reads PLC connection details from
`AquaFlow-Systems/plant-spec/network-plan.md`.

## Tests

```bash
pytest
```