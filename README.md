# EV Load balancing

A Home Assistant custom integration that brings functionality to dynamically limit allowed EV charger current on individual phases based on your settings and the load on your mains power line.

>**Work in progress!** It's still in beta phase but should maybe work, have a try if you want!
>Started by creating an [automation blueprint](https://github.com/dala318/easee_load_balancing) that sort of works but soon realized that for doing anything more advanced the lambda programming get too cumbersome so opted to do it as a custom integration.

## Scope

For a first version it will only support the combination [Slimmelezer](https://www.zuidwijk.com/product/slimmelezer/) as mains current sensor and [Easee](https://github.com/nordicopen/easee_hass) charging robot.

Will soon add a description how it could be extended to work with other devices integrations in Home Assistant as well.
