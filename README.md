# EV Load balancing

A Home Assistant custom integration that brings functionality to dynamically limit allowed EV charger current on individual phases based on your settings and the load on your mains power line.

>**Work in progress!** It's still in beta phase but should maybe work, have a try if you want!
>Started by creating an [automation blueprint](https://github.com/dala318/easee_load_balancing) that sort of works but soon realized that for doing anything more advanced the lambda programming get too cumbersome so opted to do it as a custom integration.

## Scope

For a first version it will only support the combination [Slimmelezer](https://www.zuidwijk.com/product/slimmelezer/) as mains current sensor and [Easee](https://github.com/nordicopen/easee_hass) charging robot.

For instructions how you could add a new device type or integration support, see the [developer guide](DEVELOPER_GUIDE.md)

## Install & Setup

### Install integration

1. Go to HACS -> Integrations
2. Click the three dots on the top right and select `Custom Repositories`
3. Enter `https://github.com/dala318/ev_load_balancing` as repository, select the category `Integration` and click Add
4. A new custom integration shows up for installation (EV load Balancing) - install it
5. Restart Home Assistant

### Pre-conditions

* You need a [Slimmelezer](https://www.zuidwijk.com/product/slimmelezer/) installed and configured as a ESPHome device
* You need an [Easee](https://github.com/nordicopen/easee_hass) charger robot installed
  * By default some sensors are disabled on your charger, make sure to activate the `dynamic_circuit_limit` and `status` sensors and wait until you see them with values.
* Alternatively there is some support to interact with any source or target via "templates". This is very untested and likely requires some insight into the code to get working for now.

### Configure integration

1. From your settings add new integration EV Load Balancing.
2. Select what type of device for Mains current monitor and EV Changer (for now only Slimmelezer and Easee possible).
    * Here you can also select to enable `developer_mode`, it basically disables some checks to make development easier.
3. Select the specific device for each type (for Easee select the one with the device-id, not the one name "Easee EV Charger").
    * Set the rated max current on your mains circuit (or slightly below if you want some margin).
    * Set the time-to-live for charger setting (this will cause the charger to reset to default limit if no new setting has been received for x minutes).
4. Pair the phases, this is needed since what the Mains and Charger device has as phase1 etc. may not be the same, "crossed wires" (by default it pairs 1-to-1 etc. but match as you want). Oder has no function, just make sure to not have any duplicates (ex. two mains phase 1, it will throw and error and you have to select them again).
5. Submit.
    * Directly after submit or restart of Home Assistant the integration may show an error, this is likely due to the delay in Easee sensor reporting, give it some seconds and it should work.
7. Start charging your vehicle and monitor the mains consumption and limits of your charger (attributes of the `dynamic_circuit_limit` sensor) if it works for you!

## Feedback

If you find an error of have some proposal for improvment, please look through the [Issues](https://github.com/dala318/ev_load_balancing/issues) and create a new if not reported before, or start a thread in the [Discussions page](https://github.com/dala318/ev_load_balancing/discussions).
