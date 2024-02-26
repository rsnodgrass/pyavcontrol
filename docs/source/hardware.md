# Hardware Specific Details

## Xantech

### High-Density RS232 Control Cable (Xantech Part 05913665)

Some Xantech MX88/MX88ai models use high-density HD15 (or DE15) connectors for rear COM ports, thus requiring Xantech's "DB15 to DB9" adapter cable (PN 05913665). The front DB9 RS232 and USB COM ports cannot be used for device control on these models. Instead, use the rear COM ports which are already wired as a 'null modem' connection, so no use of null modem cable is required as the Transmit and Receive lines have already been interchanged.

Thanks to [@skavan](https://community.home-assistant.io/t/xantech-dayton-audio-sonance-multi-zone-amps/450908/80) for figuring out the pinouts for the discontinued RS232 Control DB15 cable (PN 05913665) with incorrect pinouts listed in the Xantech manual. The following are the correct pinouts:

| HDB15 Male | Function | DB9 Female | DB9 Color | Function | Notes |
|:----------:|:--------:|:----------:| --------- | -------- | ----- |
|     13      | Tx  |     2     | Brown     | Rx    | |
|     12      | Rx  |     3     | White     | Tx    | |
|     4      | DSR |       4     | Green     | DTR      | |
|     6      | DTR |      6     | Red       | DSR      | |
|     9      | GND |     5     | Yellow    | GND      | Ground (see also pin 11) |
|     11      | GND |     5     | Yellow    | GND      | Ground (OPTIONAL) |

Example parts needed to build a custom Xantech MX88 style cable:

* [USB to DB9 RS232 Cable](https://amzn.com/dp/B0753HBT12?tag=carreramfi-20&tracking_id=carreramfi-20) or [IP/Ethernet to DB9 Adapter](https://amzn.com/dp/B0B8T95FV1?tag=carreramfi-20&tracking_id=carreramfi-20) or [Virtual IP2SL](https://github.com/rsnodgrass/virtual-ip2sl)

* [DB9 Female Connector with wires](https://amzn.com/dp/B0BG2BPVXV?tag=carreramfi-20&tracking_id=carreramfi-20) or [DB9 Female Connector](https://amzn.com/dp/B09L7K511Y?tag=carreramfi-20&tracking_id=carreramfi-20)

* [Xantech Male DB15 Connector](https://amzn.com/dp/B07P6R8DRJ?tag=carreramfi-20&tracking_id=carreramfi-20)
